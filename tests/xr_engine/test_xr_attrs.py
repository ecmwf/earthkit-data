#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import os
import sys

import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import compare_coords  # noqa: E402
from xr_engine_fixtures import compare_dims  # noqa: E402


def _get_attrs(metadata):
    return {k: metadata.get(k, None) for k in ["gridType", "units"]}


def _get_attrs_for_key_1(key, metadata):
    return str(metadata.get("units", "")) + "_test1"


def _get_attrs_for_key_2(key, metadata):
    return metadata.get(key, "") + "_test2"


@pytest.mark.cache
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
                "step_timedelta": [datetime.timedelta(hours=0), datetime.timedelta(hours=6)],
                "levelist": [500, 700],
            },
            {"date": 2, "time": 2, "step_timedelta": 2, "levelist": 2},
            {},
        ),
        (
            {
                "profile": "mars",
                "dims_as_attrs": "levtype",
                "time_dim_mode": "raw",
                "decode_times": False,
                "decode_timedelta": False,
                "strict": True,
                "dim_name_from_role_name": False,
            },
            {
                "date": [20240603, 20240604],
                "time": [0, 1200],
                "step_timedelta": [datetime.timedelta(hours=0), datetime.timedelta(hours=6)],
                "levelist": [500, 700],
            },
            {"date": 2, "time": 2, "step_timedelta": 2, "levelist": 2},
            {"levtype": 2},
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
                "step_timedelta": [datetime.timedelta(hours=0), datetime.timedelta(hours=6)],
                "levelist": [500, 700],
            },
            {"date": 2, "time": 2, "step_timedelta": 2, "levelist": 2},
            {},
        ),
        (
            {
                "profile": "mars",
                "dims_as_attrs": "levtype",
                "time_dim_mode": "raw",
                "decode_times": False,
                "decode_timedelta": False,
                "strict": False,
                "dim_name_from_role_name": False,
            },
            {
                "date": [20240603, 20240604],
                "time": [0, 1200],
                "step_timedelta": [datetime.timedelta(hours=0), datetime.timedelta(hours=6)],
                "levelist": [500, 700],
            },
            {"date": 2, "time": 2, "step_timedelta": 2, "levelist": 2},
            {"levtype": 2},
        ),
    ],
)
def test_xr_dims_as_attrs(kwargs, coords, dims, attrs):
    ds0 = from_source(
        "url", earthkit_remote_test_data_file("test-data", "xr_engine", "level", "pl_small.grib")
    )

    ds = ds0.to_xarray(**kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    for k, v in attrs.items():
        ds["t"].attrs[k] == v


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,coords,dims,attrs",
    [
        (
            {
                "profile": "mars",
                "attrs_mode": "fixed",
                "variable_attrs": [
                    "shortName",
                    "key=levtype",
                    "namespace=parameter",
                    _get_attrs,
                    {
                        "edition": _get_attrs_for_key_1,
                        "typeOfLevel": _get_attrs_for_key_2,
                        "param": "test",
                        "mykey1": "key=levelist",
                        "mykey2": "namespace=vertical",
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
                "step_timedelta": [datetime.timedelta(hours=0), datetime.timedelta(hours=6)],
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
                "gridType": "regular_ll",
                "units": "K",
                "edition": "K_test1",
                "typeOfLevel": "isobaricInhPa_test2",
                "param": "test",
                "mykey1": 500,
                "mykey2": {"typeOfLevel": "isobaricInhPa", "level": 500},
            },
        ),
    ],
)
def test_xr_attrs_types(kwargs, coords, dims, attrs):
    ds0 = from_source(
        "url", earthkit_remote_test_data_file("test-data", "xr_engine", "level", "pl_small.grib")
    )

    ds = ds0.to_xarray(**kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    print(ds["t"].attrs)
    for k, v in attrs.items():
        assert ds["t"].attrs[k] == v, f"{k}"


@pytest.mark.cache
def test_xr_global_attrs():
    ds_fl = from_source(
        "url", earthkit_remote_test_data_file("test-data", "xr_engine", "level", "pl_small.grib")
    )
    ds = ds_fl.to_xarray(
        attrs_mode="fixed",
        global_attrs=[
            {"centre_fixed": "_ecmf_"},
            lambda md: {"centre_callable": md.get("centre")},
            "centre",
            "key=centreDescription",
            {"centre_key": "key=centre"},
            {"geography_namespace": "namespace=geography"},
        ],
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
