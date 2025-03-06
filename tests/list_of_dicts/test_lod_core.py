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
import os
import sys

import numpy as np
import pytest

here = os.path.dirname(__file__)
sys.path.insert(0, here)

from lod_fixtures import build_lod_fieldlist  # noqa: E402


@pytest.mark.parametrize("lod", ["lod_distinct_ll", "lod_distinct_ll_list_values"])
@pytest.mark.parametrize("mode", ["list-of-dicts", "loop"])
def test_lod_core(lod, mode, request):
    ds = build_lod_fieldlist(request.getfixturevalue(lod), mode)

    assert len(ds) == 6
    ref = [("t", 500), ("t", 850), ("u", 500), ("u", 850), ("d", 850), ("d", 600)]
    assert ds.metadata("param", "levelist") == ref
    assert ds.metadata("shortName", "level") == ref

    assert ds[0].shape == (3, 2)

    lat_ref = np.array([[-10.0, -10.0], [0.0, 0.0], [10.0, 10.0]])
    lon_ref = np.array([[20.0, 40.0], [20.0, 40.0], [20.0, 40.0]])

    ll = ds[0].to_latlon()
    lat = ll["lat"]
    lon = ll["lon"]
    assert np.allclose(lat, lat_ref)
    assert np.allclose(lon, lon_ref)

    val_ref = [[1, 2], [3, 4], [5, 6]]
    # print(ds[0].to_numpy())
    # print(ds.to_numpy())

    assert ds[0].to_numpy().shape == (3, 2)
    assert np.allclose(ds[0].to_numpy(), np.array(val_ref))

    assert ds.to_numpy().shape == (6, 3, 2)
    assert np.allclose(ds.to_numpy(), np.array([val_ref for _ in range(6)]))


@pytest.mark.parametrize("mode", ["list-of-dicts", "loop"])
def test_lod_ll(lod_distinct_ll, mode):
    ds = build_lod_fieldlist(lod_distinct_ll, mode)

    assert len(ds) == 6
    ref = [("t", 500), ("t", 850), ("u", 500), ("u", 850), ("d", 850), ("d", 600)]
    assert ds.metadata("param", "levelist") == ref
    assert ds.metadata("shortName", "level") == ref

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

    assert ds[0].resolution is None

    assert ds[0].datetime() == {
        "base_time": None,
        "valid_time": datetime.datetime(2018, 8, 1, 9, 0),
    }


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
