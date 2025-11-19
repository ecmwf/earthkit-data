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

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import compare_dims  # noqa: E402


@pytest.fixture
def xr_lod_latlon():
    prototype = {
        "latitudes": [10.0, 0.0, -10.0],
        "longitudes": [20, 40.0],
        "values": [1, 2, 3, 4, 5, 6],
        "valid_datetime": "2018-08-01T09:00:00",
    }

    d = [
        {"param": "t", "level": 500, **prototype},
        {"param": "t", "level": 850, **prototype},
        {"param": "u", "level": 500, **prototype},
        {"param": "u", "level": 850, **prototype},
    ]
    ds = from_source("list-of-dicts", d)
    return ds


@pytest.fixture
def xr_lod_nongeo():
    prototype = {
        "values": [1, 2, 3, 4, 5, 6],
        "valid_datetime": "2018-08-01T09:00:00Z",
    }

    d = [
        {"param": "t", "level": 500, **prototype},
        {"param": "t", "level": 850, **prototype},
        {"param": "u", "level": 500, **prototype},
        {"param": "u", "level": 850, **prototype},
    ]
    ds = from_source("list-of-dicts", d)
    return ds


@pytest.fixture
def xr_lod_forecast():
    prototype = {
        "latitudes": [10.0, 0.0, -10.0],
        "longitudes": [20, 40.0],
        "values": [1, 2, 3, 4, 5, 6],
        "base_datetime": "2018-08-01T09:00:00",
    }

    d = [
        {"param": "t", "level": 500, "step": 0, **prototype},
        {"param": "t", "level": 500, "step": 6, **prototype},
        {"param": "u", "level": 500, "step": 0, **prototype},
        {"param": "u", "level": 500, "step": 6, **prototype},
    ]
    ds = from_source("list-of-dicts", d)
    return ds


@pytest.fixture
def xr_lod_valid_time():
    prototype = {
        "latitudes": [10.0, 0.0, -10.0],
        "longitudes": [20, 40.0],
        "values": [1, 2, 3, 4, 5, 6],
    }

    d = [
        {
            "param": "t",
            "valid_datetime": "2018-08-01T09:00:00",
            **prototype,
        },
        {
            "param": "t",
            "valid_datetime": "2018-08-01T15:00:00",
            **prototype,
        },
        {"param": "u", "valid_datetime": "2018-08-01T09:00:00", **prototype},
        {
            "param": "u",
            "valid_datetime": "2018-08-01T15:00:00",
            **prototype,
        },
    ]
    ds = from_source("list-of-dicts", d)
    return ds


@pytest.fixture
def xr_lod_raw_time():
    prototype = {
        "latitudes": [10.0, 0.0, -10.0],
        "longitudes": [20, 40.0],
        "values": [1, 2, 3, 4, 5, 6],
    }

    d = [
        {
            "param": "t",
            "date": "20180801",
            "time": 900,
            "step": 0,
            **prototype,
        },
        {
            "param": "t",
            "date": "20180801",
            "time": 900,
            "step": 6,
            **prototype,
        },
        {
            "param": "u",
            "date": "20180801",
            "time": 900,
            "step": 0,
            **prototype,
        },
        {
            "param": "u",
            "date": "20180801",
            "time": 900,
            "step": 6,
            **prototype,
        },
    ]
    ds = from_source("list-of-dicts", d)
    return ds


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_lod_latlon(allow_holes, lazy_load, xr_lod_latlon):
    ds_in = xr_lod_latlon
    ds = ds_in.to_xarray(time_dim_mode="raw", allow_holes=allow_holes, lazy_load=lazy_load)

    assert ds is not None
    assert ds["t"].shape == (2, 3, 2)
    assert ds["u"].shape == (2, 3, 2)
    assert np.allclose(ds["latitude"].values, np.array([10.0, 0.0, -10.0]))
    assert np.allclose(ds["longitude"].values, np.array([20.0, 40.0]))


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_lod_nongeo(allow_holes, lazy_load, xr_lod_nongeo):
    ds_in = xr_lod_nongeo
    ds = ds_in.to_xarray(time_dim_mode="raw", allow_holes=allow_holes, lazy_load=lazy_load)

    assert ds is not None
    assert ds["t"].shape == (2, 6)
    assert ds["u"].shape == (2, 6)

    ref = np.array(
        [
            [1, 2, 3, 4, 5, 6],
            [1, 2, 3, 4, 5, 6],
        ]
    )
    assert np.allclose(ds["t"].values, ref)
    assert np.allclose(ds["u"].values, ref)


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_lod_forecast(allow_holes, lazy_load, xr_lod_forecast):
    ds_in = xr_lod_forecast
    ds = ds_in.to_xarray(time_dim_mode="forecast", allow_holes=allow_holes, lazy_load=lazy_load)

    assert ds is not None
    assert ds["t"].shape == (2, 3, 2)
    assert ds["u"].shape == (2, 3, 2)

    dims = {"step": [np.timedelta64(0, "h"), np.timedelta64(6, "h")]}
    compare_dims(ds, dims, order_ref_var="t")

    assert np.allclose(ds["latitude"].values, np.array([10.0, 0.0, -10.0]))
    assert np.allclose(ds["longitude"].values, np.array([20.0, 40.0]))


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_lod_valid_time_from_valid_datetime_single(allow_holes, lazy_load, xr_lod_latlon):
    ds_in = xr_lod_latlon
    ds = ds_in.to_xarray(
        time_dim_mode="valid_time", allow_holes=allow_holes, lazy_load=lazy_load, squeeze=False
    )

    dims = {
        "valid_time": [np.datetime64("2018-08-01T09:00:00", "ns")],
        "level": [500, 850],
    }

    assert ds is not None
    assert ds["t"].shape == (1, 2, 3, 2)
    assert ds["u"].shape == (1, 2, 3, 2)

    compare_dims(ds, dims, order_ref_var="t")


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_lod_valid_time_from_valid_datetime_multi(allow_holes, lazy_load, xr_lod_valid_time):
    ds_in = xr_lod_valid_time
    ds = ds_in.to_xarray(
        time_dim_mode="valid_time",
        allow_holes=allow_holes,
        lazy_load=lazy_load,
    )

    dims = {
        "valid_time": [
            np.datetime64("2018-08-01T09:00:00", "ns"),
            np.datetime64("2018-08-01T15:00:00", "ns"),
        ],
    }

    assert ds is not None
    assert ds["t"].shape == (2, 3, 2)
    assert ds["u"].shape == (2, 3, 2)

    compare_dims(ds, dims, order_ref_var="t")


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_lod_valid_time_from_forecast(allow_holes, lazy_load, xr_lod_forecast):
    ds_in = xr_lod_forecast
    ds = ds_in.to_xarray(
        time_dim_mode="valid_time", allow_holes=allow_holes, lazy_load=lazy_load, squeeze=False
    )

    assert ds is not None
    assert ds["t"].shape == (2, 1, 3, 2)
    assert ds["u"].shape == (2, 1, 3, 2)

    dims = {
        "valid_time": [
            np.datetime64("2018-08-01T09:00:00", "ns"),
            np.datetime64("2018-08-01T15:00:00", "ns"),
        ],
        "level": [500],
    }

    compare_dims(ds, dims, order_ref_var="t")


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_lod_valid_time_from_raw_time(allow_holes, lazy_load, xr_lod_raw_time):
    ds_in = xr_lod_raw_time
    ds = ds_in.to_xarray(
        time_dim_mode="valid_time",
        allow_holes=allow_holes,
        lazy_load=lazy_load,
    )

    dims = {
        "valid_time": [
            np.datetime64("2018-08-01T09:00:00", "ns"),
            np.datetime64("2018-08-01T15:00:00", "ns"),
        ],
    }

    assert ds is not None
    assert ds["t"].shape == (2, 3, 2)
    assert ds["u"].shape == (2, 3, 2)

    compare_dims(ds, dims, order_ref_var="t")
