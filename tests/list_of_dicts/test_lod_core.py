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

from earthkit.data import from_source


@pytest.fixture
def lod_distinct_ll():
    prototype = {
        "latitudes": [-10.0, 0.0, 10.0],
        "longitudes": [20, 40.0],
        "values": [1, 2, 3, 4, 5, 6],
        "valid_datetime": "2018-08-01T09:00:00Z",
    }
    return [
        {"param": "t", "levelist": 500, **prototype},
        {"param": "t", "levelist": 850, **prototype},
        {"param": "u", "levelist": 500, **prototype},
        {"param": "u", "levelist": 850, **prototype},
        {"param": "d", "levelist": 850, **prototype},
        {"param": "d", "levelist": 600, **prototype},
    ]


def test_lod_distinct_ll(lod_distinct_ll):
    return
    ds = from_source("list-of-dicts", lod_distinct_ll)

    assert len(ds) == 6
    ref = [("t", 500), ("t", 850), ("u", 500), ("u", 850), ("d", 850), ("d", 600)]
    assert ds.metadata("param", "levelist") == ref

    assert ds[0].shape == (3, 2)

    lat_ref = np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]])
    lon_ref = np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]])

    ll = ds[0].to_latlon()
    lat = ll["lat"]
    lon = ll["lon"]
    assert np.allclose(lat, lat_ref)
    assert np.allclose(lon, lon_ref)

    gr = ds[0].mars_area
    assert isinstance(gr, list)
    assert np.allclose(np.array(gr), np.array([10, 20, -10, 40]))

    gr = ds[0].mars_grid
    assert isinstance(gr, list)
    assert np.allclose(np.array(gr), np.array([20.0, 10.0]))

    gr = ds[0].grid_points()
    assert len(gr) == 2
    assert np.allclose(gr[0], lat_ref.flatten())
    assert np.allclose(gr[1], lon_ref.flatten())

    with pytest.raises(AssertionError):
        ds[0].resolution

    # assert ds[0].metadata("step") == "0"

    # assert ds[0].datetime() == {
    #     "base_time": datetime.datetime(2018, 8, 1, 9, 0),
    #     "valid_time": datetime.datetime(2018, 8, 1, 9, 0),
    # }


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
