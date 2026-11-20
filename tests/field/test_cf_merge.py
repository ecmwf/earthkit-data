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
    AtmosphereHybridSigmaPressureCoordinate,
    add_parametric_vertical,
    decode_parametric_vertical,
    merge_parametric_vertical,
)

CLS = AtmosphereHybridSigmaPressureCoordinate

A = np.array([0.0, 5000.0, 4000.0, 1000.0, 0.0])
B = np.array([0.0, 0.0, 0.2, 0.7, 1.0])
PS_DIMS = {"lat": 2, "lon": 3}

STD_NAMES = {"ap", "b", "p0", "ap_bnds", "b_bnds", "level_bnds"}


@pytest.fixture
def model():
    return CLS.from_half_levels(A, B)


def _target(levels=(1, 2, 3, 4), level_dim="level"):
    levels = list(levels)
    shape = (len(levels), 2, 3)
    t = xr.DataArray(
        np.arange(np.prod(shape), dtype=np.float64).reshape(shape),
        dims=(level_dim, "lat", "lon"),
        coords={level_dim: np.array(levels, dtype=np.int64), "lat": [10.0, 20.0], "lon": [0.0, 1.0, 2.0]},
        attrs={"units": "K"},
    )
    return xr.Dataset({"t": t})


def _check_model(ds, model, level_dim="level", coord_name=None):
    """Decode the dataset and compare the result with the model."""
    d = decode_parametric_vertical(ds, coord_name or level_dim)
    np.testing.assert_array_equal(d.ap, model.ap)
    np.testing.assert_array_equal(d.b, model.b)
    np.testing.assert_array_equal(d.ap_bnds, model.ap_bnds)
    np.testing.assert_array_equal(d.b_bnds, model.b_bnds)
    np.testing.assert_array_equal(d.levels, model.levels)
    assert d.p0 == model.p0


def test_cf_merge_no_clash(model):
    target = _target()
    ds = add_parametric_vertical(target, model, "level", ps_dims=PS_DIMS)

    assert set(ds.variables) == set(target.variables) | STD_NAMES | {"ps"}
    assert list(ds.data_vars) == ["t"]
    assert set(ds.coords) == set(target.coords) | STD_NAMES | {"ps"}

    attrs = ds["level"].attrs
    assert attrs["standard_name"] == "atmosphere_hybrid_sigma_pressure_coordinate"
    assert attrs["formula_terms"] == "ap: ap b: b ps: ps p0: p0"
    assert attrs["bounds"] == "level_bnds"
    assert attrs["axis"] == "Z"
    assert attrs["positive"] == "down"
    assert ds["level_bnds"].attrs["formula_terms"] == "ap: ap_bnds b: b_bnds ps: ps p0: p0"

    assert ds["ap"].dims == ("level",)
    assert ds["ap_bnds"].dims == ("level", "bnds")
    assert ds["level_bnds"].dims == ("level", "bnds")
    assert ds["p0"].dims == ()
    assert ds["ps"].dims == ("lat", "lon")
    assert np.isnan(ds["ps"].values).all()
    assert ds["ps"].attrs["standard_name"] == "surface_air_pressure"

    # the values and the data are not changed
    np.testing.assert_array_equal(ds["level"].values, [1, 2, 3, 4])
    assert ds["t"].variable.identical(target["t"].variable)
    _check_model(ds, model)


def test_cf_merge_target_not_modified(model):
    target = _target()
    target["level"].attrs["foo"] = "bar"
    ref = target.copy(deep=True)

    ds = add_parametric_vertical(target, model, "level", ps_dims=PS_DIMS)

    assert target.identical(ref)
    assert "formula_terms" not in target["level"].attrs
    # existing attributes are kept
    assert ds["level"].attrs["foo"] == "bar"
    assert ds["level"].attrs["formula_terms"]


def test_cf_merge_ps_by_name_only(model):
    ds = add_parametric_vertical(_target(), model, "level")
    assert "ps" not in ds.variables
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b ps: ps p0: p0"

    # an existing ps is simply referred to
    target = _target()
    target = target.assign_coords(ps=(("lat", "lon"), np.full((2, 3), 1e5)))
    ds = add_parametric_vertical(target, model, "level")
    assert ds["ps"].variable.identical(target["ps"].variable)
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b ps: ps p0: p0"

    # no ps name
    m = CLS.from_half_levels(A, B, ps_name=None)
    ds = add_parametric_vertical(_target(), m, "level")
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b p0: p0"
    with pytest.raises(ValueError):
        add_parametric_vertical(_target(), m, "level", ps_dims=PS_DIMS)


def test_cf_merge_clash_different_content(model):
    target = _target()
    target = target.assign_coords(ap=("level", np.arange(4.0)), ap_bnds=("lat", [1.0, 2.0]))
    ds = add_parametric_vertical(target, model, "level", ps_dims=PS_DIMS)

    # the clashing variables are not touched
    assert ds["ap"].variable.identical(target["ap"].variable)
    assert ds["ap_bnds"].variable.identical(target["ap_bnds"].variable)

    np.testing.assert_array_equal(ds["ap_1"].values, model.ap)
    np.testing.assert_array_equal(ds["ap_bnds_1"].values, model.ap_bnds)
    assert ds["ap_bnds_1"].dims == ("level", "bnds")
    assert {"b", "b_bnds", "p0", "ps", "level_bnds"} <= set(ds.variables)

    assert ds["level"].attrs["formula_terms"] == "ap: ap_1 b: b ps: ps p0: p0"
    assert ds["level_bnds"].attrs["formula_terms"] == "ap: ap_bnds_1 b: b_bnds ps: ps p0: p0"
    assert ds["level"].attrs["bounds"] == "level_bnds"

    # the model is decoded from the renamed variables
    _check_model(ds, model)
    assert list(ds.data_vars) == ["t"]


def test_cf_merge_clash_with_dim_and_chain(model):
    # a dim named ps_1 and a variable named ps: both are taken
    target = _target()
    target["x"] = (("ps_1",), np.zeros(2))
    target = target.assign_coords(ps=("lat", [1.0, 2.0]))
    ds = add_parametric_vertical(target, model, "level", ps_dims=PS_DIMS)
    assert ds["ps_2"].dims == ("lat", "lon")
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b ps: ps_2 p0: p0"

    # ps and ps_1 variables of different content
    target = _target()
    target = target.assign_coords(ps=("lat", [1.0, 2.0]), ps_1=("lon", [1.0, 2.0, 3.0]))
    ds = add_parametric_vertical(target, model, "level", ps_dims=PS_DIMS)
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b ps: ps_2 p0: p0"


def test_cf_merge_clash_identical_content(model):
    enc = model.encode()
    target = _target()
    target = target.assign_coords(ap=enc["ap"].variable, b=enc["b"].variable, p0=enc["p0"].variable)

    ds = add_parametric_vertical(target, model, "level", ps_dims=PS_DIMS)

    # reused, no copies
    assert not [n for n in ds.variables if n.endswith("_1")]
    assert ds["ap"].variable.identical(target["ap"].variable)
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b ps: ps p0: p0"
    assert ds["level_bnds"].attrs["formula_terms"] == "ap: ap_bnds b: b_bnds ps: ps p0: p0"
    assert set(ds.variables) == set(target.variables) | {"ap_bnds", "b_bnds", "level_bnds", "ps", "bnds"} - {"bnds"}
    _check_model(ds, model)

    # the same name and values but different attrs is not identical
    target2 = _target().assign_coords(ap=("level", model.ap, {"units": "hPa"}))
    ds = add_parametric_vertical(target2, model, "level", ps_dims=PS_DIMS)
    assert "ap_1" in ds.variables
    assert ds["level"].attrs["formula_terms"] == "ap: ap_1 b: b ps: ps p0: p0"


def test_cf_merge_twice(model):
    first = add_parametric_vertical(_target(), model, "level", ps_dims=PS_DIMS)
    second = add_parametric_vertical(first, model, "level", ps_dims=PS_DIMS)

    assert set(second.variables) == set(first.variables)
    assert second.identical(first)
    assert not [n for n in second.variables if n.endswith("_1")]

    # also without ps_dims and with dimensionless values
    first = add_parametric_vertical(_target(), model, "level")
    assert add_parametric_vertical(first, model, "level").identical(first)


def test_cf_merge_ps_placeholder(model):
    # reused when identical
    ps = model.encode(ps_dims=PS_DIMS)["ps"].variable
    target = _target().assign_coords(ps=ps)
    ds = add_parametric_vertical(target, model, "level", ps_dims=PS_DIMS)
    assert "ps_1" not in ds.variables
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b ps: ps p0: p0"
    assert ds["level_bnds"].attrs["formula_terms"].endswith("ps: ps p0: p0")

    # an identical one that is a data variable is also reused (and stays a data variable)
    target = _target()
    target["ps"] = ps
    ds = add_parametric_vertical(target, model, "level", ps_dims=PS_DIMS)
    assert "ps_1" not in ds.variables
    assert list(ds.data_vars) == ["t", "ps"]

    # renamed when a different ps exists
    target = _target().assign_coords(ps=(("lat", "lon"), np.full((2, 3), 101325.0), ps.attrs))
    ds = add_parametric_vertical(target, model, "level", ps_dims=PS_DIMS)
    assert ds["ps"].variable.identical(target["ps"].variable)
    assert np.isnan(ds["ps_1"].values).all()
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b ps: ps_1 p0: p0"
    assert ds["level_bnds"].attrs["formula_terms"] == "ap: ap_bnds b: b_bnds ps: ps_1 p0: p0"

    # the same data with different attributes is not identical
    target = _target().assign_coords(ps=(("lat", "lon"), np.full((2, 3), np.nan)))
    ds = add_parametric_vertical(target, model, "level", ps_dims=PS_DIMS)
    assert "ps_1" in ds.variables


def test_cf_merge_ps_placeholder_memory(model):
    enc = model.encode(ps_dims={"lat": 5000, "lon": 5000})
    # a view of a single value
    assert enc["ps"].values.strides == (0, 0)
    assert enc["ps"].dtype == np.float64


def test_cf_merge_bnds_dim(model):
    # a dim of a different size is taken
    target = _target()
    target["x"] = (("bnds",), np.zeros(3))
    ds = add_parametric_vertical(target, model, "level", ps_dims=PS_DIMS)
    assert ds["ap_bnds"].dims == ("level", "bnds_1")
    assert ds["level_bnds"].dims == ("level", "bnds_1")
    assert ds.sizes["bnds"] == 3
    assert ds.sizes["bnds_1"] == 2
    _check_model(ds, model)

    # a variable called bnds is taken as well
    target = _target().assign_coords(bnds=("lat", [1.0, 2.0]))
    ds = add_parametric_vertical(target, model, "level")
    assert ds["ap_bnds"].dims == ("level", "bnds_1")

    # an existing dim of size 2 is reused
    target = _target()
    target["x"] = (("bnds",), np.zeros(2))
    ds = add_parametric_vertical(target, model, "level")
    assert ds["ap_bnds"].dims == ("level", "bnds")
    assert "bnds_1" not in ds.dims
    assert ds.sizes["bnds"] == 2
    _check_model(ds, model)

    # an existing dim of size 2 that is also a variable name of another kind is not reused for the bnds
    target = _target()
    target["x"] = (("bnds_1",), np.zeros(2))
    target["y"] = (("bnds",), np.zeros(5))
    ds = add_parametric_vertical(target, model, "level")
    assert ds["ap_bnds"].dims == ("level", "bnds_1")


def test_cf_merge_level_dim_ap(model):
    target = _target(level_dim="ap")
    ds = add_parametric_vertical(target, model, "ap", ps_dims=PS_DIMS)

    assert ds["t"].variable.identical(target["t"].variable)
    assert ds["ap"].dims == ("ap",)
    np.testing.assert_array_equal(ds["ap"].values, [1, 2, 3, 4])
    np.testing.assert_array_equal(ds["ap_1"].values, model.ap)
    assert ds["ap"].attrs["formula_terms"] == "ap: ap_1 b: b ps: ps p0: p0"
    # the level bounds variable would be called ap_bnds but the ap_bnds term is resolved first
    assert ds["ap"].attrs["bounds"] == "ap_bnds_1"
    assert ds["ap_bnds_1"].attrs["formula_terms"] == "ap: ap_bnds b: b_bnds ps: ps p0: p0"
    assert ds["ap_bnds_1"].dims == ("ap", "bnds")
    np.testing.assert_array_equal(ds["ap_bnds"].values, model.ap_bnds)
    _check_model(ds, model, coord_name="ap")


def test_cf_merge_level_dim_b_and_p0(model):
    for name in ("b", "p0"):
        target = _target(level_dim=name)
        ds = add_parametric_vertical(target, model, name, ps_dims=PS_DIMS)
        assert f"{name}_1" in ds.variables
        assert ds[name].dims == (name,)
        assert f"{name}: {name}_1" in ds[name].attrs["formula_terms"]
        _check_model(ds, model, coord_name=name)


def test_cf_merge_level_dim_ps(model):
    target = _target(level_dim="ps")
    ds = add_parametric_vertical(target, model, "ps", ps_dims=PS_DIMS)

    assert ds["ps"].dims == ("ps",)
    assert ds["ps_1"].dims == ("lat", "lon")
    assert np.isnan(ds["ps_1"].values).all()
    assert ds["ps"].attrs["formula_terms"] == "ap: ap b: b ps: ps_1 p0: p0"
    assert ds["ps_bnds"].attrs["formula_terms"] == "ap: ap_bnds b: b_bnds ps: ps_1 p0: p0"
    _check_model(ds, model, coord_name="ps")

    # ps is only referred to by name but it is the level dim
    with pytest.raises(ValueError):
        add_parametric_vertical(target, model, "ps")

    # not a problem for another ps name
    m = CLS.from_half_levels(A, B, ps_name="sp")
    ds = add_parametric_vertical(target, m, "ps")
    assert ds["ps"].attrs["formula_terms"] == "ap: ap b: b ps: sp p0: p0"


def test_cf_merge_level_dim_bnds(model):
    m = CLS.from_half_levels(A[:3], B[:3])  # exactly two levels
    assert len(m) == 2
    target = _target(levels=(1, 2), level_dim="bnds")

    ds = add_parametric_vertical(target, m, "bnds", ps_dims=PS_DIMS)

    assert ds.sizes["bnds"] == 2
    assert ds.sizes["bnds_1"] == 2
    assert ds["ap"].dims == ("bnds",)
    assert ds["ap_bnds"].dims == ("bnds", "bnds_1")
    assert ds["bnds_bnds"].dims == ("bnds", "bnds_1")
    assert ds["bnds"].attrs["bounds"] == "bnds_bnds"
    assert ds["bnds"].attrs["formula_terms"] == "ap: ap b: b ps: ps p0: p0"

    sub = ds.isel(bnds=[0])
    assert sub["bnds_bnds"].shape == (1, 2)
    assert sub["ap_bnds"].shape == (1, 2)
    assert sub["ap"].shape == (1,)

    d = decode_parametric_vertical(ds, "bnds")
    np.testing.assert_array_equal(d.ap, m.ap)
    np.testing.assert_array_equal(d.b, m.b)
    np.testing.assert_array_equal(d.ap_bnds, m.ap_bnds)
    np.testing.assert_array_equal(d.b_bnds, m.b_bnds)

    # the bounds dim of another size can be reused as bnds only when it is not the level dim
    d = decode_parametric_vertical(sub, "bnds")
    np.testing.assert_array_equal(d.ap_bnds, m.ap_bnds[:1])


def test_cf_merge_level_order_descending(model):
    target = _target(levels=(4, 3, 2, 1))
    ds = add_parametric_vertical(target, model, "level", ps_dims=PS_DIMS)

    np.testing.assert_array_equal(ds["level"].values, [4, 3, 2, 1])
    np.testing.assert_array_equal(ds["ap"].values, model.ap[::-1])
    np.testing.assert_array_equal(ds["b"].values, model.b[::-1])
    np.testing.assert_array_equal(ds["ap_bnds"].values, model.ap_bnds[::-1])
    np.testing.assert_array_equal(ds["b_bnds"].values, model.b_bnds[::-1])
    np.testing.assert_array_equal(ds["level_bnds"].values, model.encode()["level_bnds"].values[::-1])
    assert ds["t"].variable.identical(target["t"].variable)

    # each ap value matches its level
    for lev, ap in zip(ds["level"].values, ds["ap"].values):
        assert ap == model.ap[list(model.levels).index(lev)]

    d = decode_parametric_vertical(ds, "level")
    np.testing.assert_array_equal(d.levels, [4, 3, 2, 1])
    np.testing.assert_array_equal(d.ap, model.ap[::-1])

    # an identical variable in another order is not identical: it must be renamed
    target = _target(levels=(4, 3, 2, 1)).assign_coords(ap=("level", model.ap))
    ds = add_parametric_vertical(target, model, "level")
    assert "ap_1" in ds.variables
    np.testing.assert_array_equal(ds["ap_1"].values, model.ap[::-1])


def test_cf_merge_level_mismatch(model):
    for levels in ([1, 2, 3], [1, 2, 3, 4, 5], [1, 2, 3, 5], [0, 1, 2, 3]):
        with pytest.raises(ValueError, match="level"):
            add_parametric_vertical(_target(levels=levels), model, "level", ps_dims=PS_DIMS)

    # missing level coordinate
    with pytest.raises(ValueError):
        add_parametric_vertical(_target(), model, "lev")
    target = _target().drop_vars("level")
    with pytest.raises(ValueError):
        add_parametric_vertical(target, model, "level")

    # not a parametric coordinate
    with pytest.raises(ValueError):
        merge_parametric_vertical(_target(), _target(), "level")

    # a dimension of the encoded variables is not in the target
    with pytest.raises(ValueError):
        add_parametric_vertical(_target(), model, "level", ps_dims={"lat": 2, "foo": 3})
    with pytest.raises(ValueError):
        add_parametric_vertical(_target(), model, "level", ps_dims={"lat": 4, "lon": 3})


def test_cf_merge_data_vars_unchanged(model):
    target = _target()
    ds = add_parametric_vertical(target, model, "level", ps_dims=PS_DIMS)
    assert list(ds.data_vars) == list(target.data_vars)

    enc = model.encode(ps_dims=PS_DIMS)
    ds = merge_parametric_vertical(target, enc, "level")
    assert list(ds.data_vars) == ["t"]

    ds = merge_parametric_vertical(target, enc, "level", as_coords=False)
    assert set(ds.data_vars) == {"t", "ap", "b", "p0", "ps", "ap_bnds", "b_bnds", "level_bnds"}
    assert set(ds.coords) == {"level", "lat", "lon"}
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b ps: ps p0: p0"


def test_cf_merge_preferred_names(model):
    enc = model.encode(ps_dims=PS_DIMS)
    target = _target()
    ds = merge_parametric_vertical(
        target,
        enc,
        "level",
        preferred_names={"ap": "hyam", "b": "hybm", "bnds": "nv", "level_bnds": "lev_bounds", "unknown": "x"},
    )
    assert "ap" not in ds.variables
    np.testing.assert_array_equal(ds["hyam"].values, model.ap)
    np.testing.assert_array_equal(ds["hybm"].values, model.b)
    assert ds["ap_bnds"].dims == ("level", "nv")
    assert ds["level"].attrs["formula_terms"] == "ap: hyam b: hybm ps: ps p0: p0"
    assert ds["level"].attrs["bounds"] == "lev_bounds"
    assert ds["lev_bounds"].attrs["formula_terms"] == "ap: ap_bnds b: b_bnds ps: ps p0: p0"
    _check_model(ds, model)

    # a preferred name that is taken is numbered
    target = _target().assign_coords(hyam=("lat", [1.0, 2.0]))
    ds = merge_parametric_vertical(target, enc, "level", preferred_names={"ap": "hyam"})
    assert ds["level"].attrs["formula_terms"].startswith("ap: hyam_1 ")

    # the level dim is never used for another variable
    ds = merge_parametric_vertical(_target(), enc, "level", preferred_names={"ap": "level"})
    assert ds["level"].attrs["formula_terms"].startswith("ap: level_1 ")
    assert ds["level"].dims == ("level",)


def test_cf_merge_dimensionless(model):
    values = model.dimensionless_values()
    target = _target()
    target = target.assign_coords(level=values)
    ds = add_parametric_vertical(target, model, "level", coord_values="dimensionless", ps_dims=PS_DIMS)

    np.testing.assert_array_equal(ds["level"].values, values)
    np.testing.assert_array_equal(ds["model_level_number"].values, model.levels)
    assert ds["model_level_number"].dims == ("level",)
    assert "model_level_number" in ds.coords
    d = decode_parametric_vertical(ds, "level")
    np.testing.assert_array_equal(d.levels, model.levels)
    np.testing.assert_array_equal(d.ap, model.ap)

    # level numbers in the target do not match the dimensionless values
    with pytest.raises(ValueError):
        add_parametric_vertical(_target(), model, "level", coord_values="dimensionless")

    # merged twice
    assert add_parametric_vertical(ds, model, "level", coord_values="dimensionless", ps_dims=PS_DIMS).identical(ds)


def test_cf_merge_no_bounds(model):
    ds = add_parametric_vertical(_target(), model, "level", bounds=False, ps_dims=PS_DIMS)
    assert set(ds.variables) == set(_target().variables) | {"ap", "b", "p0", "ps"}
    assert "bounds" not in ds["level"].attrs
    assert "bnds" not in ds.dims


@pytest.mark.parametrize("level_dim", ["level", "ap", "ps", "bnds"])
@pytest.mark.parametrize("descending", [False, True])
@pytest.mark.parametrize("with_clash", [False, True])
def test_cf_merge_netcdf_roundtrip(model, level_dim, descending, with_clash, tmp_path):
    levels = (4, 3, 2, 1) if descending else (1, 2, 3, 4)
    target = _target(levels, level_dim=level_dim)
    if with_clash:
        target = target.assign_coords(b=("lat", [1.0, 2.0]), ap_bnds=("lon", [1.0, 2.0, 3.0]))

    ds = add_parametric_vertical(target, model, level_dim, ps_dims=PS_DIMS)

    path = tmp_path / "merged.nc"
    ds.to_netcdf(path)

    with xr.open_dataset(path) as ds1:
        assert list(ds1.data_vars) == ["t"]
        assert ds1[level_dim].attrs["standard_name"] == "atmosphere_hybrid_sigma_pressure_coordinate"
        d = decode_parametric_vertical(ds1, level_dim)
        order = slice(None, None, -1) if descending else slice(None)
        np.testing.assert_array_equal(d.ap, model.ap[order])
        np.testing.assert_array_equal(d.b, model.b[order])
        np.testing.assert_array_equal(d.ap_bnds, model.ap_bnds[order])
        np.testing.assert_array_equal(d.b_bnds, model.b_bnds[order])
        assert d.p0 == model.p0
        assert d.ps_name in ds1.variables or d.ps_name is None
        ps = ds1[d.ps_name]
        assert ps.dims == ("lat", "lon")
        assert np.isnan(ps.values).all()

    # decoding the netcdf file with decode_coords="all"
    with xr.open_dataset(path, decode_coords="all") as ds2:
        d = decode_parametric_vertical(ds2, level_dim)
        np.testing.assert_array_equal(d.ap, model.ap[order])
