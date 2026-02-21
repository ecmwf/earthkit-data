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

import numpy as np
import pandas as pd
import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import compare_coords  # noqa: E402
from xr_engine_fixtures import compare_dims  # noqa: E402


def _get_attrs(field):
    return {k: field.get(k) for k in ["metadata.gridType", "parameter.units"]}


def _get_attrs_for_key_1(key, field):
    return str(field.get("parameter.units", default="")) + "_test1"


def _get_attrs_for_key_2(key, field):
    return field.get(key, default="") + "_test2"


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "kwargs,coords,dims,attrs",
    [
        (
            {
                "profile": "mars",
                "dims_as_attrs": None,
                "time_dim_mode": "raw",
                "decode_times": False,
                "decode_timedelta": False,
                "strict": True,
                "dim_name_from_role_name": False,
            },
            {
                "date": [20240603, 20240604],
                "time": [0, 1200],
                "step_timedelta": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
                "levelist": [500, 700],
            },
            {"date": 2, "time": 2, "step_timedelta": 2, "levelist": 2},
            {},
        ),
        (
            {
                "profile": "mars",
                "dims_as_attrs": "metadata.levtype",
                "time_dim_mode": "raw",
                "decode_times": False,
                "decode_timedelta": False,
                "strict": True,
                "dim_name_from_role_name": False,
            },
            {
                "date": [20240603, 20240604],
                "time": [0, 1200],
                "step_timedelta": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
                "levelist": [500, 700],
            },
            {"date": 2, "time": 2, "step_timedelta": 2, "levelist": 2},
            {"levtype": "pl"},
        ),
        (
            {
                "profile": "mars",
                "dims_as_attrs": None,
                "time_dim_mode": "raw",
                "decode_times": False,
                "decode_timedelta": False,
                "strict": False,
                "dim_name_from_role_name": False,
            },
            {
                "date": [20240603, 20240604],
                "time": [0, 1200],
                "step_timedelta": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
                "levelist": [500, 700],
            },
            {"date": 2, "time": 2, "step_timedelta": 2, "levelist": 2},
            {},
        ),
        (
            {
                "profile": "mars",
                "dims_as_attrs": "metadata.levtype",
                "time_dim_mode": "raw",
                "decode_times": False,
                "decode_timedelta": False,
                "strict": False,
                "dim_name_from_role_name": False,
            },
            {
                "date": [20240603, 20240604],
                "time": [0, 1200],
                "step_timedelta": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
                "levelist": [500, 700],
            },
            {"date": 2, "time": 2, "step_timedelta": 2, "levelist": 2},
            {"levtype": "pl"},
        ),
    ],
)
def test_xr_dims_as_attrs(allow_holes, lazy_load, kwargs, coords, dims, attrs):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", "level", "pl_small.grib"))

    ds = ds0.to_xarray(allow_holes=allow_holes, lazy_load=lazy_load, **kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    for k, v in attrs.items():
        assert ds["t"].attrs[k] == v


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "idx,kwargs,coords,dims,var_attrs,global_attrs",
    [
        (
            [14, 15],
            {
                "profile": "grib",
                "time_dim_mode": "raw",
                "level_dim_mode": "level",
                "dim_name_from_role_name": True,
                "squeeze": False,
                "dims_as_attrs": ["number", "date"],
                "variable_attrs": ["metadata.typeOfLevel", "parameter.units"],
                "global_attrs": ["metadata.edition"],
                "attrs_mode": "fixed",
                "add_earthkit_attrs": False,
            },
            {
                "time": [pd.Timedelta("12h")],
                "step": [pd.Timedelta("6h")],
                "level": [500],
                "level_type": ["isobaricInhPa"],
            },
            {"time": 1, "step": 1, "level": 1, "level_type": 1},
            {
                "r": {"typeOfLevel": "isobaricInhPa", "units": "%", "number": 0, "date": 20240603},
                "t": {"typeOfLevel": "isobaricInhPa", "units": "K", "number": 0, "date": 20240603},
            },
            {"edition": 1},
        ),
        (
            [14],
            {
                "profile": "grib",
                "time_dim_mode": "raw",
                "level_dim_mode": "level",
                "dim_name_from_role_name": True,
                "squeeze": False,
                "dims_as_attrs": ["number", "date"],
                "variable_attrs": ["metadata.Nj"],
                "attrs": ["metadata.cfVarName", "parameter.units", "metadata.edition"],
                "global_attrs": ["metadata.gridType"],
                "attrs_mode": "unique",
                "add_earthkit_attrs": False,
            },
            {
                "time": [pd.Timedelta("12h")],
                "step": [pd.Timedelta("6h")],
                "level": [500],
                "level_type": ["isobaricInhPa"],
            },
            {"time": 1, "step": 1, "level": 1, "level_type": 1},
            {"t": {"units": "K", "Nj": 19, "number": 0, "date": 20240603}},
            {"cfVarName": "t", "edition": 1, "gridType": "regular_ll"},
        ),
        (
            [12, 14],
            {
                "profile": "grib",
                "time_dim_mode": "raw",
                "level_dim_mode": "level",
                "dim_name_from_role_name": True,
                "squeeze": False,
                "dims_as_attrs": ["number", "date"],
                "variable_attrs": ["metadata.Nj"],
                "attrs": ["metadata.cfVarName", "metadata.units", "metadata.edition"],
                "global_attrs": ["metadata.gridType"],
                "attrs_mode": "unique",
                "rename_attrs": {
                    "cfVarName": "cf_var_name",
                    "gridType": "grid_type",
                    "number": "realisation",
                    "date": "DATE",
                },
                "add_earthkit_attrs": False,
            },
            {
                "time": [pd.Timedelta("12h")],
                "step": [pd.Timedelta("6h")],
                "level": [500, 700],
                "level_type": ["isobaricInhPa"],
            },
            {"time": 1, "step": 1, "level": 2, "level_type": 1},
            {"t": {"units": "K", "Nj": 19, "realisation": 0, "DATE": 20240603}},
            {"cf_var_name": "t", "edition": 1, "grid_type": "regular_ll"},
        ),
        (
            [14],
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "level_dim_mode": "level_and_type",
                "dim_name_from_role_name": True,
                "squeeze": False,
                "dims_as_attrs": ["forecast_reference_time", "level_and_type"],
                "variable_attrs": ["metadata.units"],
                "global_attrs": ["geography.grid_type"],
                "add_earthkit_attrs": False,
            },
            {
                "number": [0],
                "step": [pd.Timedelta("6h")],
            },
            {"number": 1, "step": 1},
            {
                "t": {
                    "units": "K",
                    "forecast_reference_time": "2024-06-03T12:00:00",
                    "level_and_type": "500isobaricInhPa",
                }
            },
            {"grid_type": "regular_ll"},
        ),
    ],
)
def test_xr_dims_as_attrs_2(allow_holes, lazy_load, idx, kwargs, coords, dims, var_attrs, global_attrs):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", "level", "pl_small.grib"))

    ds = ds0[idx].to_xarray(allow_holes=allow_holes, lazy_load=lazy_load, **kwargs)
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
    "allow_holes,idx,kwargs,coords,dims,var_attrs,global_attrs",
    [
        (
            True,
            [12, 14, 15],
            {
                "profile": "grib",
                "time_dim_mode": "raw",
                "level_dim_mode": "level",
                "dim_name_from_role_name": True,
                "squeeze": False,
                "dims_as_attrs": ["number", "date", "level", "level_type"],
                "variable_attrs": ["metadata.Nj"],
                "attrs": ["metadata.cfVarName", "parameter.units", "metadata.edition"],
                "global_attrs": ["metadata.gridType"],
                "attrs_mode": "unique",
                "rename_attrs": {
                    "cfVarName": "cf_var_name",
                    "gridType": "grid_type",
                    "number": "realisation",
                    "date": "DATE",
                },
                "add_earthkit_attrs": False,
            },
            {
                "time": [pd.Timedelta("12h")],
                "step": [pd.Timedelta("6h")],
                "level": [500, 700],
            },
            {"time": 1, "step": 1},
            {
                "r": {
                    "cf_var_name": "r",
                    "units": "%",
                    "Nj": 19,
                    "realisation": 0,
                    "DATE": 20240603,
                    "level": 500,
                    "level_type": "isobaricInhPa",
                },
                "t": {
                    "cf_var_name": "t",
                    "units": "K",
                    "Nj": 19,
                    "realisation": 0,
                    "DATE": 20240603,
                    "level_type": "isobaricInhPa",
                },
            },
            {"edition": 1, "grid_type": "regular_ll"},
        ),
        (
            False,
            slice(0, 16, 4),
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "level_dim_mode": "level_per_type",
                "dim_name_from_role_name": True,
                "squeeze": False,
                "dims_as_attrs": ["forecast_reference_time", "<level_per_type>"],
                "variable_attrs": ["parameter.units"],
                "global_attrs": ["geography.grid_type"],
                "add_earthkit_attrs": False,
                "rename_attrs": {"isobaricInhPa": "pl"},
            },
            {
                "number": [0],
                "forecast_reference_time": [
                    pd.Timestamp("2024-06-03 00:00:00"),
                    pd.Timestamp("2024-06-03 12:00:00"),
                ],
                "step": [pd.Timedelta("0h"), pd.Timedelta("6h")],
            },
            {"number": 1, "forecast_reference_time": 2, "step": 2},
            {"t": {"units": "K", "pl": 700}},
            {"grid_type": "regular_ll"},
        ),
    ],
)
def test_xr_dims_as_attrs_3(lazy_load, allow_holes, idx, kwargs, coords, dims, var_attrs, global_attrs):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", "level", "pl_small.grib"))

    ds = ds0[idx].to_xarray(lazy_load=lazy_load, allow_holes=allow_holes, **kwargs)
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
    "kwargs,coords,dims,attrs",
    [
        (
            {
                "profile": "mars",
                "attrs_mode": "fixed",
                "variable_attrs": [
                    "metadata.shortName",
                    "key=metadata.levtype",
                    "namespace=metadata.parameter",
                    _get_attrs,
                    {
                        "edition": _get_attrs_for_key_1,
                        "metadata.typeOfLevel": _get_attrs_for_key_2,
                        "param": "test",
                        "mykey1": "key=metadata.levelist",
                        "mykey2": "namespace=metadata.vertical",
                    },
                ],
                "time_dim_mode": "raw",
                "decode_times": False,
                "decode_timedelta": False,
                "strict": False,
                "dim_name_from_role_name": False,
            },
            {
                "date": [20240603, 20240604],
                "time": [0, 1200],
                "step_timedelta": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
                "levelist": [500, 700],
            },
            {"date": 2, "time": 2, "step_timedelta": 2, "levelist": 2},
            {
                "shortName": "t",
                "levtype": "pl",
                "parameter": {
                    "centre": "ecmf",
                    "paramId": 130,
                    "units": "K",
                    "name": "Temperature",
                    "shortName": "t",
                },
                "metadata.gridType": "regular_ll",
                "parameter.units": "K",
                "edition": "K_test1",
                "metadata.typeOfLevel": "isobaricInhPa_test2",
                "param": "test",
                "mykey1": 500,
                "mykey2": {"typeOfLevel": "isobaricInhPa", "level": 500},
            },
        ),
    ],
)
def test_xr_attrs_types(lazy_load, kwargs, coords, dims, attrs):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", "level", "pl_small.grib"))

    ds = ds0.to_xarray(lazy_load=lazy_load, **kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    for k, v in attrs.items():
        if k not in ["_earthkit", "ek_grid_spec"]:
            assert ds["t"].attrs[k] == v, f"{k}"


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_global_attrs(allow_holes, lazy_load):
    ds_fl = from_source("url", earthkit_remote_test_data_file("xr_engine", "level", "pl_small.grib"))
    ds = ds_fl.to_xarray(
        attrs_mode="fixed",
        global_attrs=[
            {"centre_fixed": "_ecmf_"},
            lambda field: {"centre_callable": field.get("metadata.centre")},
            "metadata.centre",
            "key=metadata.centreDescription",
            {"centre_key": "key=metadata.centre"},
            {"geography_namespace": "namespace=metadata.geography"},
        ],
        allow_holes=allow_holes,
        lazy_load=lazy_load,
    )
    ref_global_attrs = {
        "centre_callable": "ecmf",
        "centre": "ecmf",
        "centreDescription": "European Centre for Medium-Range Weather Forecasts",
        "centre_key": "ecmf",
        "geography_namespace": {
            "Ni": 36,
            "Nj": 19,
            "latitudeOfFirstGridPointInDegrees": 90.0,
            "longitudeOfFirstGridPointInDegrees": 0.0,
            "latitudeOfLastGridPointInDegrees": -90.0,
            "longitudeOfLastGridPointInDegrees": 350.0,
            "iScansNegatively": 0,
            "jScansPositively": 0,
            "jPointsAreConsecutive": 0,
            "jDirectionIncrementInDegrees": 10.0,
            "iDirectionIncrementInDegrees": 10.0,
            "gridType": "regular_ll",
        },
        "centre_fixed": "_ecmf_",
    }
    assert ds.attrs == ref_global_attrs
