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
