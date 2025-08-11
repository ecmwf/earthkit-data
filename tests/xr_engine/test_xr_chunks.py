#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import numpy as np
import pytest

from earthkit.data import config
from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file


@pytest.mark.long_test
@pytest.mark.cache
@pytest.mark.parametrize(
    "field_policy",
    [
        {"grib-field-policy": "persistent"},
        {"grib-field-policy": "temporary"},
    ],
)
@pytest.mark.parametrize(
    "handle_policy",
    [
        {"grib-handle-policy": "persistent"},
        {"grib-handle-policy": "temporary"},
        {"grib-handle-policy": "cache", "grib-handle-cache-size": 1},
        {"grib-handle-policy": "cache", "grib-handle-cache-size": 10},
        {"grib-handle-policy": "cache", "grib-handle-cache-size": 100},
        {"grib-handle-policy": "cache", "grib-handle-cache-size": 300},
    ],
)
@pytest.mark.parametrize(
    "_kwargs",
    [
        {},
        {"chunks": "auto"},
        {"chunks": {"valid_time": 1}},
        {"chunks": {"valid_time": 10}},
        {"chunks": {"valid_time": (100, 200, 432), "latitude": (1, 2), "longitude": (2, 1)}},
        {"chunks": -1},
    ],
)
def test_xr_engine_chunk_1(field_policy, handle_policy, _kwargs):
    with config.temporary(**field_policy, **handle_policy):
        ds_in = from_source(
            "url", earthkit_remote_test_data_file("test-data", "xr_engine", "date", "t2_1_year.grib")
        )

        ds = ds_in.to_xarray(time_dim_mode="valid_time", **_kwargs)

        assert ds is not None

        r = ds["2t"].mean("valid_time").load()

        assert np.isclose(r.values.mean(), 287.2627299620878)


# This test is a copy of the previous one, but only using the default config
@pytest.mark.cache
@pytest.mark.parametrize(
    "_kwargs",
    [
        {},
        {"chunks": "auto"},
        {"chunks": {"valid_time": 1}},
        {"chunks": {"valid_time": 10}},
        {"chunks": {"valid_time": (100, 200, 432), "latitude": (1, 2), "longitude": (2, 1)}},
        {"chunks": -1},
    ],
)
def test_xr_engine_chunk_2(_kwargs):
    # the default settings
    field_policy = {"grib-field-policy": "persistent"}
    handle_policy = {"grib-handle-policy": "cache", "grib-handle-cache-size": 1}

    with config.temporary(**field_policy, **handle_policy):
        ds_in = from_source(
            "url", earthkit_remote_test_data_file("test-data", "xr_engine", "date", "t2_1_year.grib")
        )

        ds = ds_in.to_xarray(time_dim_mode="valid_time", **_kwargs)

        assert ds is not None

        r = ds["2t"].mean("valid_time").load()

        assert np.isclose(r.values.mean(), 287.2627299620878)


@pytest.mark.cache
@pytest.mark.parametrize(
    "_kwargs",
    [
        {},
        {"chunks": "auto"},
        {"chunks": {"valid_time": 1}},
        {"chunks": {"valid_time": 10}},
        {"chunks": {"valid_time": (100, 200, 432), "latitude": (1, 2), "longitude": (2, 1)}},
        {"chunks": {"valid_time": 100, "latitude": 2, "longitude": 1}},
        {"chunks": -1},
    ],
)
def test_xr_engine_chunk_3(_kwargs):
    # in-memory fieldlist
    ds_in = from_source(
        "url",
        earthkit_remote_test_data_file("test-data", "xr_engine", "date", "t2_1_year.grib"),
        stream=True,
        read_all=True,
    )

    ds = ds_in.to_xarray(time_dim_mode="valid_time", **_kwargs)
    assert ds is not None

    r = ds["2t"].mean("valid_time").load()

    assert np.isclose(r.values.mean(), 287.2627299620878)
