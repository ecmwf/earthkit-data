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
        "base_datetime": "2018-08-01T09:00:00Z",
    }

    d = [
        {"param": "t", "level": 500, "step": 0, **prototype},
        {"param": "t", "level": 500, "step": 6, **prototype},
        {"param": "u", "level": 500, "step": 0, **prototype},
        {"param": "u", "level": 500, "step": 6, **prototype},
    ]
    ds = from_source("list-of-dicts", d)
    return ds


def test_xr_engine_lod_latlon(xr_lod_latlon):
    ds_in = xr_lod_latlon
    ds = ds_in.to_xarray(time_dim_mode="raw")

    assert ds is not None
    assert ds["t"].shape == (2, 3, 2)
    assert ds["u"].shape == (2, 3, 2)
    assert np.allclose(ds["latitude"].values, np.array([10.0, 0.0, -10.0]))
    assert np.allclose(ds["longitude"].values, np.array([20.0, 40.0]))


def test_xr_engine_lod_nongeo(xr_lod_nongeo):
    ds_in = xr_lod_nongeo
    ds = ds_in.to_xarray(time_dim_mode="raw")

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


def test_xr_engine_lod_forecast(xr_lod_forecast):
    ds_in = xr_lod_forecast
    ds = ds_in.to_xarray(time_dim_mode="forecast")

    assert ds is not None
    assert ds["t"].shape == (2, 3, 2)
    assert ds["u"].shape == (2, 3, 2)

    dims = {"step": [np.timedelta64(0, "h"), np.timedelta64(6, "h")]}
    compare_dims(ds, dims, order_ref_var="t")

    assert np.allclose(ds["latitude"].values, np.array([10.0, 0.0, -10.0]))
    assert np.allclose(ds["longitude"].values, np.array([20.0, 40.0]))
