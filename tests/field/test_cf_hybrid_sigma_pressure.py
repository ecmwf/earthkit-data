#!/usr/bin/env python3

# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np
import pytest

import earthkit.data.field.cf  # noqa: F401
from earthkit.data import from_source
from earthkit.data.field.cf import (
    AtmosphereHybridSigmaPressureCoordinate,
    ParametricVerticalCoordinate,
    get_parametric_vertical_class,
)
from earthkit.data.field.component.level_parameters import HybridLevelParameters
from earthkit.data.field.component.vertical import ParametricVertical, create_vertical
from earthkit.data.utils.testing import earthkit_test_data_file

HYBRID = "atmosphere_hybrid_sigma_pressure_coordinate"
CLS = AtmosphereHybridSigmaPressureCoordinate

# synthetic 3 level model (4 half levels)
A3 = np.array([0.0, 2000.0, 1000.0, 0.0])
B3 = np.array([0.0, 0.0, 0.5, 1.0])


@pytest.fixture(scope="module")
def ml_fieldlist():
    return from_source("file", earthkit_test_data_file("ml_data.grib")).to_fieldlist()


@pytest.fixture(scope="module")
def l137(ml_fieldlist):
    A, B = ml_fieldlist[0].vertical.coefficients()
    return np.asarray(A), np.asarray(B)


def _vertical(level, A=A3, B=B3):
    return create_vertical({"level": level, "level_type": "hybrid", "coefficients": (A, B)})


# ---------------------------------------------------------------------------
# registration and constructor
# ---------------------------------------------------------------------------


def test_cf_hybrid_registered():
    assert get_parametric_vertical_class(HYBRID) is CLS
    assert issubclass(CLS, ParametricVerticalCoordinate)
    assert CLS.STANDARD_NAME == HYBRID
    assert CLS.COMPUTED_STANDARD_NAME == "air_pressure"
    assert CLS.TERMS == ("a", "b", "ps", "p0", "ap")


def test_cf_hybrid_constructor():
    ap = [1.0, 2.0, 3.0]
    b = [0.1, 0.2, 0.3]
    c = CLS(ap, b, levels=[3, 1, 2], p0=1000.0, ps_name="sp")
    assert len(c) == 3
    assert c.number_of_levels == 3
    assert c.ap.dtype == np.float64
    assert c.b.dtype == np.float64
    assert c.levels.dtype.kind == "i"
    np.testing.assert_array_equal(c.ap, ap)
    np.testing.assert_array_equal(c.b, b)
    np.testing.assert_array_equal(c.levels, [3, 1, 2])
    assert c.ap_bnds is None
    assert c.b_bnds is None
    assert c.p0 == 1000.0
    assert c.ps_name == "sp"

    c = CLS(ap, b)
    assert c.levels is None
    assert c.p0 == 100000.0
    assert c.ps_name == "ps"

    # inputs are copied and the stored arrays are read-only
    ap_in = np.array(ap)
    c = CLS(ap_in, b)
    ap_in[0] = 99.0
    assert c.ap[0] == 1.0
    with pytest.raises(ValueError):
        c.ap[0] = 5.0

    with pytest.raises(AttributeError):
        c.ap = [1.0, 2.0, 3.0]


@pytest.mark.parametrize(
    "kwargs,match",
    [
        ({"ap": [[1.0, 2.0]], "b": [[0.1, 0.2]]}, "1D"),
        ({"ap": [1.0, 2.0], "b": [0.1]}, "shape"),
        ({"ap": [], "b": []}, "At least one"),
        ({"ap": [1.0, 2.0], "b": [0.1, 0.2], "ap_bnds": [[0.0, 1.0], [1.0, 2.0]]}, "together"),
        ({"ap": [1.0, 2.0], "b": [0.1, 0.2], "b_bnds": [[0.0, 1.0], [1.0, 2.0]]}, "together"),
        (
            {"ap": [1.0, 2.0], "b": [0.1, 0.2], "ap_bnds": [0.0, 1.0], "b_bnds": [0.0, 1.0]},
            "2D",
        ),
        (
            {"ap": [1.0, 2.0], "b": [0.1, 0.2], "ap_bnds": [[0.0, 1.0]] * 3, "b_bnds": [[0.0, 1.0]] * 3},
            "shape",
        ),
        ({"ap": [1.0, 2.0], "b": [0.1, 0.2], "levels": [1, 2, 3]}, "shape"),
        ({"ap": [1.0, 2.0], "b": [0.1, 0.2], "levels": [1, 1]}, "duplicates"),
        ({"ap": [1.0, 2.0], "b": [0.1, 0.2], "levels": [1.5, 2.0]}, "integers"),
        ({"ap": [1.0, 2.0], "b": [0.1, 0.2], "levels": [[1, 2]]}, "1D"),
        ({"ap": ["a", "b"], "b": [0.1, 0.2]}, "numeric"),
    ],
)
def test_cf_hybrid_constructor_errors(kwargs, match):
    with pytest.raises(ValueError, match=match):
        CLS(**kwargs)


# ---------------------------------------------------------------------------
# from_half_levels
# ---------------------------------------------------------------------------


def test_cf_hybrid_from_half_levels():
    c = CLS.from_half_levels(A3, B3)
    assert len(c) == 3
    np.testing.assert_array_equal(c.levels, [1, 2, 3])
    np.testing.assert_allclose(c.ap, [1000.0, 1500.0, 500.0])
    np.testing.assert_allclose(c.b, [0.0, 0.25, 0.75])
    np.testing.assert_array_equal(c.ap_bnds, [[0.0, 2000.0], [2000.0, 1000.0], [1000.0, 0.0]])
    np.testing.assert_array_equal(c.b_bnds, [[0.0, 0.0], [0.0, 0.5], [0.5, 1.0]])
    assert c.p0 == 100000.0


def test_cf_hybrid_from_half_levels_kwargs():
    c = CLS.from_half_levels(A3, B3, p0=1.0e5, ps_name="sp")
    assert c.p0 == 1.0e5
    assert c.ps_name == "sp"


def test_cf_hybrid_from_half_levels_subset():
    c = CLS.from_half_levels(A3, B3, levels=[3, 1])
    np.testing.assert_array_equal(c.levels, [3, 1])
    np.testing.assert_allclose(c.ap, [500.0, 1000.0])
    np.testing.assert_allclose(c.b, [0.75, 0.0])
    np.testing.assert_array_equal(c.ap_bnds, [[1000.0, 0.0], [0.0, 2000.0]])
    np.testing.assert_array_equal(c.b_bnds, [[0.5, 1.0], [0.0, 0.0]])


@pytest.mark.parametrize("levels", [[0, 1], [1, 4], [1, 1], [-1], [], [1.5]])
def test_cf_hybrid_from_half_levels_bad_levels(levels):
    with pytest.raises(ValueError):
        CLS.from_half_levels(A3, B3, levels=levels)


def test_cf_hybrid_from_half_levels_bad_coeffs():
    with pytest.raises(ValueError):
        CLS.from_half_levels(A3, B3[:-1])
    with pytest.raises(ValueError):
        CLS.from_half_levels([0.0], [0.0])
    with pytest.raises(ValueError):
        CLS.from_half_levels([[0.0, 1.0]], [[0.0, 1.0]])


# ---------------------------------------------------------------------------
# from_level_parameters
# ---------------------------------------------------------------------------


def test_cf_hybrid_from_level_parameters():
    c = CLS.from_level_parameters(HybridLevelParameters(A3, B3))
    ref = CLS.from_half_levels(A3, B3)
    np.testing.assert_array_equal(c.ap, ref.ap)
    np.testing.assert_array_equal(c.b, ref.b)
    np.testing.assert_array_equal(c.levels, ref.levels)

    c = CLS.from_level_parameters(HybridLevelParameters(A3, B3), levels=[2])
    np.testing.assert_array_equal(c.levels, [2])
    np.testing.assert_allclose(c.ap, [1500.0])


def test_cf_hybrid_from_level_parameters_not_hybrid():
    with pytest.raises(ValueError, match="not hybrid"):
        CLS.from_level_parameters(object())

    with pytest.raises(ValueError, match="not hybrid"):
        CLS.from_level_parameters((A3, B3))


def test_cf_hybrid_l137_roundtrip(ml_fieldlist, l137):
    A, B = l137
    assert len(A) == 138

    params = ml_fieldlist[0].vertical._coefficients
    c = CLS.from_level_parameters(params)
    assert len(c) == 137
    np.testing.assert_array_equal(c.levels, np.arange(1, 138))
    assert c.can_rebuild_half_levels()

    p = c.to_level_parameters()
    assert isinstance(p, HybridLevelParameters)
    assert p.number_of_levels() == 137
    A1, B1 = p.coefficients()
    np.testing.assert_array_equal(A1, A)
    np.testing.assert_array_equal(B1, B)

    # level 137 is bounded by the last two half levels and the surface has b=1
    np.testing.assert_array_equal(c.b_bnds[-1], B[-2:])
    assert c.b_bnds[-1, 1] == 1.0


# ---------------------------------------------------------------------------
# from_verticals
# ---------------------------------------------------------------------------


def test_cf_hybrid_from_verticals_grib(ml_fieldlist, l137):
    A, B = l137
    verticals = [f.vertical for f in ml_fieldlist]
    c = CLS.from_verticals(verticals)

    expected_levels = list(dict.fromkeys(f.vertical.level() for f in ml_fieldlist))
    assert len(expected_levels) > 1
    np.testing.assert_array_equal(c.levels, expected_levels)

    ref = CLS.from_half_levels(A, B, levels=expected_levels)
    np.testing.assert_array_equal(c.ap, ref.ap)
    np.testing.assert_array_equal(c.b, ref.b)
    np.testing.assert_array_equal(c.ap_bnds, ref.ap_bnds)
    np.testing.assert_array_equal(c.b_bnds, ref.b_bnds)

    # not all the levels are available
    assert not c.can_rebuild_half_levels()


def test_cf_hybrid_from_verticals_synthetic():
    verticals = [_vertical(3), _vertical(1), _vertical(3), _vertical(2)]
    c = CLS.from_verticals(verticals)
    ref = CLS.from_half_levels(A3, B3, levels=[3, 1, 2])
    np.testing.assert_array_equal(c.levels, [3, 1, 2])
    np.testing.assert_array_equal(c.ap, ref.ap)
    np.testing.assert_array_equal(c.b, ref.b)
    np.testing.assert_array_equal(c.ap_bnds, ref.ap_bnds)
    np.testing.assert_array_equal(c.b_bnds, ref.b_bnds)

    # iterators are accepted
    c = CLS.from_verticals(iter([_vertical(1), _vertical(2)]))
    np.testing.assert_array_equal(c.levels, [1, 2])


def test_cf_hybrid_from_verticals_single():
    c = CLS.from_verticals(_vertical(2), p0=1.0e5)
    np.testing.assert_array_equal(c.levels, [2])
    np.testing.assert_allclose(c.ap, [1500.0])


def test_cf_hybrid_from_verticals_errors():
    # plain hybrid vertical without coefficients
    plain = create_vertical({"level": 1, "level_type": "hybrid"})
    assert not isinstance(plain, ParametricVertical)
    with pytest.raises(ValueError, match="no hybrid coefficients"):
        CLS.from_verticals([plain])
    with pytest.raises(ValueError, match="no hybrid coefficients"):
        CLS.from_verticals(plain)

    # not hybrid
    pl = create_vertical({"level": 500, "level_type": "pressure"})
    with pytest.raises(ValueError, match="not hybrid"):
        CLS.from_verticals([pl])
    with pytest.raises(ValueError, match="not hybrid"):
        CLS.from_verticals([_vertical(1), pl])

    # mismatched coefficients
    with pytest.raises(ValueError, match="different"):
        CLS.from_verticals([_vertical(1), _vertical(2, A=A3 + 1.0)])
    with pytest.raises(ValueError, match="different"):
        CLS.from_verticals([_vertical(1), _vertical(2, B=B3 * 0.5)])

    # empty
    with pytest.raises(ValueError, match="No verticals"):
        CLS.from_verticals([])

    with pytest.raises(ValueError):
        CLS.from_verticals(1)

    # level out of range
    with pytest.raises(ValueError, match="levels"):
        CLS.from_verticals([_vertical(4)])


# ---------------------------------------------------------------------------
# to_level_parameters, to_vertical
# ---------------------------------------------------------------------------


def test_cf_hybrid_to_level_parameters():
    c = CLS.from_half_levels(A3, B3)
    assert c.can_rebuild_half_levels()
    A, B = c.to_level_parameters().coefficients()
    np.testing.assert_array_equal(A, A3)
    np.testing.assert_array_equal(B, B3)


def test_cf_hybrid_to_level_parameters_unsorted_levels():
    c = CLS.from_half_levels(A3, B3, levels=[2, 3, 1])
    assert c.can_rebuild_half_levels()
    A, B = c.to_level_parameters().coefficients()
    np.testing.assert_array_equal(A, A3)
    np.testing.assert_array_equal(B, B3)


def test_cf_hybrid_levels_none_contiguous_chain():
    ap_bnds = np.stack([A3[:-1], A3[1:]], axis=1)
    b_bnds = np.stack([B3[:-1], B3[1:]], axis=1)
    c = CLS(ap_bnds.mean(axis=1), b_bnds.mean(axis=1), ap_bnds=ap_bnds, b_bnds=b_bnds)
    assert c.levels is None
    assert c.can_rebuild_half_levels()
    A, B = c.to_level_parameters().coefficients()
    np.testing.assert_array_equal(A, A3)
    np.testing.assert_array_equal(B, B3)

    v = c.to_vertical(2)
    assert v.level() == 2
    np.testing.assert_array_equal(v.coefficients()[0], A3)

    with pytest.raises(ValueError, match="not one of the levels"):
        c.to_vertical(4)


def test_cf_hybrid_levels_none_not_contiguous():
    ap_bnds = np.array([[0.0, 2000.0], [1000.0, 500.0]])
    b_bnds = np.array([[0.0, 0.0], [0.0, 1.0]])
    c = CLS([1000.0, 750.0], [0.0, 0.5], ap_bnds=ap_bnds, b_bnds=b_bnds)
    assert not c.can_rebuild_half_levels()
    with pytest.raises(ValueError, match="not contiguous"):
        c.to_level_parameters()

    # contiguous in ap but not in b
    ap_bnds = np.array([[0.0, 2000.0], [2000.0, 500.0]])
    c = CLS([1000.0, 750.0], [0.0, 0.5], ap_bnds=ap_bnds, b_bnds=b_bnds + [[0.0, 0.1], [0.0, 0.0]])
    with pytest.raises(ValueError, match="b bounds are not contiguous"):
        c.to_level_parameters()


def test_cf_hybrid_cannot_rebuild_without_bounds():
    c = CLS([1000.0, 1500.0], [0.0, 0.25], levels=[1, 2])
    assert not c.can_rebuild_half_levels()
    with pytest.raises(ValueError, match="no bounds"):
        c.to_level_parameters()
    with pytest.raises(ValueError, match="no bounds"):
        c.to_vertical(1)


def test_cf_hybrid_to_vertical():
    c = CLS.from_half_levels(A3, B3)
    for k in (1, 2, 3):
        v = c.to_vertical(k)
        assert isinstance(v, ParametricVertical)
        assert v.level() == k
        assert v.level_type() == "hybrid"
        assert v.number_of_levels() == 3
        A, B = v.coefficients()
        np.testing.assert_array_equal(A, A3)
        np.testing.assert_array_equal(B, B3)

    for bad in (0, 4, 1.5, "a", None):
        with pytest.raises(ValueError, match="not one of the levels"):
            c.to_vertical(bad)


def test_cf_hybrid_to_vertical_l137(ml_fieldlist, l137):
    A, B = l137
    c = CLS.from_level_parameters(ml_fieldlist[0].vertical._coefficients)
    v = c.to_vertical(137)
    assert v.level() == 137
    np.testing.assert_array_equal(v.coefficients()[0], A)
    np.testing.assert_array_equal(v.coefficients()[1], B)


def test_cf_hybrid_vertical_roundtrip():
    c = CLS.from_verticals([_vertical(k) for k in (1, 2, 3)])
    v = c.to_vertical(2)
    c2 = CLS.from_verticals(v)
    np.testing.assert_array_equal(c2.levels, [2])
    np.testing.assert_array_equal(c2.ap, c.ap[1:2])


def test_cf_hybrid_subset_cannot_rebuild(l137):
    A, B = l137
    c = CLS.from_half_levels(A, B, levels=[1, 50, 137])
    assert len(c) == 3
    assert not c.can_rebuild_half_levels()
    with pytest.raises(ValueError, match="levels must be exactly"):
        c.to_level_parameters()
    with pytest.raises(ValueError):
        c.to_vertical(50)

    p = c.pressure(101325.0)
    assert p.shape == (3,)
    assert np.all(np.diff(p) > 0)


# ---------------------------------------------------------------------------
# dimensionless values
# ---------------------------------------------------------------------------


def test_cf_hybrid_dimensionless():
    c = CLS.from_half_levels(A3, B3)
    np.testing.assert_allclose(c.dimensionless_values(), c.ap / 1.0e5 + c.b)
    np.testing.assert_allclose(c.dimensionless_values(p0=1000.0), c.ap / 1000.0 + c.b)
    np.testing.assert_allclose(c.dimensionless_bounds(), c.ap_bnds / 1.0e5 + c.b_bnds)
    assert c.dimensionless_bounds(p0=2.0e5).shape == (3, 2)

    c = CLS.from_half_levels(A3, B3, p0=1000.0)
    np.testing.assert_allclose(c.dimensionless_values(), c.ap / 1000.0 + c.b)
    np.testing.assert_allclose(c.dimensionless_values(p0=1.0e5), c.ap / 1.0e5 + c.b)


@pytest.mark.parametrize("p0", [0.0, -1.0, float("nan")])
def test_cf_hybrid_dimensionless_bad_p0(p0):
    c = CLS.from_half_levels(A3, B3)
    with pytest.raises(ValueError, match="positive"):
        c.dimensionless_values(p0=p0)
    with pytest.raises(ValueError, match="positive"):
        c.dimensionless_bounds(p0=p0)

    # invalid p0 of the object, no explicit value
    c = CLS.from_half_levels(A3, B3, p0=0.0)
    with pytest.raises(ValueError, match="explicit positive"):
        c.dimensionless_values()
    np.testing.assert_allclose(c.dimensionless_values(p0=1.0e5), c.ap / 1.0e5 + c.b)


def test_cf_hybrid_dimensionless_bounds_no_bounds():
    c = CLS([1000.0], [0.5])
    assert c.dimensionless_values().shape == (1,)
    with pytest.raises(ValueError, match="No bounds"):
        c.dimensionless_bounds()


# ---------------------------------------------------------------------------
# pressure
# ---------------------------------------------------------------------------


def test_cf_hybrid_pressure_scalar():
    c = CLS.from_half_levels(A3, B3)
    p = c.pressure(100000.0)
    assert p.shape == (3,)
    np.testing.assert_allclose(p, [1000.0, 1500.0 + 25000.0, 500.0 + 75000.0])


def test_cf_hybrid_pressure_array():
    c = CLS.from_half_levels(A3, B3)
    ps = np.array([[90000.0, 100000.0, 110000.0], [95000.0, 101325.0, 105000.0]])
    p = c.pressure(ps)
    assert p.shape == (3, 2, 3)
    for k in range(3):
        np.testing.assert_allclose(p[k], c.ap[k] + c.b[k] * ps)

    assert c.pressure([1.0e5, 1.0e5]).shape == (3, 2)


def test_cf_hybrid_half_level_pressure():
    c = CLS.from_half_levels(A3, B3)
    p = c.half_level_pressure(100000.0)
    assert p.shape == (3, 2)
    np.testing.assert_allclose(p[:, 0], A3[:-1] + B3[:-1] * 1.0e5)
    np.testing.assert_allclose(p[:, 1], A3[1:] + B3[1:] * 1.0e5)
    # full level pressure is the mean of the half level values
    np.testing.assert_allclose(c.pressure(1.0e5), p.mean(axis=1))

    ps = np.full((4, 5), 1.0e5)
    assert c.half_level_pressure(ps).shape == (3, 2, 4, 5)

    with pytest.raises(ValueError, match="No bounds"):
        CLS([1.0], [0.5]).half_level_pressure(1.0e5)


def test_cf_hybrid_pressure_l137(l137):
    A, B = l137
    c = CLS.from_half_levels(A, B)
    ps = 101325.0
    p = c.pressure(ps)
    assert p.shape == (137,)
    assert p[-1] < ps
    assert p[-1] == pytest.approx(ps, rel=1e-2)
    assert np.all(np.diff(p) > 0)

    ph = c.half_level_pressure(ps)
    assert ph[0, 0] == 0.0
    assert ph[-1, 1] == pytest.approx(ps)
    assert np.all(np.diff(ph[:, 1]) > 0)
