#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import copy
import datetime

import numpy as np
import pytest

from earthkit.data.utils.metadata.dict import UserMetadata


def test_usermetadata_nogeom():
    meta = UserMetadata(
        {
            "shortName": "test",
            "longName": "Test",
            "date": 20180801,
            "time": 300,
        }
    )

    assert meta["shortName"] == "test"
    assert meta["longName"] == "Test"
    assert meta["date"] == 20180801
    assert meta["time"] == 300
    assert meta["base_datetime"] == "2018-08-01T03:00:00"
    assert meta.base_datetime() == datetime.datetime(2018, 8, 1, 3, 0)
    assert meta.geography.latitudes() is None
    assert meta.geography.longitudes() is None


@pytest.mark.parametrize("_kwargs", [{}, {"shape": None}, {"shape": (10,)}])
def test_usermetadata_geom(_kwargs):
    meta = UserMetadata(
        {
            "shortName": "test",
            "longName": "Test",
            "date": 20180801,
            "time": 300,
            "latitudes": np.linspace(-10.0, 10.0, 10),
            "longitudes": np.linspace(20.0, 40.0, 10),
        },
        **_kwargs,
    )

    assert meta["shortName"] == "test"
    assert meta["longName"] == "Test"
    assert meta["date"] == 20180801
    assert meta["time"] == 300
    assert meta["base_datetime"] == "2018-08-01T03:00:00"
    assert meta.base_datetime() == datetime.datetime(2018, 8, 1, 3, 0)
    assert meta.geography.shape() == (10,)

    lat = meta.geography.latitudes()
    lon = meta.geography.longitudes()
    assert lat.shape == (10,)
    assert lon.shape == (10,)
    assert np.allclose(lat, meta["latitudes"])
    assert np.allclose(lon, meta["longitudes"])


@pytest.mark.parametrize(
    "initial, update, expected",
    [
        ({"shortName": "2t"}, {}, {"shortName": "2t"}),  # No update
        ({"shortName": "2t"}, {"shortName": "msl"}, {"shortName": "msl"}),  # Update existing key
        (
            {"shortName": "2t"},
            {"longName": "Temperature"},
            {"shortName": "2t", "longName": "Temperature"},
        ),  # Add new key
        ({}, {"shortName": "2t"}, {"shortName": "2t"}),  # Add key to empty metadata
        (
            {"shortName": "2t", "longName": "Temperature"},
            {"shortName": "temperature"},
            {"shortName": "temperature", "longName": "Temperature"},
        ),  # Update one key, keep others
    ],
)
def test_usermetadata_override(initial, update, expected):

    initial_copied = copy.deepcopy(initial)
    update_copied = copy.deepcopy(update)

    meta = UserMetadata(initial)
    new_meta = meta.override(update)
    _ = meta.override(**update)  # Check that the override method works with keyword arguments

    # Check that the updated metadata matches the expected result
    for k, v in expected.items():
        assert new_meta[k] == v

    # Ensure the original metadata remains unchanged
    for k, v in initial_copied.items():
        assert meta[k] == v

    # Check that the updated metadata contains all expected keys
    for k in update_copied:
        if k in initial:
            assert meta[k] == initial[k]
        else:
            assert k not in meta


def test_usermetadata_override_shape():
    meta = UserMetadata({}, shape=(10, 1))
    new_meta = meta.override(
        {
            "shortName": "2t",
            "longName": "Temperature",
        }
    )
    new_meta._shape = None
    assert new_meta._shape is None
    assert meta._shape is not None


@pytest.mark.parametrize("data,ref_base", [({"base_datetime": "2018-08-01T09:00:00"}, "2018-08-01T09:00:00")])
def test_usermetadata_base_date_only(data, ref_base):
    meta = UserMetadata(data)

    ref_base_dt = datetime.datetime.fromisoformat(ref_base)
    assert meta["base_datetime"] == ref_base
    assert meta.base_datetime() == ref_base_dt
    assert meta["valid_datetime"] == ref_base
    assert meta.valid_datetime() == ref_base_dt
    assert meta.datetime() == {"base_time": ref_base_dt, "valid_time": ref_base_dt}


@pytest.mark.parametrize(
    "data,ref_base,ref_valid", [({"valid_datetime": "2018-08-01T09:00:00"}, None, "2018-08-01T09:00:00")]
)
def test_usermetadata_valid_date_only(data, ref_base, ref_valid):
    meta = UserMetadata(data)

    ref_valid_dt = datetime.datetime.fromisoformat(ref_valid)
    assert meta["valid_datetime"] == ref_valid
    assert meta.valid_datetime() == ref_valid_dt
    assert meta.datetime() == {"base_time": ref_base, "valid_time": ref_valid_dt}


@pytest.mark.parametrize(
    "data,ref_base,ref_valid,ref_step",
    [
        (
            {
                "base_datetime": "2018-08-01T03:00:00",
                "step": 6,
            },
            "2018-08-01T03:00:00",
            "2018-08-01T09:00:00",
            6,
        ),
        (
            {
                "valid_datetime": "2018-08-01T09:00:00",
                "step": 6,
            },
            "2018-08-01T03:00:00",
            "2018-08-01T09:00:00",
            6,
        ),
        (
            {
                "forecast_reference_time": "2018-08-01T03:00:00",
                "step": 6,
            },
            "2018-08-01T03:00:00",
            "2018-08-01T09:00:00",
            6,
        ),
        (
            {
                "forecast_reference_time": "2018-08-01T03:00:00",
                "step": datetime.timedelta(hours=6),
            },
            "2018-08-01T03:00:00",
            "2018-08-01T09:00:00",
            datetime.timedelta(hours=6),
        ),
        (
            {
                "date": 20180801,
                "time": 300,
                "step": datetime.timedelta(hours=6),
            },
            "2018-08-01T03:00:00",
            "2018-08-01T09:00:00",
            datetime.timedelta(hours=6),
        ),
    ],
)
def test_usermetadata_forecast(data, ref_base, ref_valid, ref_step):
    meta = UserMetadata(data)

    ref_base_dt = datetime.datetime.fromisoformat(ref_base)
    ref_valid_dt = datetime.datetime.fromisoformat(ref_valid)

    if isinstance(ref_step, int):
        ref_step_td = datetime.timedelta(hours=ref_step)
    else:
        ref_step_td = ref_step

    assert meta["valid_datetime"] == ref_valid
    assert meta.valid_datetime() == ref_valid_dt
    assert meta["base_datetime"] == ref_base
    assert meta.base_datetime() == ref_base_dt
    assert meta.datetime() == {"base_time": ref_base_dt, "valid_time": ref_valid_dt}
    assert meta["step"] == ref_step
    assert meta["step_timedelta"] == ref_step_td
    assert meta.step_timedelta() == ref_step_td
    assert meta["forecast_reference_time"] == ref_base


def test_usermetadata_hdate_from_mars():
    meta = UserMetadata(
        {
            "class": "od",
            "expver": "0001",
            "stream": "enfh",
            "type": "cf",
            "levtype": "sfc",
            "param": "167.128",
            "date": "20180830",  # Model version
            "hdate": "20100830",  # Start date of the forecasts
            "time": "0000",  # Forecast starts at 0am
            "step": 12,  # Forecast 12 hours ahead
        }
    )

    ref_base_dt = datetime.datetime(2010, 8, 30, 0, 0)
    ref_valid_dt = datetime.datetime(2010, 8, 30, 12, 0)

    assert meta.base_datetime() == ref_base_dt
    assert meta.valid_datetime() == ref_valid_dt
    assert meta.datetime() == {"base_time": ref_base_dt, "valid_time": ref_valid_dt}
    assert meta["step"] == 12
    assert meta["step_timedelta"] == datetime.timedelta(hours=12)
    assert meta["date"] == "20180830"
    assert meta["hdate"] == "20100830"
    assert meta["time"] == "0000"
    assert meta["forecast_reference_time"] == "2010-08-30T00:00:00"
