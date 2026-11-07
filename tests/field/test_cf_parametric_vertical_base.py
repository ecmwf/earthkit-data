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
import xarray as xr

from earthkit.data.field.cf import (
    CF_PARAMETRIC_VERTICAL_TERMS,
    ParametricVerticalCoordinate,
    decode_parametric_vertical,
    format_formula_terms,
    get_cf_attribute,
    get_parametric_vertical_class,
    parse_formula_terms,
    register_parametric_vertical,
)
from earthkit.data.field.cf.parametric_vertical import _REGISTRY

SIGMA = "atmosphere_sigma_coordinate"
HEIGHT = "atmosphere_hybrid_height_coordinate"
HYBRID = "atmosphere_hybrid_sigma_pressure_coordinate"


@pytest.fixture
def registry():
    """Restore the registry after the test so that test classes cannot leak."""
    saved = dict(_REGISTRY)
    yield _REGISTRY
    _REGISTRY.clear()
    _REGISTRY.update(saved)


def _make_dummy(standard_name=SIGMA):
    class Dummy(ParametricVerticalCoordinate):
        STANDARD_NAME = standard_name
        COMPUTED_STANDARD_NAME = "air_pressure"
        TERMS = CF_PARAMETRIC_VERTICAL_TERMS.get(standard_name, ())

        def __init__(self, ds=None, coord_name=None):
            self.ds = ds
            self.coord_name = coord_name

        def encode(self, **kwargs):
            return xr.Dataset()

        @classmethod
        def from_xarray(cls, ds, coord_name):
            return cls(ds, coord_name)

    return Dummy


def _sigma_dataset(with_bounds=True, name="lev"):
    ds = xr.Dataset(
        coords={name: (name, np.array([0.1, 0.5, 0.9]))},
        data_vars={
            "ps": (("x",), np.array([1e5, 1e5])),
            "ptop": ((), 100.0),
            "t": ((name, "x"), np.zeros((3, 2))),
        },
    )
    ds[name].attrs = {
        "standard_name": SIGMA,
        "formula_terms": "sigma: lev ps: ps ptop: ptop",
    }
    if with_bounds:
        ds[name].attrs["bounds"] = f"{name}_bnds"
        ds[f"{name}_bnds"] = ((name, "nv"), np.zeros((3, 2)))
        ds[f"{name}_bnds"].attrs = {"formula_terms": f"sigma: {name}_bnds ps: ps ptop: ptop"}
    return ds


# ---------------------------------------------------------------------------
# formula_terms
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "s,expected",
    [
        ("a: v1 b: v2 ps: v3 p0: v4", {"a": "v1", "b": "v2", "ps": "v3", "p0": "v4"}),
        ("a:v1  b :v2", {"a": "v1", "b": "v2"}),
        ("A : v1", {"a": "v1"}),
        ("  AP: ap B: b Ps: PS  ", {"ap": "ap", "b": "b", "ps": "PS"}),
        ("a: hyam b: hybm p0: P0 ps: PS", {"a": "hyam", "b": "hybm", "p0": "P0", "ps": "PS"}),
        ("a:\tv1\nb: v2", {"a": "v1", "b": "v2"}),
    ],
)
def test_parse_formula_terms(s, expected):
    r = parse_formula_terms(s)
    assert r == expected
    assert list(r) == list(expected)


@pytest.mark.parametrize(
    "s",
    [
        "",
        "   ",
        "a:",
        "a: v1 b:",
        "a: b: v2",
        "v1",
        "a: v1 v2",
        ":v1",
        "a: v1 : v2",
        "a: v1:v2",
    ],
)
def test_parse_formula_terms_malformed(s):
    with pytest.raises(ValueError):
        parse_formula_terms(s)


@pytest.mark.parametrize("s", ["a: v1 a: v2", "a: v1 A: v2", "ps:x b:y PS:z"])
def test_parse_formula_terms_duplicate(s):
    with pytest.raises(ValueError, match="duplicate"):
        parse_formula_terms(s)


def test_parse_formula_terms_not_str():
    with pytest.raises(ValueError):
        parse_formula_terms(None)


def test_format_formula_terms():
    assert format_formula_terms({"ap": "ap", "b": "b", "ps": "ps"}) == "ap: ap b: b ps: ps"
    assert format_formula_terms({"b": "b", "ap": "ap"}) == "b: b ap: ap"


def test_format_formula_terms_order():
    t = {"ps": "PS", "b": "B", "ap": "A"}
    assert format_formula_terms(t, order=("ap", "b", "ps")) == "ap: A b: B ps: PS"
    # terms missing from order are appended, unknown names in order are ignored
    assert format_formula_terms(t, order=("b", "p0")) == "b: B ps: PS ap: A"


@pytest.mark.parametrize(
    "t",
    [
        {"ap": "ap", "b": "b", "ps": "ps"},
        {"a": "hyam", "b": "hybm", "p0": "P0", "ps": "PS"},
        {"ps": "x"},
    ],
)
def test_formula_terms_roundtrip(t):
    assert parse_formula_terms(format_formula_terms(t)) == t


def test_cf_parametric_vertical_terms():
    assert len(CF_PARAMETRIC_VERTICAL_TERMS) == 11
    assert set(CF_PARAMETRIC_VERTICAL_TERMS) == {
        "atmosphere_ln_pressure_coordinate",
        "atmosphere_sigma_coordinate",
        "atmosphere_hybrid_sigma_pressure_coordinate",
        "atmosphere_hybrid_height_coordinate",
        "atmosphere_sleve_coordinate",
        "ocean_sigma_coordinate",
        "ocean_s_coordinate",
        "ocean_s_coordinate_g1",
        "ocean_s_coordinate_g2",
        "ocean_sigma_z_coordinate",
        "ocean_double_sigma_coordinate",
    }
    assert CF_PARAMETRIC_VERTICAL_TERMS[HYBRID] == ("a", "b", "ps", "p0", "ap")
    assert "nsigma" in CF_PARAMETRIC_VERTICAL_TERMS["ocean_sigma_z_coordinate"]
    for name, terms in CF_PARAMETRIC_VERTICAL_TERMS.items():
        assert isinstance(terms, tuple)
        assert all(t == t.lower() for t in terms), name


# ---------------------------------------------------------------------------
# base class and registry
# ---------------------------------------------------------------------------


def test_base_class_is_abstract():
    with pytest.raises(TypeError):
        ParametricVerticalCoordinate()

    class Incomplete(ParametricVerticalCoordinate):
        def encode(self, **kwargs):
            pass

    with pytest.raises(TypeError):
        Incomplete()


def test_register_and_get(registry):
    Dummy = _make_dummy()
    assert register_parametric_vertical(Dummy) is Dummy
    assert get_parametric_vertical_class(SIGMA) is Dummy
    # registering the same class again is fine
    register_parametric_vertical(Dummy)
    assert get_parametric_vertical_class(SIGMA) is Dummy


def test_register_decorator(registry):
    @register_parametric_vertical
    class Dummy(_make_dummy()):
        pass

    assert get_parametric_vertical_class(SIGMA) is Dummy


def test_register_missing_standard_name(registry):
    class NoName(_make_dummy()):
        STANDARD_NAME = None

    with pytest.raises(ValueError, match="STANDARD_NAME"):
        register_parametric_vertical(NoName)


def test_register_duplicate(registry):
    register_parametric_vertical(_make_dummy())
    with pytest.raises(ValueError, match="already registered"):
        register_parametric_vertical(_make_dummy())


def test_get_class_unsupported_vs_unknown(registry):
    # known CF parametric coordinate, but nothing registered
    _REGISTRY.pop(HEIGHT, None)
    with pytest.raises(ValueError, match="not yet supported"):
        get_parametric_vertical_class(HEIGHT)

    with pytest.raises(ValueError, match="not a CF parametric vertical coordinate"):
        get_parametric_vertical_class("air_temperature")


def test_registry_does_not_leak():
    # the registry fixture must have removed the test classes
    assert SIGMA not in _REGISTRY


# ---------------------------------------------------------------------------
# decode_parametric_vertical
# ---------------------------------------------------------------------------


def test_decode_with_coord_name(registry):
    Dummy = register_parametric_vertical(_make_dummy())
    ds = _sigma_dataset()
    r = decode_parametric_vertical(ds, "lev")
    assert isinstance(r, Dummy)
    assert r.ds is ds
    assert r.coord_name == "lev"


def test_decode_auto_with_bounds(registry):
    Dummy = register_parametric_vertical(_make_dummy())
    ds = _sigma_dataset(with_bounds=True)
    # lev and lev_bnds both carry formula_terms, but lev_bnds is a bounds variable
    r = decode_parametric_vertical(ds)
    assert isinstance(r, Dummy)
    assert r.coord_name == "lev"


def _move_to_encoding(ds):
    """Mimic ``decode_coords="all"``: formula_terms and bounds move from attrs to encoding."""
    for name in ds.variables:
        for key in ("formula_terms", "bounds"):
            if key in ds[name].attrs:
                ds[name].encoding[key] = ds[name].attrs.pop(key)
    return ds


def test_decode_auto_with_bounds_in_encoding(registry):
    Dummy = register_parametric_vertical(_make_dummy())
    ds = _move_to_encoding(_sigma_dataset(with_bounds=True))
    assert "formula_terms" not in ds["lev"].attrs
    assert "bounds" not in ds["lev"].attrs
    assert ds["lev_bnds"].encoding["formula_terms"]

    # lev and lev_bnds both carry formula_terms (in encoding), lev_bnds is a bounds variable of lev
    r = decode_parametric_vertical(ds)
    assert isinstance(r, Dummy)
    assert r.coord_name == "lev"


def test_decode_auto_formula_terms_in_encoding_only(registry):
    register_parametric_vertical(_make_dummy())
    ds = _move_to_encoding(_sigma_dataset(with_bounds=False))
    assert decode_parametric_vertical(ds).coord_name == "lev"

    # a variable with formula_terms only in encoding is a candidate, a standard_name is still needed
    ds = xr.Dataset({"x": (("z",), np.zeros(2))})
    ds["x"].encoding["formula_terms"] = "sigma: x"
    with pytest.raises(ValueError, match="no standard_name"):
        decode_parametric_vertical(ds)


def test_get_cf_attribute():
    da = xr.DataArray(np.zeros(2), attrs={"a": 1, "c": 3}, name="v")
    da.encoding.update({"a": 10, "b": 2})
    assert get_cf_attribute(da, "a") == 1
    assert get_cf_attribute(da, "b") == 2
    assert get_cf_attribute(da, "c") == 3
    assert get_cf_attribute(da, "d") is None
    assert get_cf_attribute(da, "d", "x") == "x"
    assert get_cf_attribute(da.variable, "b") == 2


def test_decode_auto_without_bounds(registry):
    register_parametric_vertical(_make_dummy())
    r = decode_parametric_vertical(_sigma_dataset(with_bounds=False))
    assert r.coord_name == "lev"


def test_decode_auto_standard_name_only(registry):
    register_parametric_vertical(_make_dummy())
    ds = _sigma_dataset(with_bounds=False)
    del ds["lev"].attrs["formula_terms"]
    assert decode_parametric_vertical(ds).coord_name == "lev"


def test_decode_auto_data_variable(registry):
    register_parametric_vertical(_make_dummy())
    ds = xr.Dataset({"lev": (("z",), np.array([0.1, 0.5]))})
    ds["lev"].attrs = {"standard_name": SIGMA, "formula_terms": "sigma: lev"}
    assert "lev" not in ds.coords
    assert decode_parametric_vertical(ds).coord_name == "lev"


def test_decode_ambiguous(registry):
    register_parametric_vertical(_make_dummy())
    ds = xr.merge([_sigma_dataset(name="lev1"), _sigma_dataset(name="lev2")], compat="override")
    with pytest.raises(ValueError, match="ambiguous"):
        decode_parametric_vertical(ds)

    # picking one explicitly works
    assert decode_parametric_vertical(ds, "lev2").coord_name == "lev2"


def test_decode_none_found(registry):
    ds = xr.Dataset({"t": (("x",), np.zeros(2))})
    with pytest.raises(ValueError, match="No parametric vertical"):
        decode_parametric_vertical(ds)


def test_decode_coord_name_missing(registry):
    with pytest.raises(ValueError, match="not found"):
        decode_parametric_vertical(_sigma_dataset(), "foo")


def test_decode_coord_name_no_standard_name(registry):
    with pytest.raises(ValueError, match="no standard_name"):
        decode_parametric_vertical(_sigma_dataset(), "ps")


def test_decode_unsupported_and_unknown(registry):
    _REGISTRY.pop(SIGMA, None)
    ds = _sigma_dataset()
    with pytest.raises(ValueError, match="not yet supported"):
        decode_parametric_vertical(ds)

    ds["ps"].attrs["standard_name"] = "surface_air_pressure"
    with pytest.raises(ValueError, match="not a CF parametric vertical coordinate"):
        decode_parametric_vertical(ds, "ps")
