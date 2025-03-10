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

here = os.path.dirname(__file__)
sys.path.insert(0, here)

from lod_fixtures import build_lod_fieldlist  # noqa: E402


@pytest.mark.parametrize("mode", ["list-of-dicts", "loop"])
def test_lod_geo_distinct_ll(lod_distinct_ll, mode):
    ds = build_lod_fieldlist(lod_distinct_ll, mode)

    assert len(ds) == 6
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

    ll = ds.to_latlon()
    lat = ll["lat"]
    lon = ll["lon"]
    assert np.allclose(lat, lat_ref)
    assert np.allclose(lon, lon_ref)


@pytest.mark.parametrize("mode", ["list-of-dicts", "loop"])
def test_lod_geo_ll_flat(lod_ll_flat, mode):
    ds = build_lod_fieldlist(lod_ll_flat, mode)

    assert len(ds) == 6
    assert ds[0].shape == (6,)

    lat_ref = np.array([-10.0, -10.0, 0.0, 0.0, 10.0, 10.0])
    lon_ref = np.array([20.0, 40.0, 20.0, 40.0, 20.0, 40.0])

    ll = ds[0].to_latlon()
    lat = ll["lat"]
    lon = ll["lon"]
    assert np.allclose(lat, lat_ref)
    assert np.allclose(lon, lon_ref)

    gr = ds[0].mars_area
    assert isinstance(gr, list)
    assert np.allclose(np.array(gr), np.array([10, 20, -10, 40]))

    with pytest.raises(NotImplementedError):
        gr = ds[0].mars_grid

    gr = ds[0].grid_points()
    assert len(gr) == 2
    assert np.allclose(gr[0], lat_ref.flatten())
    assert np.allclose(gr[1], lon_ref.flatten())

    assert ds[0].resolution is None

    ll = ds.to_latlon()
    lat = ll["lat"]
    lon = ll["lon"]
    assert np.allclose(lat, lat_ref)
    assert np.allclose(lon, lon_ref)


@pytest.mark.parametrize("data", ["lod_ll_2D_all", "lod_ll_2D_ll", "lod_ll_2D_values"])
@pytest.mark.parametrize("mode", ["list-of-dicts", "loop"])
def test_lod_geo_ll_2D(request, data, mode):
    ds = build_lod_fieldlist(request.getfixturevalue(data), mode)

    assert len(ds) == 6
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

    # gr = ds[0].mars_grid
    # assert isinstance(gr, list)
    # assert np.allclose(np.array(gr), np.array([20.0, 10.0]))

    gr = ds[0].grid_points()
    assert len(gr) == 2
    assert np.allclose(gr[0], lat_ref.flatten())
    assert np.allclose(gr[1], lon_ref.flatten())

    assert ds[0].resolution is None

    ll = ds.to_latlon()
    lat = ll["lat"]
    lon = ll["lon"]
    assert np.allclose(lat, lat_ref)
    assert np.allclose(lon, lon_ref)


@pytest.mark.parametrize("data", ["lod_ll_flat_invalid"])
@pytest.mark.parametrize("mode", ["list-of-dicts", "loop"])
def test_lod_geo_invalid(
    request,
    data,
    mode,
):
    ds = build_lod_fieldlist(request.getfixturevalue(data), mode)

    assert len(ds) == 6
    with pytest.raises(ValueError):
        ds[0].shape


@pytest.mark.parametrize("data", ["lod_no_latlon"])
@pytest.mark.parametrize("mode", ["list-of-dicts", "loop"])
def test_lod_no_latlon(
    request,
    data,
    mode,
):
    ds = build_lod_fieldlist(request.getfixturevalue(data), mode)

    assert len(ds) == 6
    assert ds[0].shape == (6,)
    assert ds[0].values.shape == (6,)
    assert ds.values.shape == (6, 6)

    with pytest.raises(ValueError):
        ds[0].to_latlon()


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
