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
    "kwargs,dims,step_units",
    [
        (
            {
                "time_dim_mode": "raw",
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": True,
            },
            {"date": [20240603, 20240604], "time": [0, 1200], "step": [0, 6]},
            ("step", "hours"),
        ),
        (
            {
                "time_dim_mode": "raw",
                "dim_name_from_role_name": True,
            },
            {
                "date": [np.datetime64("2024-06-03", "ns"), np.datetime64("2024-06-04", "ns")],
                "time": [np.timedelta64(0, "s"), np.timedelta64(43200, "s")],
                "step": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
            },
            None,
        ),
        (
            {
                "time_dim_mode": "forecast",
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": True,
            },
            {
                "forecast_reference_time": [
                    np.datetime64("2024-06-03T00", "ns"),
                    np.datetime64("2024-06-03T12", "ns"),
                    np.datetime64("2024-06-04T00", "ns"),
                    np.datetime64("2024-06-04T12", "ns"),
                ],
                "step": [0, 6],
            },
            ("step", "hours"),
        ),
        (
            {
                "time_dim_mode": "forecast",
                "dim_name_from_role_name": True,
            },
            {
                "forecast_reference_time": [
                    np.datetime64("2024-06-03T00", "ns"),
                    np.datetime64("2024-06-03T12", "ns"),
                    np.datetime64("2024-06-04T00", "ns"),
                    np.datetime64("2024-06-04T12", "ns"),
                ],
                "step": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
            },
            None,
        ),
        (
            {
                "time_dim_mode": "valid_time",
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": True,
            },
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
            None,
        ),
        (
            {
                "time_dim_mode": "valid_time",
                "decode_times": True,
                "decode_timedelta": True,
                "dim_name_from_role_name": True,
            },
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
            None,
        ),
        (
            {
                "time_dim_mode": "raw",
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": False,
            },
            {"date": [20240603, 20240604], "time": [0, 1200], "step_timedelta": [0, 6]},
            ("step_timedelta", "hours"),
        ),
        (
            {
                "time_dim_mode": "raw",
                "dim_name_from_role_name": False,
            },
            {
                "date": [np.datetime64("2024-06-03", "ns"), np.datetime64("2024-06-04", "ns")],
                "time": [np.timedelta64(0, "s"), np.timedelta64(43200, "s")],
                "step_timedelta": [np.timedelta64(0, "h"), np.timedelta64(6, "h")],
            },
            None,
        ),
    ],
)
def test_xr_time_basic(kwargs, dims, step_units):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl.grib"))

    ds = ds_ek.to_xarray(**kwargs)
    compare_dims(ds, dims, order_ref_var="t")

    if step_units is not None:
        assert (
            ds[step_units[0]].attrs["units"] == step_units[1]
        ), f"step units mismatch {ds[step_units[0]].attrs['units']} != {step_units[1]}"


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dims,step_units",
    [
        (
            {
                "dim_roles": {"date": "indexingDate", "time": "indexingTime", "step": "forecastMonth"},
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": False,
            },
            {
                "indexing_time": [
                    np.datetime64("2014-09-01", "ns"),
                    np.datetime64("2014-10-01", "ns"),
                ],
                "forecastMonth": [1, 2, 3],
            },
            ("forecastMonth", "months"),
        ),
        (
            {
                "dim_roles": {"forecast_reference_time": "indexing_time", "step": "forecastMonth"},
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": False,
            },
            {
                "indexing_time": [
                    np.datetime64("2014-09-01", "ns"),
                    np.datetime64("2014-10-01", "ns"),
                ],
                "forecastMonth": [1, 2, 3],
            },
            ("forecastMonth", "months"),
        ),
        (
            {
                "dim_roles": {"date": "indexingDate", "time": "indexingTime", "step": "forecastMonth"},
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": True,
            },
            {
                "forecast_reference_time": [
                    np.datetime64("2014-09-01", "ns"),
                    np.datetime64("2014-10-01", "ns"),
                ],
                "step": [1, 2, 3],
            },
            ("step", "months"),
        ),
        (
            {
                "dim_roles": {"forecast_reference_time": "indexing_time", "step": "forecastMonth"},
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": True,
            },
            {
                "forecast_reference_time": [
                    np.datetime64("2014-09-01", "ns"),
                    np.datetime64("2014-10-01", "ns"),
                ],
                "step": [1, 2, 3],
            },
            ("step", "months"),
        ),
    ],
)
def test_xr_time_seasonal_monthly_indexing_date(kwargs, dims, step_units):
    ds_ek = from_source(
        "url",
        earthkit_remote_test_data_file("test-data/xr_engine/date/jma_seasonal_fc_ref_time_per_member.grib"),
    )

    ds = ds_ek.to_xarray(**kwargs)
    compare_dims(ds, dims, order_ref_var="2t")

    if step_units is not None:
        assert (
            ds[step_units[0]].attrs["units"] == step_units[1]
        ), f"step units mismatch {ds[step_units[0]].attrs['units']} != {step_units[1]}"


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dims,step_units",
    [
        (
            {
                "time_dim_mode": "forecast",
                "dim_roles": {"step": "forecastMonth"},
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": False,
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
            ("forecastMonth", "months"),
        ),
        (
            {
                "time_dim_mode": "forecast",
                "dim_roles": {"step": "fcmonth"},
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": False,
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
            ("fcmonth", "months"),
        ),
        (
            {
                "time_dim_mode": "raw",
                "dim_roles": {"step": "forecastMonth"},
                "decode_times": False,
                "decode_timedelta": False,
                "ensure_dims": ["number", "date", "time", "forecastMonth"],
                "dim_name_from_role_name": False,
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
            ("forecastMonth", "months"),
        ),
        (
            {
                "time_dim_mode": "forecast",
                "dim_roles": {"step": "forecastMonth"},
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": True,
            },
            {
                "number": [0, 1, 2],
                "forecast_reference_time": [
                    np.datetime64("1993-10-01", "ns"),
                    np.datetime64("1994-10-01", "ns"),
                    np.datetime64("1995-10-01", "ns"),
                    np.datetime64("1996-10-01", "ns"),
                ],
                "step": [1, 2, 3, 4, 5, 6],
            },
            ("step", "months"),
        ),
        (
            {
                "time_dim_mode": "forecast",
                "dim_roles": {"step": "fcmonth"},
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": True,
            },
            {
                "number": [0, 1, 2],
                "forecast_reference_time": [
                    np.datetime64("1993-10-01", "ns"),
                    np.datetime64("1994-10-01", "ns"),
                    np.datetime64("1995-10-01", "ns"),
                    np.datetime64("1996-10-01", "ns"),
                ],
                "step": [1, 2, 3, 4, 5, 6],
            },
            ("step", "months"),
        ),
        (
            {
                "time_dim_mode": "raw",
                "dim_roles": {"step": "forecastMonth"},
                "decode_times": False,
                "decode_timedelta": False,
                "ensure_dims": ["number", "date", "time", "step"],
                "dim_name_from_role_name": True,
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
                "step": [1, 2, 3, 4, 5, 6],
            },
            ("step", "months"),
        ),
    ],
)
def test_xr_time_seasonal_monthly_simple(kwargs, dims, step_units):
    ds_ek = from_source(
        "url",
        earthkit_remote_test_data_file("test-data/xr_engine/date/seasonal_monthly.grib"),
    )

    ds = ds_ek.to_xarray(**kwargs)
    compare_dims(ds, dims, order_ref_var="2t")

    if step_units is not None:
        assert (
            ds[step_units[0]].attrs["units"] == step_units[1]
        ), f"step units mismatch {ds[step_units[0]].attrs['units']} != {step_units[1]}"


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dims,step_units,coords",
    [
        (
            {
                "time_dim_mode": "forecast",
                "add_valid_time_coord": True,
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": True,
            },
            {
                "forecast_reference_time": [
                    np.datetime64("2024-06-03T00", "ns"),
                    np.datetime64("2024-06-03T12", "ns"),
                ],
                "step": [0, 6],
            },
            ("step", "hours"),
            {
                "valid_time": [
                    [np.datetime64("2024-06-03T00", "ns"), np.datetime64("2024-06-03T06", "ns")],
                    [np.datetime64("2024-06-03T12", "ns"), np.datetime64("2024-06-03T18", "ns")],
                ]
            },
        ),
        (
            {
                "fixed_dims": ["level", "forecast_reference_time", "step"],
                "add_valid_time_coord": True,
                "decode_times": False,
                "decode_timedelta": False,
            },
            {
                "forecast_reference_time": [
                    np.datetime64("2024-06-03T00", "ns"),
                    np.datetime64("2024-06-03T12", "ns"),
                ],
                "step": [0, 6],
            },
            ("step", "hours"),
            {
                "valid_time": [
                    [np.datetime64("2024-06-03T00", "ns"), np.datetime64("2024-06-03T06", "ns")],
                    [np.datetime64("2024-06-03T12", "ns"), np.datetime64("2024-06-03T18", "ns")],
                ]
            },
        ),
        (
            {
                "fixed_dims": ["level", "step", "forecast_reference_time"],
                "add_valid_time_coord": True,
                "decode_times": False,
                "decode_timedelta": False,
            },
            {
                "step": [0, 6],
                "forecast_reference_time": [
                    np.datetime64("2024-06-03T00", "ns"),
                    np.datetime64("2024-06-03T12", "ns"),
                ],
            },
            ("step", "hours"),
            {
                "valid_time": [
                    [np.datetime64("2024-06-03T00", "ns"), np.datetime64("2024-06-03T12", "ns")],
                    [np.datetime64("2024-06-03T06", "ns"), np.datetime64("2024-06-03T18", "ns")],
                ]
            },
        ),
        (
            {
                "time_dim_mode": "forecast",
                "add_valid_time_coord": True,
                "decode_times": False,
                "decode_timedelta": False,
                "dim_name_from_role_name": False,
            },
            {
                "forecast_reference_time": [
                    np.datetime64("2024-06-03T00", "ns"),
                    np.datetime64("2024-06-03T12", "ns"),
                ],
                "step_timedelta": [0, 6],
            },
            ("step_timedelta", "hours"),
            {
                "valid_time": [
                    [np.datetime64("2024-06-03T00", "ns"), np.datetime64("2024-06-03T06", "ns")],
                    [np.datetime64("2024-06-03T12", "ns"), np.datetime64("2024-06-03T18", "ns")],
                ]
            },
        ),
    ],
)
def test_xr_valid_time_coord(kwargs, dims, step_units, coords):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl_small.grib")).sel(
        date=20240603, time=[0, 1200]
    )

    ds = ds_ek.to_xarray(**kwargs)

    compare_dims(ds, dims, order_ref_var="t")

    vt = ds.coords["valid_time"]
    assert vt.dims == tuple(dims.keys())

    compare_coords(ds, coords)

    if step_units is not None:
        assert (
            ds[step_units[0]].attrs["units"] == step_units[1]
        ), f"step units mismatch {ds[step_units[0]].attrs['units']} != {step_units[1]}"


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dims,step_units",
    [
        (
            {
                "time_dim_mode": "raw",
                "dim_name_from_role_name": True,
                "ensure_dims": ["date", "time", "step"],
            },
            {
                "date": [np.datetime64("2011-12-15", "ns")],
                "time": [np.timedelta64(12, "h")],
                "step": [
                    np.timedelta64(12, "h"),
                    np.timedelta64(18, "h"),
                    np.timedelta64(24, "h"),
                    np.timedelta64(30, "h"),
                    np.timedelta64(36, "h"),
                ],
            },
            None,
        ),
    ],
)
def test_xr_time_step_range_1(kwargs, dims, step_units):
    ds_ek = from_source(
        "url", earthkit_remote_test_data_file("test-data/xr_engine/date/wgust_step_range.grib1")
    )

    ds = ds_ek.to_xarray(**kwargs)
    compare_dims(ds, dims, order_ref_var="10fg6")

    if step_units is not None:
        assert (
            ds[step_units[0]].attrs["units"] == step_units[1]
        ), f"step units mismatch {ds[step_units[0]].attrs['units']} != {step_units[1]}"


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dims,step_units",
    [
        (
            {
                "time_dim_mode": "raw",
                "dim_name_from_role_name": True,
                "ensure_dims": ["date", "time", "step"],
            },
            {
                "date": [np.datetime64("2025-05-27", "ns")],
                "time": [np.timedelta64(0, "ns")],
                "step": [np.timedelta64(72, "h"), np.timedelta64(73, "h")],
            },
            None,
        ),
    ],
)
def test_xr_time_step_range_2(kwargs, dims, step_units):
    ds_ek = from_source(
        "url", earthkit_remote_test_data_file("test-data/xr_engine/date/lsp_step_range.grib2")
    )

    ds = ds_ek.to_xarray(**kwargs)
    compare_dims(ds, dims, order_ref_var="lsp")

    if step_units is not None:
        assert (
            ds[step_units[0]].attrs["units"] == step_units[1]
        ), f"step units mismatch {ds[step_units[0]].attrs['units']} != {step_units[1]}"
