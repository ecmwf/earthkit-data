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

from earthkit.data import ArrayField
from earthkit.data.utils.metadata.dict import UserMetadata


def test_array_field_usermetadata_nogeom():
    vals = np.linspace(0, 1, 10)
    meta = UserMetadata(
        {
            "shortName": "test",
            "longName": "Test",
            "date": 20180801,
            "time": 300,
        }
    )

    f = ArrayField(vals, meta)

    assert f.metadata("shortName") == "test"
    assert f.metadata("longName") == "Test"
    assert f.metadata("date") == 20180801
    assert f.metadata("time") == 300
    assert f.datetime()["base_time"] == datetime.datetime(2018, 8, 1, 3, 0)
    assert f.shape == (10,)
    assert np.allclose(f.values, vals)

    with pytest.raises(ValueError):
        f.to_latlon()


@pytest.mark.parametrize("_kwargs", [{}, {"shape": None}, {"shape": (10,)}])
def test_array_field_usermetadata_geom(_kwargs):
    vals = np.linspace(0, 1, 10)
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

    f = ArrayField(vals, meta)

    assert f.metadata("shortName") == "test"
    assert f.metadata("longName") == "Test"
    assert f.metadata("date") == 20180801
    assert f.metadata("time") == 300
    assert f.datetime()["base_time"] == datetime.datetime(2018, 8, 1, 3, 0)
    assert f.shape == (10,)
    lat = f.to_latlon()["lat"]
    lon = f.to_latlon()["lon"]
    assert lat.shape == (10,)
    assert lon.shape == (10,)
    assert np.allclose(lat, meta["latitudes"])
    assert np.allclose(lon, meta["longitudes"])
    assert np.allclose(f.values, vals)


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
def test_array_field_usermetadata_override(initial, update, expected):

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


def test_array_field_usermetadata_override_shape():
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
