#!/usr/bin/env python3

# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

import numpy as np
import pytest
import xarray as xr

import earthkit.data.field.cf  # noqa: F401
from earthkit.data import from_source
from earthkit.data.field.cf import AtmosphereHybridSigmaPressureCoordinate, decode_parametric_vertical
from earthkit.data.utils.testing import earthkit_test_data_file

HYBRID = "atmosphere_hybrid_sigma_pressure_coordinate"
CLS = AtmosphereHybridSigmaPressureCoordinate


@pytest.fixture(scope="module")
def l137():
    ds = from_source("file", earthkit_test_data_file("ml_data.grib")).to_fieldlist()
    A, B = ds[0].vertical.coefficients()
    return np.asarray(A), np.asarray(B)


@pytest.fixture(scope="module")
def full_model(l137):
    return CLS.from_half_levels(*l137, ps_name="sp")


def _assert_same(a, b, bounds=True):
    np.testing.assert_array_equal(a.ap, b.ap)
    np.testing.assert_array_equal(a.b, b.b)
    if bounds:
        np.testing.assert_array_equal(a.ap_bnds, b.ap_bnds)
        np.testing.assert_array_equal(a.b_bnds, b.b_bnds)
    else:
        assert b.ap_bnds is None
        assert b.b_bnds is None
    if a.levels is None:
        assert b.levels is None
    else:
        np.testing.assert_array_equal(a.levels, b.levels)
    assert a.ps_name == b.ps_name
    assert a.p0 == b.p0
    ps = np.array([[101325.0, 90000.0], [80000.0, 100000.0]])
    np.testing.assert_allclose(a.pressure(ps), b.pressure(ps), rtol=1e-14)


# ---------------------------------------------------------------------------
# encoding
# ---------------------------------------------------------------------------


def test_cf_hybrid_encode_attrs_level_number(full_model):
    ds = full_model.encode()

    assert set(ds.variables) == {"level", "ap", "b", "ap_bnds", "b_bnds", "level_bnds", "p0"}
    assert ds["level"].dims == ("level",)
    assert ds["level"].dtype.kind == "i"
    np.testing.assert_array_equal(ds["level"].values, np.arange(1, 138))

    attrs = ds["level"].attrs
    assert attrs["standard_name"] == HYBRID
    assert attrs["long_name"] == "hybrid level"
    assert attrs["units"] == "1"
    assert attrs["positive"] == "down"
    assert attrs["axis"] == "Z"
    assert attrs["computed_standard_name"] == "air_pressure"
    assert attrs["formula_terms"] == "ap: ap b: b ps: sp p0: p0"
    assert attrs["bounds"] == "level_bnds"

    assert ds["p0"].dims == ()
    assert ds["p0"].values == 100000.0
    assert ds["p0"].attrs == {
        "units": "Pa",
        "standard_name": "reference_air_pressure_for_atmosphere_vertical_coordinate",
        "long_name": "vertical coordinate formula term: reference pressure",
    }

    assert ds["ap"].dims == ("level",)
    assert ds["ap"].attrs["units"] == "Pa"
    assert "ap" in ds["ap"].attrs["long_name"]
    assert ds["b"].dims == ("level",)
    assert ds["b"].attrs["units"] == "1"

    for v in ("ap_bnds", "b_bnds", "level_bnds"):
        assert ds[v].dims == ("level", "bnds")
        assert ds[v].shape == (137, 2)
    assert ds["ap_bnds"].attrs["units"] == "Pa"
    assert ds["b_bnds"].attrs["units"] == "1"
    assert ds["level_bnds"].attrs == {"formula_terms": "ap: ap_bnds b: b_bnds ps: sp p0: p0"}
    np.testing.assert_array_equal(ds["level_bnds"].values[:, 0], np.arange(1, 138) - 0.5)
    np.testing.assert_array_equal(ds["level_bnds"].values[:, 1], np.arange(1, 138) + 0.5)

    # ps is never written
    assert "sp" not in ds.variables


def test_cf_hybrid_encode_dimensionless(full_model):
    ds = full_model.encode(coord_values="dimensionless")

    assert set(ds.variables) == {"level", "ap", "b", "ap_bnds", "b_bnds", "level_bnds", "model_level_number", "p0"}
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b ps: sp p0: p0"
    np.testing.assert_array_equal(ds["level"].values, full_model.ap / full_model.p0 + full_model.b)
    np.testing.assert_array_equal(ds["level_bnds"].values, full_model.ap_bnds / full_model.p0 + full_model.b_bnds)
    assert ds["level"].attrs["units"] == "1"
    assert ds["level"].attrs["standard_name"] == HYBRID

    mln = ds["model_level_number"]
    assert mln.dims == ("level",)
    assert mln.attrs == {"standard_name": "model_level_number", "long_name": "model level number", "units": "1"}
    np.testing.assert_array_equal(mln.values, np.arange(1, 138))


def test_cf_hybrid_encode_names(full_model):
    ds = full_model.encode(
        level_dim="lev",
        coord_values="dimensionless",
        names={
            "ap": "hyai",
            "b": "hybi",
            "ap_bnds": "hyai_bnds",
            "b_bnds": "hybi_bnds",
            "ps": "PS",
            "p0": "P0",
            "level_bnds": "lev_b",
            "bnds": "nv",
            "level_number": "mln",
        },
    )
    assert set(ds.variables) == {"lev", "hyai", "hybi", "hyai_bnds", "hybi_bnds", "lev_b", "mln", "P0"}
    assert ds["lev"].attrs["formula_terms"] == "ap: hyai b: hybi ps: PS p0: P0"
    assert ds["lev"].attrs["bounds"] == "lev_b"
    assert ds["lev_b"].attrs["formula_terms"] == "ap: hyai_bnds b: hybi_bnds ps: PS p0: P0"
    assert ds["lev_b"].dims == ("lev", "nv")

    d = CLS.from_xarray(ds, "lev")
    assert d.ps_name == "PS"
    assert d.p0 == full_model.p0
    np.testing.assert_array_equal(d.ap, full_model.ap)
    np.testing.assert_array_equal(d.b, full_model.b)
    np.testing.assert_array_equal(d.ap_bnds, full_model.ap_bnds)
    np.testing.assert_array_equal(d.levels, full_model.levels)


def test_cf_hybrid_encode_default_ps_name():
    m = CLS([1.0, 2.0], [0.5, 0.6], levels=[1, 2])
    assert m.encode()["level"].attrs["formula_terms"] == "ap: ap b: b ps: ps p0: p0"
    assert m.encode(names={"ps": "lnsp"})["level"].attrs["formula_terms"] == "ap: ap b: b ps: lnsp p0: p0"


def test_cf_hybrid_encode_invalid():
    m = CLS([1000.0, 2000.0], [0.5, 0.6], levels=[1, 2])
    with pytest.raises(ValueError):
        m.encode(coord_values="invalid")
    with pytest.raises(ValueError):
        m.encode(names={"xx": "a"})
    with pytest.raises(ValueError):
        m.encode(names={"ap": "b"})
    with pytest.raises(ValueError):
        m.encode(names={"ap": ""})

    # unknown levels
    m = CLS([1000.0, 2000.0], [0.5, 0.6])
    with pytest.raises(ValueError):
        m.encode()
    ds = m.encode(coord_values="dimensionless")
    assert "model_level_number" not in ds.variables

    # not monotonic
    m = CLS([1000.0, 2000.0, 1000.0], [0.5, 0.6, 0.5], levels=[1, 2, 3])
    with pytest.raises(ValueError):
        m.encode(coord_values="dimensionless")
    m.encode(coord_values="level_number")

    # no valid p0
    m = CLS([1000.0, 2000.0], [0.5, 0.6], levels=[1, 2], p0=0.0)
    with pytest.raises(ValueError):
        m.encode(coord_values="dimensionless")


def test_cf_hybrid_encode_name_collisions():
    m = CLS([1000.0, 2000.0], [0.5, 0.6], ap_bnds=[[0, 1], [1, 2]], b_bnds=[[0, 1]] * 2, levels=[1, 2])

    # the ps name is only referred to but must not be the name of a written variable
    for name in ("ap", "b", "level", "ap_bnds", "b_bnds", "level_bnds", "bnds", "p0"):
        with pytest.raises(ValueError):
            m.encode(names={"ps": name})

    # the same for the p0 name
    for name in ("ap", "b", "level", "ap_bnds", "b_bnds", "level_bnds", "bnds", "ps"):
        with pytest.raises(ValueError):
            m.encode(names={"p0": name})

    with pytest.raises(ValueError):
        m.encode(coord_values="dimensionless", names={"p0": "model_level_number"})

    # ps does not collide with the model level number when it is not written
    m.encode(names={"ps": "model_level_number"})

    # p0 is not written when it is not valid, so its name is free
    m0 = CLS([1000.0, 2000.0], [0.5, 0.6], levels=[1, 2], p0=0.0)
    ds = m0.encode(names={"p0": "ap"})
    assert "p0" not in ds["level"].attrs["formula_terms"]


def test_cf_hybrid_encode_no_bounds_model():
    m = CLS([1000.0, 2000.0], [0.1, 0.2], levels=[1, 2])
    for mode in ("level_number", "dimensionless"):
        ds = m.encode(coord_values=mode)
        assert "bounds" not in ds["level"].attrs
        assert set(ds.variables) <= {"level", "ap", "b", "model_level_number", "p0"}


def test_cf_hybrid_encode_bounds_false(full_model):
    ds = full_model.encode(bounds=False)
    assert set(ds.variables) == {"level", "ap", "b", "p0"}
    assert "bounds" not in ds["level"].attrs
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b ps: sp p0: p0"


def test_cf_hybrid_encode_no_valid_p0():
    m = CLS([1000.0, 2000.0], [0.5, 0.6], ap_bnds=[[0, 1], [1, 2]], b_bnds=[[0, 1]] * 2, levels=[1, 2], p0=0.0)
    ds = m.encode()
    assert "p0" not in ds.variables
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b ps: ps"
    assert ds["level_bnds"].attrs["formula_terms"] == "ap: ap_bnds b: b_bnds ps: ps"


def test_cf_hybrid_encode_ps_dims(full_model, tmp_path):
    ref = full_model.encode()
    ds = full_model.encode(ps_dims={"lat": 3, "lon": 4})

    assert set(ds.variables) == set(ref.variables) | {"sp"}
    ps = ds["sp"]
    assert ps.dims == ("lat", "lon")
    assert ps.shape == (3, 4)
    assert ps.dtype == np.float64
    assert np.isnan(ps.values).all()
    assert ps.attrs == {"standard_name": "surface_air_pressure", "units": "Pa", "long_name": "surface air pressure"}
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b ps: sp p0: p0"
    assert ds["level_bnds"].attrs["formula_terms"] == "ap: ap_bnds b: b_bnds ps: sp p0: p0"

    # the other variables are not changed
    for name in ref.variables:
        assert ds[name].identical(ref[name])

    # dims are kept in the given order, a scalar is possible
    assert full_model.encode(ps_dims={"x": 2, "y": 3})["sp"].dims == ("x", "y")
    assert full_model.encode(ps_dims={})["sp"].dims == ()

    # the variable is written and read back
    path = tmp_path / "ps.nc"
    ds.to_netcdf(path)
    with xr.open_dataset(path) as ds1:
        assert ds1["sp"].dims == ("lat", "lon")
        assert np.isnan(ds1["sp"].values).all()
        assert ds1["sp"].attrs["standard_name"] == "surface_air_pressure"
        assert decode_parametric_vertical(ds1).ps_name == "sp"


def test_cf_hybrid_encode_ps_dims_names():
    m = CLS([1000.0, 2000.0], [0.5, 0.6], ap_bnds=[[0, 1], [1, 2]], b_bnds=[[0, 1]] * 2, levels=[1, 2])
    ds = m.encode(ps_dims={"lat": 2}, names={"ps": "lnsp"})
    assert ds["lnsp"].dims == ("lat",)
    assert "ps" not in ds.variables

    # the placeholder is written without bounds too
    assert "ps" in m.encode(ps_dims={"lat": 2}, bounds=False).variables


def test_cf_hybrid_encode_ps_dims_invalid():
    m = CLS([1000.0, 2000.0], [0.5, 0.6], ap_bnds=[[0, 1], [1, 2]], b_bnds=[[0, 1]] * 2, levels=[1, 2])

    # no ps name
    m_no_ps = CLS([1000.0, 2000.0], [0.5, 0.6], levels=[1, 2], ps_name=None)
    m_no_ps.encode()
    with pytest.raises(ValueError):
        m_no_ps.encode(ps_dims={"lat": 2})

    # the dims must not be the names of other written variables or the ps name itself
    for name in ("level", "ap", "b", "ap_bnds", "b_bnds", "level_bnds", "bnds", "p0", "ps"):
        with pytest.raises(ValueError):
            m.encode(ps_dims={name: 2})
    with pytest.raises(ValueError):
        m.encode(ps_dims={"lat": 2, "bnds": 2})

    # names that are not written do not collide
    m.encode(ps_dims={"bnds": 2}, bounds=False)
    m.encode(ps_dims={"model_level_number": 2})

    with pytest.raises(ValueError):
        m.encode(ps_dims={"": 2})
    with pytest.raises(ValueError):
        m.encode(ps_dims={"lat": -1})
    with pytest.raises(ValueError):
        m.encode(ps_dims={"lat": 2.0})
    with pytest.raises(ValueError):
        m.encode(ps_dims=3)


# ---------------------------------------------------------------------------
# round trips
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("coord_values", ["level_number", "dimensionless"])
@pytest.mark.parametrize("bounds", [True, False])
@pytest.mark.parametrize("to_file", [False, True])
def test_cf_hybrid_roundtrip_full(full_model, l137, coord_values, bounds, to_file, tmp_path):
    A, B = l137
    ds = full_model.encode(coord_values=coord_values, bounds=bounds)

    if to_file:
        path = tmp_path / "hybrid.nc"
        ds.to_netcdf(path)
        ds = xr.open_dataset(path)

    d = CLS.from_xarray(ds, "level")
    _assert_same(full_model, d, bounds=bounds)
    assert d.p0 == 100000.0

    if bounds:
        params = d.to_level_parameters()
        A2, B2 = params.coefficients()
        np.testing.assert_array_equal(A2, A)
        np.testing.assert_array_equal(B2, B)
        assert d.can_rebuild_half_levels()
    else:
        with pytest.raises(ValueError):
            d.to_level_parameters()
        assert not d.can_rebuild_half_levels()
        np.testing.assert_array_equal(d.ap, full_model.ap)
        np.testing.assert_array_equal(d.b, full_model.b)
        np.testing.assert_array_equal(d.pressure(100000.0), full_model.pressure(100000.0))

    if to_file:
        ds.close()


@pytest.mark.parametrize("coord_values", ["level_number", "dimensionless"])
@pytest.mark.parametrize("to_file", [False, True])
def test_cf_hybrid_roundtrip_p0(l137, coord_values, to_file, tmp_path):
    # a non-default p0 is written and restored
    m = CLS.from_half_levels(*l137, p0=80000.0)
    ds = m.encode(coord_values=coord_values)
    assert ds["p0"].values == 80000.0

    if to_file:
        ds.to_netcdf(tmp_path / "p0.nc")
        ds = xr.open_dataset(tmp_path / "p0.nc")

    d = CLS.from_xarray(ds, "level")
    assert d.p0 == 80000.0
    _assert_same(m, d)
    np.testing.assert_array_equal(d.dimensionless_values(), m.dimensionless_values())
    np.testing.assert_array_equal(d.dimensionless_bounds(), m.dimensionless_bounds())
    if coord_values == "dimensionless":
        np.testing.assert_array_equal(d.dimensionless_values(), ds["level"].values)
        np.testing.assert_array_equal(d.dimensionless_bounds(), ds["level_bnds"].values)

    if to_file:
        ds.close()


@pytest.mark.parametrize("coord_values", ["level_number", "dimensionless"])
def test_cf_hybrid_roundtrip_p0_small(coord_values):
    m = CLS([1000.0, 2000.0], [0.1, 0.2], levels=[1, 2], p0=80000.0)
    d = CLS.from_xarray(m.encode(coord_values=coord_values), "level")
    assert d.p0 == 80000.0
    np.testing.assert_array_equal(d.dimensionless_values(), m.dimensionless_values())
    np.testing.assert_allclose(d.dimensionless_values(), [0.1125, 0.225])


def test_cf_hybrid_roundtrip_no_valid_p0():
    # no p0 is written, so the default of the ap form is restored
    m = CLS([1000.0, 2000.0], [0.1, 0.2], levels=[1, 2], p0=0.0)
    d = CLS.from_xarray(m.encode(), "level")
    np.testing.assert_array_equal(d.ap, m.ap)
    assert d.p0 == 100000.0


@pytest.mark.parametrize("coord_values", ["level_number", "dimensionless"])
def test_cf_hybrid_roundtrip_level_subset(l137, coord_values, tmp_path):
    A, B = l137
    m = CLS.from_half_levels(A, B, levels=[137, 1, 50])

    ds = m.encode(coord_values=coord_values)
    if coord_values == "level_number":
        np.testing.assert_array_equal(ds["level"].values, [1, 50, 137])
    else:
        np.testing.assert_array_equal(ds["model_level_number"].values, [1, 50, 137])
    np.testing.assert_array_equal(ds["ap"].values, m.ap[[1, 2, 0]])
    np.testing.assert_array_equal(ds["b"].values, m.b[[1, 2, 0]])
    np.testing.assert_array_equal(ds["ap_bnds"].values, m.ap_bnds[[1, 2, 0]])

    ds.to_netcdf(tmp_path / "subset.nc")
    with xr.open_dataset(tmp_path / "subset.nc") as ds2:
        d = CLS.from_xarray(ds2, "level")

    np.testing.assert_array_equal(d.levels, [1, 50, 137])
    np.testing.assert_array_equal(d.ap, m.ap[[1, 2, 0]])
    np.testing.assert_array_equal(d.b, m.b[[1, 2, 0]])
    np.testing.assert_array_equal(d.ap_bnds, m.ap_bnds[[1, 2, 0]])
    ps = np.array([100000.0, 95000.0])
    np.testing.assert_array_equal(d.pressure(ps), m.pressure(ps)[[1, 2, 0]])
    assert not d.can_rebuild_half_levels()
    with pytest.raises(ValueError):
        d.to_level_parameters()


def test_cf_hybrid_roundtrip_unknown_levels():
    m = CLS([1000.0, 2000.0, 500.0], [0.5, 0.6, 0.7], ap_bnds=[[0, 1], [1, 2], [2, 3]], b_bnds=[[0, 1]] * 3)
    ds = m.encode(coord_values="dimensionless")
    d = CLS.from_xarray(ds, "level")
    assert d.levels is None
    np.testing.assert_array_equal(d.ap, m.ap)
    np.testing.assert_array_equal(d.b, m.b)
    np.testing.assert_array_equal(d.ap_bnds, m.ap_bnds)


def test_cf_hybrid_decode_parametric_vertical(full_model, tmp_path):
    for coord_values in ("level_number", "dimensionless"):
        ds = full_model.encode(coord_values=coord_values)
        d = decode_parametric_vertical(ds)
        assert isinstance(d, CLS)
        _assert_same(full_model, d)

        ds.to_netcdf(tmp_path / f"{coord_values}.nc")
        with xr.open_dataset(tmp_path / f"{coord_values}.nc") as ds2:
            _assert_same(full_model, decode_parametric_vertical(ds2))
            _assert_same(full_model, decode_parametric_vertical(ds2, "level"))


@pytest.mark.parametrize("coord_values", ["level_number", "dimensionless"])
@pytest.mark.parametrize("p0", [100000.0, 80000.0])
def test_cf_hybrid_decode_coords_all(l137, coord_values, p0, tmp_path):
    # decode_coords="all" moves formula_terms and bounds from attrs to encoding
    A, B = l137
    m = CLS.from_half_levels(A, B, ps_name="sp", p0=p0)
    encoded = m.encode(coord_values=coord_values)
    # xarray only moves the attributes when all the variables of the formula terms are in the dataset
    encoded["sp"] = (("lat",), np.array([100000.0, 95000.0]), {"units": "Pa"})
    path = tmp_path / "coords_all.nc"
    encoded.to_netcdf(path)

    with xr.open_dataset(path, decode_coords="all") as ds1:
        datasets = {"open_dataset": ds1}
        with xr.open_dataset(path, decode_cf=False) as raw:
            datasets["decode_cf"] = xr.decode_cf(raw.load(), decode_coords="all")

        for name, ds in datasets.items():
            assert "formula_terms" not in ds["level"].attrs, name
            assert "formula_terms" in ds["level"].encoding, name

            for d in (
                CLS.from_xarray(ds, "level"),
                decode_parametric_vertical(ds),
                decode_parametric_vertical(ds, "level"),
            ):
                _assert_same(m, d)
                assert d.p0 == p0
                A2, B2 = d.to_level_parameters().coefficients()
                np.testing.assert_array_equal(A2, A)
                np.testing.assert_array_equal(B2, B)
                np.testing.assert_array_equal(d.dimensionless_values(), m.dimensionless_values())
                np.testing.assert_array_equal(d.dimensionless_bounds(), m.dimensionless_bounds())


def test_cf_hybrid_decode_formula_terms_in_encoding():
    # attributes only in encoding, for the coordinate and the bounds variable
    ds = _cmip6_dataset()
    for name in ("lev", "lev_bnds"):
        for key in ("formula_terms", "bounds"):
            if key in ds[name].attrs:
                ds[name].encoding[key] = ds[name].attrs.pop(key)

    d = decode_parametric_vertical(ds)
    expected = CLS.from_xarray(_cmip6_dataset(), "lev")
    _assert_same(expected, d)


# ---------------------------------------------------------------------------
# hand-built datasets
# ---------------------------------------------------------------------------


def _cmip6_dataset():
    # a complete model: zero pressure top (ap=0, b=0) and surface (ap=0, b=1)
    ap_bnds = np.array([[0.0, 1000.0], [1000.0, 3000.0], [3000.0, 0.0]])
    b_bnds = np.array([[0.0, 0.0], [0.0, 0.2], [0.2, 1.0]])
    ap = ap_bnds.mean(axis=1)
    b = b_bnds.mean(axis=1)
    lev = ap / 100000.0 + b
    lev_bnds = ap_bnds / 100000.0 + b_bnds
    return xr.Dataset(
        data_vars={
            "ap": ("lev", ap, {"long_name": "vertical coordinate formula term: ap(k)", "units": "Pa"}),
            "b": ("lev", b, {"long_name": "vertical coordinate formula term: b(k)"}),
            "ap_bnds": (("lev", "bnds"), ap_bnds, {"units": "Pa"}),
            "b_bnds": (("lev", "bnds"), b_bnds),
            "lev_bnds": (("lev", "bnds"), lev_bnds, {"formula_terms": "ap: ap_bnds b: b_bnds ps: ps"}),
            "ps": (("time", "lat", "lon"), np.full((2, 2, 3), 100000.0), {"units": "Pa"}),
        },
        coords={
            "lev": (
                "lev",
                lev,
                {
                    "standard_name": HYBRID,
                    "long_name": "hybrid sigma pressure coordinate",
                    "units": "1",
                    "axis": "Z",
                    "positive": "down",
                    "bounds": "lev_bnds",
                    "formula_terms": "ap: ap b: b ps: ps",
                },
            ),
            "time": ("time", [0, 1]),
            "lat": ("lat", [0.0, 1.0]),
            "lon": ("lon", [0.0, 1.0, 2.0]),
        },
    )


def test_cf_hybrid_decode_cmip6():
    ds = _cmip6_dataset()
    d = decode_parametric_vertical(ds)

    assert d.levels is None
    assert d.ps_name == "ps"
    assert d.p0 == 100000.0
    np.testing.assert_array_equal(d.ap, ds["ap"].values)
    np.testing.assert_array_equal(d.b, ds["b"].values)
    np.testing.assert_array_equal(d.ap_bnds, ds["ap_bnds"].values)
    np.testing.assert_array_equal(d.b_bnds, ds["b_bnds"].values)

    np.testing.assert_allclose(d.dimensionless_values(), ds["lev"].values)
    np.testing.assert_allclose(d.dimensionless_bounds(), ds["lev_bnds"].values)
    np.testing.assert_allclose(d.pressure(ds["ps"].values)[:, 0, 0, 0], d.ap + d.b * 100000.0)

    # bounds are contiguous, the half levels can be rebuilt
    A, B = d.to_level_parameters().coefficients()
    np.testing.assert_array_equal(A, [0.0, 1000.0, 3000.0, 0.0])
    np.testing.assert_array_equal(B, [0.0, 0.0, 0.2, 1.0])


def test_cf_hybrid_decode_transposed_bounds():
    ds = _cmip6_dataset()
    ds["ap_bnds"] = ds["ap_bnds"].transpose("bnds", "lev")
    ds["b_bnds"] = ds["b_bnds"].transpose("bnds", "lev")
    d = CLS.from_xarray(ds, "lev")
    np.testing.assert_array_equal(d.ap_bnds, _cmip6_dataset()["ap_bnds"].values)
    np.testing.assert_array_equal(d.b_bnds, _cmip6_dataset()["b_bnds"].values)


def test_cf_hybrid_decode_bounds_without_formula_terms(caplog):
    ds = _cmip6_dataset()
    del ds["lev_bnds"].attrs["formula_terms"]
    with caplog.at_level(logging.WARNING):
        d = CLS.from_xarray(ds, "lev")
    assert d.ap_bnds is None
    assert d.b_bnds is None
    assert "formula_terms" in caplog.text


def test_cf_hybrid_decode_bounds_mismatch():
    ds = _cmip6_dataset()
    ds["lev_bnds"].attrs["formula_terms"] = "ap: ap_bnds b: b_bnds ps: other"
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "lev")

    ds = _cmip6_dataset()
    ds["lev_bnds"].attrs["formula_terms"] = "ap: ap_bnds b: b_bnds"
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "lev")

    # bounds term not 2D, wrong size, missing variable
    ds = _cmip6_dataset()
    ds["lev_bnds"].attrs["formula_terms"] = "ap: ap b: b_bnds ps: ps"
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "lev")

    ds = _cmip6_dataset()
    ds["lev_bnds"].attrs["formula_terms"] = "ap: ap_bnds b: nothing ps: ps"
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "lev")

    # the bounds omit a term which is present in the coordinate
    ds = _cmip6_dataset()
    ds["lev_bnds"].attrs["formula_terms"] = "ap: ap_bnds ps: ps"
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "lev")


def _cesm_dataset(p0_value=100000.0, p0_units="Pa"):
    A = np.array([0.0, 0.01, 0.02, 0.0])
    B = np.array([0.0, 0.0, 0.5, 1.0])
    hyam = (A[:-1] + A[1:]) / 2
    hybm = (B[:-1] + B[1:]) / 2
    return xr.Dataset(
        data_vars={
            "hyam": ("lev", hyam, {"long_name": "hybrid A coefficient at layer midpoints"}),
            "hybm": ("lev", hybm, {"long_name": "hybrid B coefficient at layer midpoints"}),
            "P0": ((), p0_value, {"long_name": "reference pressure", "units": p0_units}),
            "PS": (("time", "lat"), np.full((1, 2), 100000.0), {"units": "Pa"}),
        },
        coords={
            "lev": (
                "lev",
                hyam + hybm,
                {
                    "standard_name": HYBRID,
                    "units": "level",
                    "positive": "down",
                    "formula_terms": "a: hyam b: hybm p0: P0 ps: PS",
                },
            )
        },
    )


@pytest.mark.parametrize("p0_value,p0_units", [(100000.0, "Pa"), (1000.0, "hPa")])
def test_cf_hybrid_decode_cesm(p0_value, p0_units):
    ds = _cesm_dataset(p0_value, p0_units)
    d = decode_parametric_vertical(ds)
    np.testing.assert_allclose(d.ap, ds["hyam"].values * 100000.0)
    np.testing.assert_array_equal(d.b, ds["hybm"].values)
    assert d.p0 == 100000.0
    assert d.ps_name == "PS"
    assert d.ap_bnds is None
    assert d.levels is None


def test_cf_hybrid_decode_cesm_bounds():
    ds = _cesm_dataset()
    hyai = np.array([[0.0, 0.01], [0.01, 0.02], [0.02, 0.0]])
    hybi = np.array([[0.0, 0.0], [0.0, 0.5], [0.5, 1.0]])
    ds["hyai"] = (("lev", "nbnd"), hyai)
    ds["hybi"] = (("nbnd", "lev"), hybi.T)
    ds["lev_bnds"] = (("lev", "nbnd"), hyai + hybi, {"formula_terms": "a: hyai b: hybi p0: P0 ps: PS"})
    ds["lev"].attrs["bounds"] = "lev_bnds"
    d = CLS.from_xarray(ds, "lev")
    np.testing.assert_allclose(d.ap_bnds, hyai * 100000.0)
    np.testing.assert_array_equal(d.b_bnds, hybi)


def test_cf_hybrid_decode_omitted_terms():
    ds = _cmip6_dataset()

    # no b, also in the bounds
    ds["lev"].attrs["formula_terms"] = "ap: ap ps: ps"
    ds["lev_bnds"].attrs["formula_terms"] = "ap: ap_bnds ps: ps"
    d = CLS.from_xarray(ds, "lev")
    np.testing.assert_array_equal(d.b, np.zeros(3))
    np.testing.assert_array_equal(d.b_bnds, np.zeros((3, 2)))
    np.testing.assert_array_equal(d.ap, ds["ap"].values)
    np.testing.assert_array_equal(d.ap_bnds, ds["ap_bnds"].values)

    # no ap/a, also in the bounds
    ds = _cmip6_dataset()
    ds["lev"].attrs["formula_terms"] = "b: b ps: ps"
    ds["lev_bnds"].attrs["formula_terms"] = "b: b_bnds ps: ps"
    d = CLS.from_xarray(ds, "lev")
    np.testing.assert_array_equal(d.ap, np.zeros(3))
    np.testing.assert_array_equal(d.ap_bnds, np.zeros((3, 2)))
    np.testing.assert_array_equal(d.b, ds["b"].values)

    # no ps
    ds = _cmip6_dataset()
    ds["lev"].attrs["formula_terms"] = "ap: ap b: b"
    ds["lev_bnds"].attrs["formula_terms"] = "ap: ap_bnds b: b_bnds"
    d = CLS.from_xarray(ds, "lev")
    assert d.ps_name is None

    # and it is not written when encoding a model without ps_name
    ds = d.encode(coord_values="dimensionless")
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b p0: p0"
    assert ds["level_bnds"].attrs["formula_terms"] == "ap: ap_bnds b: b_bnds p0: p0"


def test_cf_hybrid_decode_a_without_p0():
    ds = _cesm_dataset()
    ds["lev"].attrs["formula_terms"] = "a: hyam b: hybm ps: PS"
    d = CLS.from_xarray(ds, "lev")
    np.testing.assert_array_equal(d.ap, np.zeros(3))
    np.testing.assert_array_equal(d.b, ds["hybm"].values)

    # the reference pressure is unknown, it is not replaced by a default
    assert d.p0 == 0.0
    with pytest.raises(ValueError):
        d.dimensionless_values()
    np.testing.assert_array_equal(d.dimensionless_values(p0=100000.0), ds["hybm"].values)


def test_cf_hybrid_decode_a_without_p0_bounds():
    ds = _cesm_dataset()
    hyai = np.array([[0.0, 0.01], [0.01, 0.02], [0.02, 0.0]])
    hybi = np.array([[0.0, 0.0], [0.0, 0.5], [0.5, 1.0]])
    ds["hyai"] = (("lev", "nbnd"), hyai)
    ds["hybi"] = (("lev", "nbnd"), hybi)
    ds["lev_bnds"] = (("lev", "nbnd"), hyai + hybi, {"formula_terms": "a: hyai b: hybi ps: PS"})
    ds["lev"].attrs["formula_terms"] = "a: hyam b: hybm ps: PS"
    ds["lev"].attrs["bounds"] = "lev_bnds"
    d = CLS.from_xarray(ds, "lev")
    assert d.p0 == 0.0
    np.testing.assert_array_equal(d.ap_bnds, np.zeros((3, 2)))
    with pytest.raises(ValueError):
        d.dimensionless_bounds()
    np.testing.assert_array_equal(d.dimensionless_bounds(p0=100000.0), hybi)


def test_cf_hybrid_decode_ap_with_p0_term():
    # a p0 term is valid in the ap form too
    ds = _cmip6_dataset()
    ds["p0"] = ((), 90000.0, {"units": "Pa"})
    ds["lev"].attrs["formula_terms"] = "ap: ap b: b ps: ps p0: p0"
    ds["lev_bnds"].attrs["formula_terms"] = "ap: ap_bnds b: b_bnds ps: ps p0: p0"
    d = CLS.from_xarray(ds, "lev")
    assert d.p0 == 90000.0
    np.testing.assert_array_equal(d.ap, ds["ap"].values)


def test_cf_hybrid_decode_ap_without_p0_default():
    # CMIP style: no p0 term, the default is kept
    d = CLS.from_xarray(_cmip6_dataset(), "lev")
    assert d.p0 == 100000.0


def test_cf_hybrid_decode_errors():
    # missing variable
    ds = _cmip6_dataset()
    ds["lev"].attrs["formula_terms"] = "ap: nothing b: b ps: ps"
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "lev")

    # units
    ds = _cmip6_dataset()
    ds["ap"].attrs["units"] = "K"
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "lev")

    ds = _cmip6_dataset()
    ds["b"].attrs["units"] = "Pa"
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "lev")

    ds = _cesm_dataset()
    ds["hyam"].attrs["units"] = "Pa"
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "lev")

    ds = _cesm_dataset(p0_units="K")
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "lev")

    # a and ap
    ds = _cesm_dataset()
    ds["lev"].attrs["formula_terms"] = "a: hyam ap: hyam b: hybm p0: P0 ps: PS"
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "lev")

    # no formula_terms, unknown variable and term
    ds = _cmip6_dataset()
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "ap")
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "nothing")
    ds["lev"].attrs["formula_terms"] = "ap: ap b: b ps: ps zz: ps"
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "lev")

    # term not on the coordinate dimension
    ds = _cmip6_dataset()
    ds["lev"].attrs["formula_terms"] = "ap: ap b: ps ps: ps"
    with pytest.raises(ValueError):
        CLS.from_xarray(ds, "lev")


def test_cf_hybrid_decode_units_accepted():
    ds = _cmip6_dataset()
    ds["ap"].attrs.pop("units")
    ds["b"].attrs["units"] = ""
    d = CLS.from_xarray(ds, "lev")
    np.testing.assert_array_equal(d.ap, ds["ap"].values)

    ds["ap"].attrs["units"] = "hPa"
    ds["ap_bnds"].attrs["units"] = "hPa"
    d = CLS.from_xarray(ds, "lev")
    np.testing.assert_allclose(d.ap, ds["ap"].values * 100.0)
    np.testing.assert_allclose(d.ap_bnds, ds["ap_bnds"].values * 100.0)


def test_cf_hybrid_decode_levels():
    # level numbers from the coordinate values
    ds = _cmip6_dataset()
    ds["lev"].values[:] = [3.0, 1.0, 2.0]
    np.testing.assert_array_equal(CLS.from_xarray(ds, "lev").levels, [3, 1, 2])

    # not integers
    ds["lev"].values[:] = [3.0, 1.5, 2.0]
    assert CLS.from_xarray(ds, "lev").levels is None

    # < 1
    ds["lev"].values[:] = [3.0, 0.0, 2.0]
    assert CLS.from_xarray(ds, "lev").levels is None

    # explicit level number coordinate has priority
    ds = _cmip6_dataset()
    ds = ds.assign_coords(
        mln=("lev", [10, 20, 30], {"standard_name": "model_level_number"}),
    )
    np.testing.assert_array_equal(CLS.from_xarray(ds, "lev").levels, [10, 20, 30])


# ---------------------------------------------------------------------------
# positive
# ---------------------------------------------------------------------------

# synthetic 3 level model (4 half levels)
A3 = np.array([0.0, 2000.0, 1000.0, 0.0])
B3 = np.array([0.0, 0.0, 0.5, 1.0])

# a positive-up model: level 1 at the surface
A_UP = np.array([0.0, 0.0, 0.0])
B_UP = np.array([1.0, 0.5, 0.0])


@pytest.mark.parametrize("positive", ["down", "up"])
@pytest.mark.parametrize("to_file", [False, True])
def test_cf_hybrid_roundtrip_positive(l137, positive, to_file, tmp_path):
    A, B = l137
    if positive == "up":
        A, B = A[::-1], B[::-1]
    m = CLS.from_half_levels(A, B, positive=positive)
    ds = m.encode()
    assert ds["level"].attrs["positive"] == positive

    if to_file:
        ds.to_netcdf(tmp_path / "positive.nc")
        ds = xr.open_dataset(tmp_path / "positive.nc")

    d = CLS.from_xarray(ds, "level")
    assert d.positive == positive
    _assert_same(m, d)
    assert decode_parametric_vertical(ds).positive == positive

    if positive == "down":
        A1, B1 = d.to_level_parameters().coefficients()
        np.testing.assert_array_equal(A1, A)
        np.testing.assert_array_equal(B1, B)
    else:
        assert not d.can_rebuild_half_levels()
    np.testing.assert_array_equal(d.level_numbers(), np.arange(1, 138))

    if to_file:
        ds.close()


def test_cf_hybrid_decode_positive_attribute():
    ds = _cmip6_dataset()

    # missing: down
    del ds["lev"].attrs["positive"]
    assert CLS.from_xarray(ds, "lev").positive == "down"

    # case-insensitive
    for value, expected in (("UP", "up"), ("Down", "down"), ("up", "up")):
        ds["lev"].attrs["positive"] = value
        assert CLS.from_xarray(ds, "lev").positive == expected

    # in the encoding
    del ds["lev"].attrs["positive"]
    ds["lev"].encoding["positive"] = "up"
    assert CLS.from_xarray(ds, "lev").positive == "up"

    # invalid
    for bad in ("sideways", "", 1):
        ds = _cmip6_dataset()
        ds["lev"].attrs["positive"] = bad
        with pytest.raises(ValueError, match="positive"):
            CLS.from_xarray(ds, "lev")
        with pytest.raises(ValueError, match="positive"):
            decode_parametric_vertical(ds, "lev")


def test_cf_hybrid_encode_positive_up():
    m = CLS.from_half_levels(A_UP, B_UP, positive="up")
    ds = m.encode()
    assert ds["level"].attrs["positive"] == "up"

    # the coordinate values increase with the level number, the bounds are in level order
    np.testing.assert_array_equal(ds["level"].values, [1, 2])
    np.testing.assert_array_equal(ds["level_bnds"].values, [[0.5, 1.5], [1.5, 2.5]])
    np.testing.assert_array_equal(ds["ap_bnds"].values, [[0.0, 0.0], [0.0, 0.0]])
    np.testing.assert_array_equal(ds["b_bnds"].values, [[1.0, 0.5], [0.5, 0.0]])
    np.testing.assert_array_equal(ds["b"].values, [0.75, 0.25])

    d = CLS.from_xarray(ds, "level")
    assert d.positive == "up"
    _assert_same(m, d)
    np.testing.assert_array_equal(d.levels, [1, 2])
    np.testing.assert_array_equal(d.b_bnds, [[1.0, 0.5], [0.5, 0.0]])

    # the values decrease with the level number
    with pytest.raises(ValueError, match="increase"):
        m.encode(coord_values="dimensionless")

    # the levels are written in ascending order whatever the array order
    m = CLS.from_half_levels(A_UP, B_UP, levels=[2, 1], positive="up")
    ds = m.encode()
    np.testing.assert_array_equal(ds["level"].values, [1, 2])
    np.testing.assert_array_equal(ds["b_bnds"].values, [[1.0, 0.5], [0.5, 0.0]])


def test_cf_hybrid_positive_up_unknown_levels_level_numbers():
    m = CLS(
        [0.0, 0.0],
        [0.75, 0.25],
        ap_bnds=[[0.0, 0.0], [0.0, 0.0]],
        b_bnds=[[1.0, 0.5], [0.5, 0.0]],
        positive="up",
    )
    np.testing.assert_array_equal(m.level_numbers(), [1, 2])
    assert not m.can_rebuild_half_levels()
    with pytest.raises(ValueError, match="positive"):
        m.to_level_parameters()

    # decoded from a dataset with unknown levels (non-integer coordinate values increasing upwards)
    ds = CLS.from_half_levels(A_UP, B_UP, positive="up").encode(coord_values="level_number")
    ds["level"] = ("level", np.array([-0.75, -0.25]), ds["level"].attrs)
    d = CLS.from_xarray(ds, "level")
    assert d.levels is None
    assert d.positive == "up"
    np.testing.assert_array_equal(d.level_numbers(), [1, 2])
    np.testing.assert_array_equal(d.b_bnds, [[1.0, 0.5], [0.5, 0.0]])


def test_cf_hybrid_encode_surface_first_dimensionless():
    # positive down, the arrays are stored surface-first: the increasing check is made in level order
    m = CLS.from_half_levels(A3, B3, levels=[3, 2, 1])
    ds = m.encode(coord_values="dimensionless")
    assert ds["level"].attrs["positive"] == "down"
    values = ds["level"].values
    assert np.all(np.diff(values) > 0)
    np.testing.assert_array_equal(ds["model_level_number"].values, [1, 2, 3])
    np.testing.assert_array_equal(ds["ap"].values, m.ap[::-1])
    np.testing.assert_array_equal(ds["ap_bnds"].values, m.ap_bnds[::-1])

    d = CLS.from_xarray(ds, "level")
    np.testing.assert_array_equal(d.levels, [1, 2, 3])
    A, B = d.to_level_parameters().coefficients()
    np.testing.assert_array_equal(A, A3)
    np.testing.assert_array_equal(B, B3)

    # the values must increase with the level number, not decrease
    with pytest.raises(ValueError, match="increase"):
        CLS([1000.0, 500.0], [0.5, 0.25], levels=[1, 2]).encode(coord_values="dimensionless")
    with pytest.raises(ValueError, match="increase"):
        CLS([1000.0, 500.0], [0.5, 0.25]).encode(coord_values="dimensionless")


# ---------------------------------------------------------------------------
# CMIP6-style data: surface-first, either vertex order, no model_level_number
# ---------------------------------------------------------------------------


def _cmip6_l137_dataset(l137, flip="none", positive="down"):
    """Strict-CF dataset of the full L137 model with ``lev`` stored surface-first (IFS level 137 first).

    The coordinate values increase in the ``positive`` direction. ``flip`` selects the vertex order of
    the bounds: "none" is (upper, lower) i.e. (top, bottom), "all" is (lower, upper) and "alternate"
    mixes them cell by cell. The level bounds and the term bounds always use the same vertex order.
    """
    A, B = l137
    m = CLS.from_half_levels(A, B)
    p0 = 100000.0

    ap, b = m.ap[::-1], m.b[::-1]
    ap_bnds, b_bnds = m.ap_bnds[::-1], m.b_bnds[::-1]  # (upper, lower)
    sign = 1.0 if positive == "down" else -1.0
    lev = sign * (ap / p0 + b)
    lev_bnds = sign * (ap_bnds / p0 + b_bnds)

    if flip == "all":
        swap = np.ones(len(ap), dtype=bool)
    elif flip == "alternate":
        swap = np.arange(len(ap)) % 2 == 1
    else:
        swap = np.zeros(len(ap), dtype=bool)
    sw = swap[:, None]
    ap_bnds = np.where(sw, ap_bnds[:, ::-1], ap_bnds)
    b_bnds = np.where(sw, b_bnds[:, ::-1], b_bnds)
    lev_bnds = np.where(sw, lev_bnds[:, ::-1], lev_bnds)

    ds = xr.Dataset(
        data_vars={
            "ap": ("lev", ap, {"units": "Pa"}),
            "b": ("lev", b),
            "ap_bnds": (("lev", "bnds"), ap_bnds, {"units": "Pa"}),
            "b_bnds": (("lev", "bnds"), b_bnds),
            "lev_bnds": (("lev", "bnds"), lev_bnds, {"formula_terms": "ap: ap_bnds b: b_bnds ps: ps"}),
        },
        coords={
            "lev": (
                "lev",
                lev,
                {
                    "standard_name": HYBRID,
                    "units": "1",
                    "axis": "Z",
                    "positive": positive,
                    "bounds": "lev_bnds",
                    "formula_terms": "ap: ap b: b ps: ps",
                },
            )
        },
    )
    return ds, m


@pytest.mark.parametrize("flip", ["none", "all", "alternate"])
@pytest.mark.parametrize("to_file", [False, True])
def test_cf_hybrid_decode_cmip6_l137_surface_first(l137, flip, to_file, tmp_path):
    A, B = l137
    ds, m = _cmip6_l137_dataset(l137, flip=flip)
    # strictly increasing downwards: surface-first storage is in descending coordinate order
    assert np.all(np.diff(ds["lev"].values) < 0)

    if to_file:
        ds.to_netcdf(tmp_path / "cmip6.nc")
        ds = xr.open_dataset(tmp_path / "cmip6.nc")

    d = CLS.from_xarray(ds, "lev")
    assert d.positive == "down"
    assert d.levels is None

    # the arrays keep the order of the dataset, the bounds are in level order
    np.testing.assert_array_equal(d.ap, m.ap[::-1])
    np.testing.assert_array_equal(d.b, m.b[::-1])
    np.testing.assert_array_equal(d.ap_bnds, m.ap_bnds[::-1])
    np.testing.assert_array_equal(d.b_bnds, m.b_bnds[::-1])

    # the half levels are those of the GRIB, top-first
    assert d.can_rebuild_half_levels()
    A1, B1 = d.to_level_parameters().coefficients()
    np.testing.assert_array_equal(A1, A)
    np.testing.assert_array_equal(B1, B)

    # level numbers: array entry i is IFS level 137 - i
    ln = d.level_numbers()
    np.testing.assert_array_equal(ln, np.arange(137, 0, -1))
    np.testing.assert_array_equal(d.ap, m.ap[ln - 1])
    np.testing.assert_array_equal(d.b_bnds, m.b_bnds[ln - 1])
    assert d.levels is None

    v = d.to_vertical(137)
    assert v.level() == 137
    np.testing.assert_array_equal(v.coefficients()[0], A)

    # it can be encoded again in CF "dimensionless" mode: values increase with the level number
    ds2 = d.encode(coord_values="dimensionless")
    assert np.all(np.diff(ds2["level"].values) > 0)
    d2 = CLS.from_xarray(ds2, "level")
    assert d2.levels is None
    np.testing.assert_array_equal(d2.level_numbers(), np.arange(1, 138))
    np.testing.assert_array_equal(d2.to_level_parameters().coefficients()[0], A)

    if to_file:
        ds.close()


def test_cf_hybrid_decode_cmip6_l137_with_model_level_number(l137):
    ds, m = _cmip6_l137_dataset(l137)
    ds = ds.assign_coords(mln=("lev", np.arange(137, 0, -1), {"standard_name": "model_level_number"}))
    d = CLS.from_xarray(ds, "lev")
    np.testing.assert_array_equal(d.levels, np.arange(137, 0, -1))
    np.testing.assert_array_equal(d.level_numbers(), np.arange(137, 0, -1))
    np.testing.assert_array_equal(d.to_level_parameters().coefficients()[0], l137[0])


@pytest.mark.parametrize("flip", ["none", "all", "alternate"])
def test_cf_hybrid_decode_l137_positive_up(l137, flip):
    A, B = l137
    # coordinate values increase upward: level 1 is the surface, which is stored first
    ds, m = _cmip6_l137_dataset(l137, flip=flip, positive="up")
    d = CLS.from_xarray(ds, "lev")
    assert d.positive == "up"
    assert d.levels is None

    m_up = CLS.from_half_levels(A[::-1], B[::-1], positive="up")
    np.testing.assert_array_equal(d.ap, m_up.ap)
    np.testing.assert_array_equal(d.b, m_up.b)
    np.testing.assert_array_equal(d.ap_bnds, m_up.ap_bnds)
    np.testing.assert_array_equal(d.b_bnds, m_up.b_bnds)
    np.testing.assert_array_equal(d.level_numbers(), np.arange(1, 138))

    # but the half levels are not rebuilt
    assert not d.can_rebuild_half_levels()
    with pytest.raises(ValueError, match="positive"):
        d.to_level_parameters()
    with pytest.raises(ValueError, match="positive"):
        d.to_vertical(1)


def test_cf_hybrid_decode_bounds_level_order_errors():
    # the level bounds variable must be usable to order the vertices
    ds = _cmip6_dataset()
    ds["lev_bnds"] = (("lev", "bnds"), np.full((3, 2), np.nan), ds["lev_bnds"].attrs)
    with pytest.raises(ValueError, match="lev_bnds"):
        CLS.from_xarray(ds, "lev")

    ds = _cmip6_dataset()
    ds["lev_bnds"] = ("lev", np.zeros(3), ds["lev_bnds"].attrs)
    with pytest.raises(ValueError, match="lev_bnds"):
        CLS.from_xarray(ds, "lev")


def test_cf_hybrid_decode_incomplete_not_rebuilt_and_no_level_numbers():
    # a prefix of the model with unknown levels (no zero pressure top is possible to prove)
    ds = _cmip6_dataset()
    ap_bnds = np.array([[0.0, 1000.0], [1000.0, 3000.0], [3000.0, 6000.0]])
    ds["ap_bnds"] = (("lev", "bnds"), ap_bnds, {"units": "Pa"})
    d = CLS.from_xarray(ds, "lev")
    assert not d.can_rebuild_half_levels()
    assert d.level_numbers() is None
    with pytest.raises(ValueError, match="surface"):
        d.to_level_parameters()
