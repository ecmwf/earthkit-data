#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Tests for the CF hybrid sigma-pressure parametric vertical coordinate added by the xr_engine."""

import logging

import numpy as np
import pytest
from xr_engine_fixtures import load_grib_data

import earthkit.data as ekd
from earthkit.data.field.cf import decode_parametric_vertical, parse_formula_terms

PARAMETRIC_LOGGER = "earthkit.data.xr_engine.parametric"

CF_ATTRS = {
    "standard_name": "atmosphere_hybrid_sigma_pressure_coordinate",
    "positive": "down",
    "axis": "Z",
    "computed_standard_name": "air_pressure",
}

# synthetic half level coefficients, 11 model levels
A11 = np.linspace(0.0, 2000.0, 12) ** 1.1
B11 = np.linspace(0.0, 1.0, 12) ** 2
A11_OTHER = A11 + 1.0


def ml_fieldlist():
    ds, _ = load_grib_data("ml_data.grib", "file", folder="data")
    return ds


def ml_coefficients(fl):
    A, B = fl.sel({"parameter.variable": "t"})[0].vertical.coefficients()
    return np.asarray(A, dtype=np.float64), np.asarray(B, dtype=np.float64)


def synthetic_fieldlist(
    A=A11,
    B=B11,
    levels=range(1, 12),
    variables=("t",),
    members=(None,),
    level_type="hybrid",
    coefficients=True,
):
    fields = []
    for member in members:
        for variable in variables:
            for lev in levels:
                vertical = {"level": lev, "level_type": level_type}
                if coefficients and level_type == "hybrid":
                    vertical["coefficients"] = (A, B)

                kwargs = {}
                if member is not None:
                    kwargs["ensemble"] = {"member": member}

                fields.append(
                    ekd.Field.from_components(
                        values=np.array([lev, lev + 1, lev + 2], dtype=np.float64),
                        parameter={"variable": variable, "units": "K"},
                        vertical=vertical,
                        **kwargs,
                    )
                )
    return ekd.FieldList.from_fields(fields)


def check_hybrid(ds, level, A, B, ps_dims, ref_levels=None):
    """Check the CF hybrid coordinate on dimension ``level`` and return the final names of the terms."""
    levels = np.asarray(ds[level].values)
    if ref_levels is not None:
        assert levels.tolist() == list(ref_levels)

    attrs = ds[level].attrs
    assert CF_ATTRS.items() <= attrs.items()

    terms = parse_formula_terms(attrs["formula_terms"])
    assert set(terms) == {"ap", "b", "ps", "p0"}

    exp_ap_bnds = np.stack([A[levels - 1], A[levels]], axis=1)
    exp_b_bnds = np.stack([B[levels - 1], B[levels]], axis=1)

    ap = ds[terms["ap"]]
    assert ap.dims == (level,)
    np.testing.assert_allclose(ap.values, exp_ap_bnds.mean(axis=1))
    b = ds[terms["b"]]
    assert b.dims == (level,)
    np.testing.assert_allclose(b.values, exp_b_bnds.mean(axis=1))

    p0 = ds[terms["p0"]]
    assert p0.dims == ()
    assert float(p0) == 100000.0

    ps = ds[terms["ps"]]
    assert ps.dims == tuple(ps_dims)
    assert dict(ps.sizes) == dict(ps_dims)
    assert ps.attrs["standard_name"] == "surface_air_pressure"
    assert np.isnan(ps.values).all()

    bnds = ds[attrs["bounds"]]
    assert len(bnds.dims) == 2 and bnds.dims[0] == level
    bdim = bnds.dims[1]
    assert bdim != level
    assert ds.sizes[bdim] == 2
    np.testing.assert_allclose(bnds.values, levels[:, None] + np.array([-0.5, 0.5]))

    bterms = parse_formula_terms(bnds.attrs["formula_terms"])
    assert set(bterms) == {"ap", "b", "ps", "p0"}
    assert bterms["ps"] == terms["ps"]
    assert bterms["p0"] == terms["p0"]
    ap_bnds = ds[bterms["ap"]]
    b_bnds = ds[bterms["b"]]
    assert ap_bnds.dims == (level, bdim)
    assert b_bnds.dims == (level, bdim)
    np.testing.assert_allclose(ap_bnds.values, exp_ap_bnds)
    np.testing.assert_allclose(b_bnds.values, exp_b_bnds)

    # all the added variables are coordinates
    added = {*terms.values(), attrs["bounds"], *bterms.values()}
    for name in added:
        assert name in ds.coords, name
        assert name not in ds.data_vars, name

    return {**terms, "bounds": attrs["bounds"], "ap_bnds": bterms["ap"], "b_bnds": bterms["b"], "bnds": bdim}


def check_no_hybrid(ds):
    for name in ("ap", "b", "p0", "ps", "ap_bnds", "b_bnds", "bnds"):
        assert name not in ds.variables, name
        assert name not in ds.dims, name
    for var in ds.variables.values():
        assert "formula_terms" not in var.attrs
        assert "bounds" not in var.attrs


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_hybrid_level(allow_holes, lazy_load):
    fl = ml_fieldlist()
    A, B = ml_coefficients(fl)

    ds = fl.to_xarray(allow_holes=allow_holes, lazy_load=lazy_load)

    assert sorted(ds.data_vars) == ["lnsp", "t"]
    assert ds["t"].dims == ("level", "latitude", "longitude")

    names = check_hybrid(ds, "level", A, B, {"latitude": 7, "longitude": 5})
    assert names == {
        "ap": "ap",
        "b": "b",
        "ps": "ps",
        "p0": "p0",
        "bounds": "level_bnds",
        "ap_bnds": "ap_bnds",
        "b_bnds": "b_bnds",
        "bnds": "bnds",
    }
    assert ds["level"].attrs["formula_terms"] == "ap: ap b: b ps: ps p0: p0"
    assert ds["level"].attrs["bounds"] == "level_bnds"
    # the levels are still the model level numbers
    assert ds["level"].values.tolist() == list(
        fl.sel({"parameter.variable": "t"}).unique("vertical.level")["vertical.level"]
    )
    assert ds["level"].dtype.kind == "i"


@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_hybrid_level_per_type(lazy_load):
    fl = ml_fieldlist()
    A, B = ml_coefficients(fl)

    ds = fl.to_xarray(level_dim_mode="level_per_type", lazy_load=lazy_load)

    assert "level" not in ds.dims
    assert sorted(ds.data_vars) == ["lnsp", "t"]
    names = check_hybrid(ds, "hybrid", A, B, {"latitude": 7, "longitude": 5})
    assert names["bounds"] == "hybrid_bnds"
    assert ds["hybrid"].attrs["formula_terms"] == "ap: ap b: b ps: ps p0: p0"


@pytest.mark.cache
def test_xr_engine_hybrid_level_and_type_skipped():
    ds = ml_fieldlist().to_xarray(level_dim_mode="level_and_type")
    assert "level_and_type" in ds.dims
    check_no_hybrid(ds)


@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_hybrid_release_source(lazy_load):
    fl = ml_fieldlist()
    fl_ref = ml_fieldlist()
    A, B = ml_coefficients(fl_ref)

    ds = fl.to_xarray(lazy_load=lazy_load, release_source=True)
    check_hybrid(ds, "level", A, B, {"latitude": 7, "longitude": 5})

    ref = fl_ref.sel({"parameter.variable": "t"}).order_by("vertical.level").to_numpy()
    np.testing.assert_allclose(ds["t"].values, ref)


@pytest.mark.cache
@pytest.mark.parametrize("name", ["b", "ps"])
def test_xr_engine_hybrid_clash_variable(name):
    fl = ml_fieldlist()
    A, B = ml_coefficients(fl)

    ds = fl.to_xarray(rename_variables={"t": name})

    assert name in ds.data_vars
    assert ds[name].dims == ("level", "latitude", "longitude")

    names = check_hybrid(ds, "level", A, B, {"latitude": 7, "longitude": 5})
    assert names[name] == f"{name}_1"
    assert ds["level"].attrs["formula_terms"] == (
        "ap: ap b: b_1 ps: ps p0: p0" if name == "b" else "ap: ap b: b ps: ps_1 p0: p0"
    )
    # the data variable keeps its name and data
    assert name not in ds.coords


@pytest.mark.cache
@pytest.mark.parametrize("level_name", ["ap", "bnds"])
def test_xr_engine_hybrid_clash_level_dim(level_name):
    fl = ml_fieldlist()
    A, B = ml_coefficients(fl)

    ds = fl.to_xarray(rename_dims={"level": level_name})

    assert level_name in ds.dims
    assert "level" not in ds.dims
    names = check_hybrid(ds, level_name, A, B, {"latitude": 7, "longitude": 5})
    # the level dimension is never used as the name of a term, bounds variable or bounds dimension
    assert level_name not in names.values()
    if level_name == "ap":
        assert names["ap"] == "ap_1"
    else:
        assert names["bnds"] == "bnds_1"


@pytest.mark.cache
def test_xr_engine_hybrid_rename_horizontal_dims():
    fl = ml_fieldlist()
    A, B = ml_coefficients(fl)

    ds = fl.to_xarray(rename_dims={"latitude": "lat", "longitude": "lon"})

    assert ds["t"].dims == ("level", "lat", "lon")
    check_hybrid(ds, "level", A, B, {"lat": 7, "lon": 5})
    assert ds["ps"].dims == ("lat", "lon")


@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_hybrid_flatten_values(lazy_load):
    fl = ml_fieldlist()
    A, B = ml_coefficients(fl)

    ds = fl.to_xarray(flatten_values=True, lazy_load=lazy_load)

    assert ds["t"].dims == ("level", "values")
    check_hybrid(ds, "level", A, B, {"values": 35})
    assert ds["ps"].dims == ("values",)


@pytest.mark.cache
def test_xr_engine_hybrid_split_dims_variable():
    fl = ml_fieldlist()
    A, B = ml_coefficients(fl)

    datasets, split_coords = fl.to_xarray(split_dims="parameter.variable")
    assert len(datasets) == 2

    by_var = {next(iter(ds.data_vars)): ds for ds in datasets}
    assert sorted(by_var) == ["lnsp", "t"]

    # lnsp has a single level that is squeezed
    check_no_hybrid(by_var["lnsp"])
    check_hybrid(by_var["t"], "level", A, B, {"latitude": 7, "longitude": 5})


@pytest.mark.parametrize("direct_backend", [True, False])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_hybrid_split_dims_member(lazy_load, direct_backend):
    fl = synthetic_fieldlist(members=(0, 1))

    datasets, split_coords = fl.to_xarray(
        split_dims="ensemble.member", lazy_load=lazy_load, direct_backend=direct_backend
    )
    assert len(datasets) == 2
    for ds in datasets:
        assert ds["t"].dims == ("level", "values")
        check_hybrid(ds, "level", A11, B11, {"values": 3}, ref_levels=range(1, 12))


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_hybrid_synthetic(allow_holes, lazy_load):
    fl = synthetic_fieldlist(variables=("t", "q"), members=(0, 1))

    ds = fl.to_xarray(allow_holes=allow_holes, lazy_load=lazy_load)

    assert sorted(ds.data_vars) == ["q", "t"]
    assert ds["t"].dims == ("member", "level", "values")
    check_hybrid(ds, "level", A11, B11, {"values": 3}, ref_levels=range(1, 12))


@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_hybrid_synthetic_subset_of_levels(lazy_load):
    levels = [3, 5, 6, 10]
    fl = synthetic_fieldlist(levels=levels)

    ds = fl.to_xarray(lazy_load=lazy_load)
    check_hybrid(ds, "level", A11, B11, {"values": 3}, ref_levels=levels)


@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_hybrid_single_level(lazy_load):
    fl = synthetic_fieldlist(levels=[4])

    # squeezed: no level dimension, so nothing is added
    ds = fl.to_xarray(lazy_load=lazy_load)
    assert "level" not in ds.dims
    check_no_hybrid(ds)

    # retained as a dimension
    ds = fl.to_xarray(lazy_load=lazy_load, ensure_dims=["level"])
    assert ds.sizes["level"] == 1
    check_hybrid(ds, "level", A11, B11, {"values": 3}, ref_levels=[4])


def test_xr_engine_hybrid_no_coefficients():
    fl = synthetic_fieldlist(coefficients=False)

    ds = fl.to_xarray()

    assert ds.sizes["level"] == 11
    check_no_hybrid(ds)
    assert sorted(ds.coords) == ["level"]

    from earthkit.data.field.component.level_type import get_level_type

    assert ds["level"].attrs == get_level_type("hybrid").cf


def test_xr_engine_hybrid_pressure_levels():
    fl = synthetic_fieldlist(level_type="pressure", levels=[300, 500, 700])

    ds = fl.to_xarray()

    assert ds.sizes["level"] == 3
    check_no_hybrid(ds)
    assert sorted(ds.coords) == ["level"]

    from earthkit.data.field.component.level_type import get_level_type

    assert ds["level"].attrs == get_level_type("pressure").cf


def test_xr_engine_hybrid_mixed_level_types():
    fl = ekd.FieldList.from_fields(
        list(synthetic_fieldlist(variables=("t",), levels=range(1, 6)))
        + list(synthetic_fieldlist(variables=("u",), levels=range(1, 6), level_type="pressure"))
    )

    ds = fl.to_xarray()

    assert sorted(ds.data_vars) == ["t", "u"]
    assert ds.sizes["level"] == 5
    check_no_hybrid(ds)


def test_xr_engine_hybrid_different_coefficients(caplog):
    fl = ekd.FieldList.from_fields(
        list(synthetic_fieldlist(variables=("t",), A=A11, B=B11))
        + list(synthetic_fieldlist(variables=("q",), A=A11_OTHER, B=B11))
    )

    with caplog.at_level(logging.WARNING, logger=PARAMETRIC_LOGGER):
        ds = fl.to_xarray()

    warnings = [r for r in caplog.records if r.name == PARAMETRIC_LOGGER and r.levelno == logging.WARNING]
    assert len(warnings) == 1
    assert "differ" in warnings[0].getMessage()

    assert sorted(ds.data_vars) == ["q", "t"]
    check_no_hybrid(ds)


def test_xr_engine_hybrid_same_coefficients_no_warning(caplog):
    fl = synthetic_fieldlist(variables=("t", "q"))

    with caplog.at_level(logging.DEBUG, logger=PARAMETRIC_LOGGER):
        ds = fl.to_xarray()

    assert not [r for r in caplog.records if r.name == PARAMETRIC_LOGGER and r.levelno >= logging.WARNING]
    check_hybrid(ds, "level", A11, B11, {"values": 3})


def test_xr_engine_hybrid_levels_out_of_range(caplog):
    # level 20 does not exist in 11 level coefficients: skipped with a warning
    fl = synthetic_fieldlist(levels=[1, 5, 20])

    with caplog.at_level(logging.WARNING, logger=PARAMETRIC_LOGGER):
        ds = fl.to_xarray()

    assert [r for r in caplog.records if r.name == PARAMETRIC_LOGGER and r.levelno == logging.WARNING]
    check_no_hybrid(ds)
    assert ds["level"].values.tolist() == [1, 5, 20]


@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_hybrid_to_fieldlist(lazy_load):
    fl = ml_fieldlist()

    ds = fl.to_xarray(lazy_load=lazy_load)
    fl2 = ds.earthkit.to_fieldlist()

    assert len(fl2) == len(fl)
    for var in ("t", "lnsp"):
        assert fl2.sel({"parameter.variable": var}).unique("vertical.level") == fl.sel({
            "parameter.variable": var
        }).unique("vertical.level")
    np.testing.assert_allclose(
        fl2.sel({"parameter.variable": "t"}).order_by("vertical.level").to_numpy(),
        fl.sel({"parameter.variable": "t"}).order_by("vertical.level").to_numpy(),
    )


@pytest.mark.cache
@pytest.mark.parametrize("method", ["to_xarray", "accessor"])
def test_xr_engine_hybrid_netcdf_roundtrip(tmp_path, method):
    import xarray as xr

    fl = ml_fieldlist()
    A, B = ml_coefficients(fl)
    path = str(tmp_path / "ml.nc")

    if method == "to_xarray":
        ds = fl.to_xarray(add_earthkit_attrs=False)
        ds.to_netcdf(path)
    else:
        ds = fl.to_xarray()
        ds.earthkit.to_netcdf(path, remove_earthkit_attrs=True)

    ds2 = xr.open_dataset(path)
    try:
        assert "ap" in ds2.variables and "ps" in ds2.variables
        assert CF_ATTRS.items() <= ds2["level"].attrs.items()

        model = decode_parametric_vertical(ds2)
        levels = ds["level"].values
        np.testing.assert_allclose(model.ap, ds["ap"].values)
        np.testing.assert_allclose(model.b, ds["b"].values)
        np.testing.assert_allclose(model.ap, (A[levels - 1] + A[levels]) / 2)
        np.testing.assert_allclose(model.b, (B[levels - 1] + B[levels]) / 2)
        np.testing.assert_allclose(model.ap_bnds, ds["ap_bnds"].values)
        np.testing.assert_allclose(model.b_bnds, ds["b_bnds"].values)
        assert model.levels.tolist() == levels.tolist()
        assert model.p0 == 100000.0
    finally:
        ds2.close()
