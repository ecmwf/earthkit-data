#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import sys

import pandas as pd
import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import compare_coords  # noqa: E402
from xr_engine_fixtures import compare_dim_order  # noqa: E402
from xr_engine_fixtures import compare_dims  # noqa: E402


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "kwargs,dim_keys",
    [
        (
            {
                "profile": "mars",
                "time_dim_mode": "raw",
                "rename_dims": {"levelist": "zz"},
                "dim_name_from_role_name": False,
            },
            ["date", "time", "step", "zz"],
        ),
        (
            {
                "profile": "mars",
                "time_dim_mode": "raw",
                "rename_dims": {"level": "zz"},
            },
            ["date", "time", "step", "zz"],
        ),
    ],
)
def test_xr_rename_dims(allow_holes, lazy_load, kwargs, dim_keys):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib"))
    ds = ds_ek.to_xarray(allow_holes=allow_holes, lazy_load=lazy_load, **kwargs)
    num = len(ds)

    dim_keys = dim_keys + ["latitude", "longitude"]
    assert len(ds) == num

    for v in ds:
        compare_dim_order(ds, dim_keys, v)


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "kwargs,dim_keys",
    [
        (
            {
                "profile": "mars",
                "fixed_dims": ["metadata.date", "metadata.time", "metadata.step", "metadata.level"],
            },
            ["date", "time", "step", "level"],
        ),
        (
            {
                "profile": "mars",
                "fixed_dims": ["metadata.level", "metadata.date", "metadata.time", "metadata.step"],
            },
            ["level", "date", "time", "step"],
        ),
        (
            {
                "profile": "mars",
                "fixed_dims": [
                    {"my_date": "metadata.date"},
                    ("my_time", "metadata.time"),
                    "metadata.step",
                    "metadata.level",
                ],
            },
            ["my_date", "my_time", "step", "level"],
        ),
        (
            {
                "profile": "mars",
                "fixed_dims": ["time.forecast_reference_time", "metadata.endStep", "metadata.level"],
            },
            ["forecast_reference_time", "endStep", "level"],
        ),
        (
            {
                "profile": "mars",
                "fixed_dims": [
                    "time.forecast_reference_time",
                    ("step", "metadata.endStep"),
                    "metadata.level",
                ],
            },
            ["forecast_reference_time", "step", "level"],
        ),
    ],
)
def test_xr_fixed_dims(allow_holes, lazy_load, kwargs, dim_keys):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib"))
    ds = ds_ek.to_xarray(allow_holes=allow_holes, lazy_load=lazy_load, **kwargs)
    num = len(ds)

    dim_keys = dim_keys + ["latitude", "longitude"]
    assert len(ds) == num

    for v in ds:
        compare_dim_order(ds, dim_keys, v)


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "kwargs,dim_keys",
    [
        (
            {
                "profile": "mars",
                "drop_dims": "number",
                "time_dim_mode": "raw",
                "squeeze": False,
                "dim_name_from_role_name": True,
            },
            ["date", "time", "step", "level", "level_type"],
        ),
        (
            {
                "profile": "mars",
                "drop_dims": ["level_type", "number"],
                "time_dim_mode": "raw",
                "squeeze": False,
                "dim_name_from_role_name": True,
            },
            ["date", "time", "step", "level"],
        ),
        (
            {
                "profile": "mars",
                "drop_dims": "metadata.number",
                "time_dim_mode": "raw",
                "squeeze": False,
                "dim_name_from_role_name": False,
            },
            ["date", "time", "step", "levelist", "levtype"],
        ),
        (
            {
                "profile": "mars",
                "drop_dims": ["metadata.levtype", "metadata.number"],
                "time_dim_mode": "raw",
                "squeeze": False,
                "dim_name_from_role_name": False,
            },
            ["date", "time", "step", "levelist"],
        ),
    ],
)
def test_xr_drop_dims(allow_holes, lazy_load, kwargs, dim_keys):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib"))
    ds = ds_ek.to_xarray(allow_holes=allow_holes, lazy_load=lazy_load, **kwargs)
    num = len(ds)

    dim_keys = dim_keys + ["latitude", "longitude"]
    assert len(ds) == num

    for v in ds:
        compare_dim_order(ds, dim_keys, v)


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "path,sel,kwargs,coords,dims,var_attrs,global_attrs",
    [
        (
            "level/pl_small.grib",
            {
                "metadata.shortName": "t",
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 1200,
                "metadata.level": 500,
            },
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "level_dim_mode": "level_and_type",
                "dim_name_from_role_name": True,
                "squeeze": True,
                "ensure_dims": ["level_and_type", "forecast_reference_time"],
                "dims_as_attrs": ["member", "level_and_type"],
                "rename_attrs": {"member": "realisation"},
                "rename_dims": {"step": "STEP", "level_and_type": "LEVEL_AND_TYPE"},
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [pd.Timestamp("2024-06-03 12:00:00")],
                "STEP": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "LEVEL_AND_TYPE": ["500isobaricInhPa"],
            },
            {"forecast_reference_time": 1, "STEP": 2, "LEVEL_AND_TYPE": 1},
            {
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "kelvin",
                    "typeOfLevel": "isobaricInhPa",
                    "realisation": 0,
                    "level_and_type": "500isobaricInhPa",
                }
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
        (
            "level/pl_small.grib",
            {
                "metadata.shortName": "t",
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 1200,
                "metadata.level": 500,
            },
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "remapping": {"my_level": "{metadata.level}__{metadata.typeOfLevel}"},
                "ensure_dims": ["my_level", "metadata.expver"],
                "dims_as_attrs": ["forecast_reference_time", "member"],
                "add_earthkit_attrs": False,
            },
            {
                "my_level": ["500__isobaricInhPa"],
                "expver": ["0001"],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
            },
            {"my_level": 1, "expver": 1, "step": 2},
            {
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "kelvin",
                    "typeOfLevel": "isobaricInhPa",
                    "member": 0,
                    "forecast_reference_time": "2024-06-03T12:00:00",
                }
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
    ],
)
def test_xr_ensure_dims(allow_holes, lazy_load, path, sel, kwargs, coords, dims, var_attrs, global_attrs):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", path))
    if sel:
        ds0 = ds0.sel(**sel)
    ds = ds0.to_xarray(lazy_load=lazy_load, allow_holes=allow_holes, **kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    for v in var_attrs:
        v_attrs = dict(ds[v].attrs)
        v_attrs.pop("_earthkit", None)
        v_attrs.pop("ek_grid_spec", None)
        assert v_attrs == var_attrs[v]
    assert ds.attrs == global_attrs


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "path,sel,kwargs,coords,dims,var_attrs,global_attrs",
    [
        (
            "level/pl_small.grib",
            None,
            {
                "profile": "grib",
                "extra_dims": [{"exp_version": "metadata.expver"}],
                "squeeze": False,
                "add_earthkit_attrs": False,
            },
            {
                "exp_version": ["0001"],
                "member": [0],
                "forecast_reference_time": [
                    pd.Timestamp("2024-06-03 00:00:00"),
                    pd.Timestamp("2024-06-03 12:00:00"),
                    pd.Timestamp("2024-06-04 00:00:00"),
                    pd.Timestamp("2024-06-04 12:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "level": [500, 700],
                "level_type": ["isobaricInhPa"],
            },
            {
                "exp_version": 1,
                "member": 1,
                "forecast_reference_time": 4,
                "step": 2,
                "level": 2,
                "level_type": 1,
            },
            {
                "r": {
                    "standard_name": "relative_humidity",
                    "long_name": "Relative humidity",
                    "units": "percent",
                    "typeOfLevel": "isobaricInhPa",
                },
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "kelvin",
                    "typeOfLevel": "isobaricInhPa",
                },
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
        (
            "level/pl_small.grib",
            None,
            {
                "profile": "grib",
                "extra_dims": [{"exp_version": "metadata.expver"}],
                "squeeze": True,
                "ensure_dims": ["exp_version"],
                "add_earthkit_attrs": False,
            },
            {
                "exp_version": ["0001"],
                "forecast_reference_time": [
                    pd.Timestamp("2024-06-03 00:00:00"),
                    pd.Timestamp("2024-06-03 12:00:00"),
                    pd.Timestamp("2024-06-04 00:00:00"),
                    pd.Timestamp("2024-06-04 12:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "level": [500, 700],
            },
            {"exp_version": 1, "forecast_reference_time": 4, "step": 2, "level": 2},
            {
                "r": {
                    "standard_name": "relative_humidity",
                    "long_name": "Relative humidity",
                    "units": "percent",
                    "typeOfLevel": "isobaricInhPa",
                },
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "kelvin",
                    "typeOfLevel": "isobaricInhPa",
                },
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
        (
            "level/pl_small.grib",
            None,
            {
                "profile": "grib",
                "remapping": {"my_ver": "GRIB{metadata.edition}_ver{metadata.expver}"},
                "extra_dims": ["my_ver"],
                "squeeze": True,
                "ensure_dims": ["my_ver"],
                "add_earthkit_attrs": False,
            },
            {
                "my_ver": ["GRIB1_ver0001"],
                "forecast_reference_time": [
                    pd.Timestamp("2024-06-03 00:00:00"),
                    pd.Timestamp("2024-06-03 12:00:00"),
                    pd.Timestamp("2024-06-04 00:00:00"),
                    pd.Timestamp("2024-06-04 12:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "level": [500, 700],
            },
            {"my_ver": 1, "forecast_reference_time": 4, "step": 2, "level": 2},
            {
                "r": {
                    "standard_name": "relative_humidity",
                    "long_name": "Relative humidity",
                    "units": "percent",
                    "typeOfLevel": "isobaricInhPa",
                },
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "kelvin",
                    "typeOfLevel": "isobaricInhPa",
                },
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
        (
            "ens/quantiles_pd.grib",
            None,
            {
                "profile": "grib",
                "time_dim_mode": "valid_time",
                "extra_dims": "metadata.quantile",
                "drop_dims": "member",
                "dims_as_attrs": ["level", "level_type", "valid_time"],
                "variable_attrs": "parameter.units",
                "add_earthkit_attrs": False,
            },
            {
                "quantile": [
                    "10:10",
                    "1:10",
                    "1:3",
                    "1:5",
                    "2:10",
                    "2:3",
                    "2:5",
                    "3:10",
                    "3:3",
                    "3:5",
                    "4:10",
                    "4:5",
                    "5:10",
                    "5:5",
                    "6:10",
                    "7:10",
                    "8:10",
                    "9:10",
                ],
            },
            {"quantile": 18},
            {
                "2tp": {
                    "units": "percent",
                    "valid_time": "2025-12-16T00:00:00",
                    "level": 0,
                    "level_type": "surface",
                }
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
        (
            "wave_spectra.grib",
            None,
            {
                "profile": "grib",
                "time_dim_mode": "valid_time",
                "extra_dims": ["metadata.directionNumber", "metadata.frequencyNumber"],
                "squeeze": False,
                "add_earthkit_attrs": False,
            },
            {
                "directionNumber": [6, 12, 18, 24, 30, 36],
                "frequencyNumber": [1, 15, 29],
                "member": [0],
                "valid_time": [pd.Timestamp("2025-12-10 00:00:00")],
                "level": [0],
                "level_type": ["meanSea"],
            },
            {
                "directionNumber": 6,
                "frequencyNumber": 3,
                "member": 1,
                "valid_time": 1,
                "level": 1,
                "level_type": 1,
            },
            {
                "2dfd": {
                    "standard_name": "unknown",
                    "long_name": "2D wave spectra (single)",
                    "units": "meter ** 2 * second / radian",
                    "typeOfLevel": "meanSea",
                }
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
    ],
)
def test_xr_extra_dims(allow_holes, lazy_load, path, sel, kwargs, coords, dims, var_attrs, global_attrs):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", path))
    if sel:
        ds0 = ds0.sel(**sel)
    ds = ds0.to_xarray(lazy_load=lazy_load, allow_holes=allow_holes, **kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    for v in var_attrs:
        v_attrs = dict(ds[v].attrs)
        v_attrs.pop("_earthkit", None)
        v_attrs.pop("ek_grid_spec", None)
        assert v_attrs == var_attrs[v]
    assert ds.attrs == global_attrs


@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "path,sel,kwargs,coords,dims,var_attrs,global_attrs",
    [
        (
            "level/pl_sfc.grib1",
            {
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 0,
                "metadata.step": 0,
                "metadata.level": [0, 850],
            },
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "level_dim_mode": "level_per_type",
                "dim_name_from_role_name": True,
                "squeeze": True,
                "ensure_dims": "<level_per_type>",
                "variable_attrs": [],
                "global_attrs": [],
                "add_earthkit_attrs": False,
            },
            {
                "isobaricInhPa": [850],
                "surface": [0],
            },
            {"isobaricInhPa": 1, "surface": 1},
            {"2t": {}, "msl": {}, "r": {}, "t": {}, "u": {}, "v": {}, "z": {}},
            {},
        ),
        (
            "level/pl_sfc.grib1",
            None,
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "level_dim_mode": "level_per_type",
                "dim_name_from_role_name": True,
                "squeeze": False,
                "dims_as_attrs": ["<level_per_type>"],
                "variable_attrs": ["parameter.units"],
                "global_attrs": ["metadata.gridType"],
                "add_earthkit_attrs": False,
            },
            {
                "member": [0],
                "forecast_reference_time": [
                    pd.Timestamp("2024-06-03 00:00:00"),
                    pd.Timestamp("2024-06-03 12:00:00"),
                    pd.Timestamp("2024-06-04 00:00:00"),
                    pd.Timestamp("2024-06-04 12:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "isobaricInhPa": [300, 400, 500, 700, 850, 1000],
            },
            {"member": 1, "forecast_reference_time": 4, "step": 2, "isobaricInhPa": 6},
            {
                "2t": {"units": "kelvin", "surface": 0},
                "msl": {"units": "pascal", "surface": 0},
                "r": {"units": "percent"},
                "t": {"units": "kelvin"},
                "u": {"units": "meter / second"},
                "v": {"units": "meter / second"},
                "z": {"units": "meter ** 2 / second ** 2"},
            },
            {"gridType": "regular_ll"},
        ),
        (
            "level/pl_sfc.grib1",
            {
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 0,
                "metadata.step": 0,
                "metadata.level": [0, 850],
            },
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "level_dim_mode": "level_per_type",
                "dim_name_from_role_name": True,
                "squeeze": True,
                "dims_as_attrs": ["<level_per_type>"],
                "variable_attrs": [],
                "global_attrs": [],
                "rename_attrs": {"isobaricInhPa": "pl"},
                "add_earthkit_attrs": False,
            },
            {},
            {},
            {
                "2t": {"surface": 0},
                "msl": {"surface": 0},
                "r": {"pl": 850},
                "t": {"pl": 850},
                "u": {"pl": 850},
                "v": {"pl": 850},
                "z": {"pl": 850},
            },
            {},
        ),
        (
            "level/pl_sfc.grib1",
            {
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 0,
                "metadata.step": 0,
                "metadata.level": [0, 850],
            },
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "level_dim_mode": "level_per_type",
                "dim_name_from_role_name": True,
                "squeeze": True,
                "ensure_dims": ["<level_per_type>"],
                "dims_as_attrs": ["<level_per_type>"],
                "variable_attrs": [],
                "global_attrs": [],
                "rename_dims": {"surface": "SURFACE"},
                "rename_attrs": {"isobaricInhPa": "pl"},
                "add_earthkit_attrs": False,
            },
            {
                "SURFACE": [0],
                "isobaricInhPa": [850],
            },
            {"SURFACE": 1, "isobaricInhPa": 1},
            {
                "2t": {"surface": 0},
                "msl": {"surface": 0},
                "r": {"pl": 850},
                "t": {"pl": 850},
                "u": {"pl": 850},
                "v": {"pl": 850},
                "z": {"pl": 850},
            },
            {},
        ),
    ],
)
def test_xr_engine_level_per_type_dim(lazy_load, path, sel, kwargs, coords, dims, var_attrs, global_attrs):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", path))
    if sel:
        ds0 = ds0.sel(**sel)
    ds = ds0.to_xarray(lazy_load=lazy_load, **kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    for v in var_attrs:
        v_attrs = dict(ds[v].attrs)
        v_attrs.pop("_earthkit", None)
        v_attrs.pop("ek_grid_spec", None)
        assert v_attrs == var_attrs[v], f"Variable {v} attributes do not match expected values"
    assert ds.attrs == global_attrs


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "path,sel,idx,kwargs,coords,dims,var_attrs,global_attrs",
    [
        (
            "level/pl_small.grib",
            {
                "metadata.shortName": ["t", "r"],
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 1200,
                "metadata.step": 0,
                "metadata.level": [500, 700],
            },
            [0, 3],  # gets t @ 700hPa and r @ 500hPa
            {
                "profile": "grib",
                "ensure_dims": ["metadata.expver"],
                "dims_as_attrs": ["level"],
                "add_earthkit_attrs": False,
            },
            {
                "expver": ["0001"],
            },
            {"expver": 1},
            {
                "r": {
                    "standard_name": "relative_humidity",
                    "long_name": "Relative humidity",
                    "units": "percent",
                    "typeOfLevel": "isobaricInhPa",
                    "level": 500,
                },
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "kelvin",
                    "typeOfLevel": "isobaricInhPa",
                    "level": 700,
                },
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
        (
            "level/pl_small.grib",
            {
                "metadata.shortName": ["t", "r"],
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 1200,
                "metadata.step": 0,
                "metadata.level": [500, 700],
            },
            [0, 3],  # gets t @ 700hPa and r @ 500hPa
            {
                "profile": "grib",
                "remapping": {"my_level": "{metadata.level}__{metadata.typeOfLevel}"},
                "extra_dims": ["my_level"],
                "ensure_dims": ["metadata.expver"],
                "dims_as_attrs": ["my_level"],
                "add_earthkit_attrs": False,
            },
            {
                "expver": ["0001"],
            },
            {"expver": 1},
            {
                "r": {
                    "standard_name": "relative_humidity",
                    "long_name": "Relative humidity",
                    "units": "percent",
                    "typeOfLevel": "isobaricInhPa",
                    "my_level": "500__isobaricInhPa",
                },
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "kelvin",
                    "typeOfLevel": "isobaricInhPa",
                    "my_level": "700__isobaricInhPa",
                },
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
    ],
)
def test_xr_engine_dims_as_attrs_1(
    allow_holes, lazy_load, path, sel, idx, kwargs, coords, dims, var_attrs, global_attrs
):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", path))
    if sel:
        ds0 = ds0.sel(**sel)
    if idx:
        ds0 = ds0[idx]
    ds = ds0.to_xarray(lazy_load=lazy_load, allow_holes=allow_holes, **kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    for v in var_attrs:
        v_attrs = dict(ds[v].attrs)
        v_attrs.pop("_earthkit", None)
        v_attrs.pop("ek_grid_spec", None)
        assert v_attrs == var_attrs[v]
    assert ds.attrs == global_attrs


@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "path,sel,idx,kwargs,coords,dims,var_attrs,global_attrs",
    [
        (
            "level/aifs-sfc.grib",
            None,
            None,
            {
                "profile": None,
                "level_dim_mode": "level",
                "dims_as_attrs": ["level", "level_type"],
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [
                    pd.Timestamp("2025-12-12 00:00:00"),
                    pd.Timestamp("2025-12-12 06:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
            },
            {"forecast_reference_time": 2, "step": 2},
            {
                "10u": {"level": 10, "level_type": "height_above_ground_level"},
                "2t": {"level": 2, "level_type": "height_above_ground_level"},
                "msl": {"level": 0, "level_type": "mean_sea"},
                "tcw": {"level": 0, "level_type": "entire_atmosphere"},
                "tp": {"level": 0, "level_type": "surface"},
            },
            {},
        ),
        (
            "level/aifs-pl_sfc.grib",
            None,
            None,
            {
                "profile": None,
                "level_dim_mode": "level",
                "dims_as_attrs": ["level", "level_type"],
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [
                    pd.Timestamp("2025-12-12 00:00:00"),
                    pd.Timestamp("2025-12-12 06:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "level": [500, 850, 1000],
            },
            {"forecast_reference_time": 2, "step": 2, "level": 3},
            {
                "10u": {"level": 10, "level_type": "height_above_ground_level"},
                "2t": {"level": 2, "level_type": "height_above_ground_level"},
                "msl": {"level": 0, "level_type": "mean_sea"},
                "tcw": {"level": 0, "level_type": "entire_atmosphere"},
                "tp": {"level": 0, "level_type": "surface"},
                "z": {"level_type": "pressure"},
            },
            {},
        ),
        (
            "level/aifs-sfc.grib",
            None,
            None,
            {
                "profile": None,
                "level_dim_mode": "level_and_type",
                "dims_as_attrs": ["level_and_type"],
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [
                    pd.Timestamp("2025-12-12 00:00:00"),
                    pd.Timestamp("2025-12-12 06:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
            },
            {"forecast_reference_time": 2, "step": 2},
            {
                "10u": {"level_and_type": "10height_above_ground_level"},
                "2t": {"level_and_type": "2height_above_ground_level"},
                "msl": {"level_and_type": "0mean_sea"},
                "tcw": {"level_and_type": "0entire_atmosphere"},
                "tp": {"level_and_type": "0surface"},
            },
            {},
        ),
        (
            "level/aifs-pl_sfc.grib",
            None,
            None,
            {
                "profile": None,
                "level_dim_mode": "level_and_type",
                "dims_as_attrs": ["level_and_type"],
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [
                    pd.Timestamp("2025-12-12 00:00:00"),
                    pd.Timestamp("2025-12-12 06:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "level_and_type": ["1000pressure", "500pressure", "850pressure"],
            },
            {"forecast_reference_time": 2, "step": 2, "level_and_type": 3},
            {
                "10u": {"level_and_type": "10height_above_ground_level"},
                "2t": {"level_and_type": "2height_above_ground_level"},
                "msl": {"level_and_type": "0mean_sea"},
                "tcw": {"level_and_type": "0entire_atmosphere"},
                "tp": {"level_and_type": "0surface"},
                "z": {},
            },
            {},
        ),
        (
            "level/aifs-sfc.grib",
            None,
            None,
            {
                "profile": None,
                "level_dim_mode": "level_per_type",
                "dims_as_attrs": ["<level_per_type>"],
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [
                    pd.Timestamp("2025-12-12 00:00:00"),
                    pd.Timestamp("2025-12-12 06:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
            },
            {"forecast_reference_time": 2, "step": 2},
            {
                "10u": {"height_above_ground_level": 10},
                "2t": {"height_above_ground_level": 2},
                "msl": {"mean_sea": 0},
                "tcw": {"entire_atmosphere": 0},
                "tp": {"surface": 0},
            },
            {},
        ),
        (
            "level/aifs-pl_sfc.grib",
            None,
            None,
            {
                "profile": None,
                "level_dim_mode": "level_per_type",
                "dims_as_attrs": ["<level_per_type>"],
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [
                    pd.Timestamp("2025-12-12 00:00:00"),
                    pd.Timestamp("2025-12-12 06:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "pressure": [500, 850, 1000],
            },
            {"forecast_reference_time": 2, "step": 2, "pressure": 3},
            {
                "10u": {"height_above_ground_level": 10},
                "2t": {"height_above_ground_level": 2},
                "msl": {"mean_sea": 0},
                "tcw": {"entire_atmosphere": 0},
                "tp": {"surface": 0},
                "z": {},
            },
            {},
        ),
    ],
)
def test_xr_engine_dims_as_attrs2(lazy_load, path, sel, idx, kwargs, coords, dims, var_attrs, global_attrs):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", path))
    if sel:
        ds0 = ds0.sel(**sel)
    if idx:
        ds0 = ds0[idx]
    ds = ds0.to_xarray(lazy_load=lazy_load, **kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    for v in var_attrs:
        v_attrs = dict(ds[v].attrs)
        v_attrs.pop("_earthkit", None)
        v_attrs.pop("ek_grid_spec", None)
        assert v_attrs == var_attrs[v]
    assert ds.attrs == global_attrs
