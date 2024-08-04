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
import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import compare_coords  # noqa: E402


@pytest.mark.parametrize(
    "kwargs,dims",
    [
        (
            {"time_dim_mode": "raw", "decode_time": False},
            {"date": [20240603, 20240604], "time": [0, 1200], "step": [0, 6]},
        ),
        (
            {"time_dim_mode": "raw"},
            {
                "date": [np.datetime64("2024-06-03", "ns"), np.datetime64("2024-06-04", "ns")],
                "time": [0, 1200],
                "step": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
            },
        ),
        (
            {"time_dim_mode": "forecast", "decode_time": False},
            {
                "forecast_reference_time": [
                    np.datetime64("2024-06-03T00", "ns"),
                    np.datetime64("2024-06-03T12", "ns"),
                    np.datetime64("2024-06-04T00", "ns"),
                    np.datetime64("2024-06-04T12", "ns"),
                ],
                "step": [0, 6],
            },
        ),
        (
            {"time_dim_mode": "forecast"},
            {
                "forecast_reference_time": [
                    np.datetime64("2024-06-03T00", "ns"),
                    np.datetime64("2024-06-03T12", "ns"),
                    np.datetime64("2024-06-04T00", "ns"),
                    np.datetime64("2024-06-04T12", "ns"),
                ],
                "step": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
            },
        ),
        (
            {"time_dim_mode": "valid_time", "decode_time": False},
            {
                "valid_time": [
                    np.datetime64("2024-06-03T00", "ns"),
                    np.datetime64("2024-06-03T06", "ns"),
                    np.datetime64("2024-06-03T12", "ns"),
                    np.datetime64("2024-06-03T18", "ns"),
                    np.datetime64("2024-06-04T00", "ns"),
                    np.datetime64("2024-06-04T06", "ns"),
                    np.datetime64("2024-06-04T12", "ns"),
                    np.datetime64("2024-06-04T18", "ns"),
                ],
            },
        ),
        (
            {"time_dim_mode": "valid_time", "decode_time": True},
            {
                "valid_time": [
                    np.datetime64("2024-06-03T00", "ns"),
                    np.datetime64("2024-06-03T06", "ns"),
                    np.datetime64("2024-06-03T12", "ns"),
                    np.datetime64("2024-06-03T18", "ns"),
                    np.datetime64("2024-06-04T00", "ns"),
                    np.datetime64("2024-06-04T06", "ns"),
                    np.datetime64("2024-06-04T12", "ns"),
                    np.datetime64("2024-06-04T18", "ns"),
                ],
            },
        ),
    ],
)
def test_xr_time(kwargs, dims):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl_regular_ll.grib"))

    ds = ds_ek.to_xarray(**kwargs)

    dim_order = []
    for d in ds["t"].dims:
        if d in dims:
            dim_order.append(d)
    assert dim_order == list(dims.keys())

    compare_coords(ds, dims)


@pytest.mark.parametrize(
    "kwargs,dims",
    [
        (
            {
                "dim_roles": {"date": "indexingDate", "time": "indexingTime", "step": "forecastMonth"},
                "decode_time": False,
            },
            {
                "indexing_time": [
                    np.datetime64("2014-09-01", "ns"),
                    np.datetime64("2014-10-01", "ns"),
                ],
                "forecastMonth": [1, 2, 3],
            },
        ),
        (
            {
                "dim_roles": {"forecast_reference_time": "indexing_time", "step": "forecastMonth"},
                "decode_time": False,
            },
            {
                "indexing_time": [
                    np.datetime64("2014-09-01", "ns"),
                    np.datetime64("2014-10-01", "ns"),
                ],
                "forecastMonth": [1, 2, 3],
            },
        ),
    ],
)
def test_xr_time_seasonal(kwargs, dims):
    ds_ek = from_source(
        "url",
        earthkit_remote_test_data_file("test-data/xr_engine/date/jma_seasonal_fc_ref_time_per_member.grib"),
    )

    ds = ds_ek.to_xarray(**kwargs)

    dim_order = []
    for d in ds["2t"].dims:
        if d in dims:
            dim_order.append(d)
    assert dim_order == list(dims.keys())

    compare_coords(ds, dims)
