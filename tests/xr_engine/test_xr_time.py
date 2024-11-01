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
from xr_engine_fixtures import compare_dims  # noqa: E402


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dims",
    [
        (
            {"time_dim_mode": "raw", "decode_times": False, "decode_timedelta": False},
            {"date": [20240603, 20240604], "time": [0, 1200], "step": [0, 6]},
        ),
        (
            {"time_dim_mode": "raw"},
            {
                "date": [np.datetime64("2024-06-03", "ns"), np.datetime64("2024-06-04", "ns")],
                "time": [np.timedelta64(0, "s"), np.timedelta64(43200, "s")],
                "step": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
            },
        ),
        (
            {"time_dim_mode": "forecast", "decode_times": False, "decode_timedelta": False},
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
            {"time_dim_mode": "valid_time", "decode_times": False, "decode_timedelta": False},
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
            {"time_dim_mode": "valid_time", "decode_times": True, "decode_timedelta": True},
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
def test_xr_time_basic(kwargs, dims):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl.grib"))

    ds = ds_ek.to_xarray(**kwargs)
    compare_dims(ds, dims, order_ref_var="t")


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dims",
    [
        (
            {
                "dim_roles": {"date": "indexingDate", "time": "indexingTime", "step": "forecastMonth"},
                "decode_times": False,
                "decode_timedelta": False,
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
                "decode_times": False,
                "decode_timedelta": False,
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
def test_xr_time_seasonal_monthly_indexing_date(kwargs, dims):
    ds_ek = from_source(
        "url",
        earthkit_remote_test_data_file("test-data/xr_engine/date/jma_seasonal_fc_ref_time_per_member.grib"),
    )

    ds = ds_ek.to_xarray(**kwargs)
    compare_dims(ds, dims, order_ref_var="2t")


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dims",
    [
        (
            {
                "time_dim_mode": "forecast",
                "dim_roles": {"step": "forecastMonth"},
                "decode_times": False,
                "decode_timedelta": False,
            },
            {
                "number": [0, 1, 2],
                "forecast_reference_time": [
                    np.datetime64("1993-10-01", "ns"),
                    np.datetime64("1994-10-01", "ns"),
                    np.datetime64("1995-10-01", "ns"),
                    np.datetime64("1996-10-01", "ns"),
                ],
                "forecastMonth": [1, 2, 3, 4, 5, 6],
            },
        ),
        (
            {
                "time_dim_mode": "forecast",
                "dim_roles": {"step": "fcmonth"},
                "decode_times": False,
                "decode_timedelta": False,
            },
            {
                "number": [0, 1, 2],
                "forecast_reference_time": [
                    np.datetime64("1993-10-01", "ns"),
                    np.datetime64("1994-10-01", "ns"),
                    np.datetime64("1995-10-01", "ns"),
                    np.datetime64("1996-10-01", "ns"),
                ],
                "fcmonth": [1, 2, 3, 4, 5, 6],
            },
        ),
        (
            {
                "time_dim_mode": "raw",
                "dim_roles": {"step": "forecastMonth"},
                "decode_times": False,
                "decode_timedelta": False,
                "ensure_dims": ["number", "date", "time", "forecastMonth"],
            },
            {
                "number": [0, 1, 2],
                "date": [
                    np.datetime64("1993-10-01", "ns"),
                    np.datetime64("1994-10-01", "ns"),
                    np.datetime64("1995-10-01", "ns"),
                    np.datetime64("1996-10-01", "ns"),
                ],
                "time": [np.timedelta64(0, "s")],
                "forecastMonth": [1, 2, 3, 4, 5, 6],
            },
        ),
    ],
)
def test_xr_time_seasonal_monthly_simple(kwargs, dims):
    ds_ek = from_source(
        "url",
        earthkit_remote_test_data_file("test-data/xr_engine/date/seasonal_monthly.grib"),
    )

    ds = ds_ek.to_xarray(**kwargs)
    compare_dims(ds, dims, order_ref_var="2t")


@pytest.mark.cache
def test_xr_valid_time_coord():
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl_small.grib")).sel(
        date=20240603, time=[0, 1200]
    )

    ds = ds_ek.to_xarray(
        time_dim_mode="forecast", add_valid_time_coord=True, decode_times=False, decode_timedelta=False
    )

    dims = {
        "forecast_reference_time": [
            np.datetime64("2024-06-03T00", "ns"),
            np.datetime64("2024-06-03T12", "ns"),
        ],
        "step": [0, 6],
    }
    compare_dims(ds, dims, order_ref_var="t")

    vt = ds.coords["valid_time"]
    assert vt.dims == ("forecast_reference_time", "step")

    ref = [
        [np.datetime64("2024-06-03T00", "ns"), np.datetime64("2024-06-03T06", "ns")],
        [np.datetime64("2024-06-03T12", "ns"), np.datetime64("2024-06-03T18", "ns")],
    ]

    compare_coords(ds, {"valid_time": ref})
