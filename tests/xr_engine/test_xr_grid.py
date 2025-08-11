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

import numpy as np
import pytest
import yaml

from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file
from earthkit.data.testing import earthkit_test_data_file
from earthkit.data.utils import ensure_iterable


def to_tuple(x):
    return tuple(ensure_iterable(x))


def grid_list(files=None):
    with open(earthkit_test_data_file(os.path.join("xr_engine", "xr_grid.yaml")), "r") as f:
        r = yaml.safe_load(f)

    files = [] if files is None else files
    for item in r:
        if not files or item["file"] in files:
            yield (item["file"], item["dims"], item["coords"], item["distinct_ll"])


@pytest.mark.cache
@pytest.mark.parametrize(
    "file,dims,coords,distinct_ll",
    # grid_list(files=["sh_t32.grib1"]),
    grid_list(),
)
def test_xr_engine_grid(file, dims, coords, distinct_ll):
    ds = from_source("url", earthkit_remote_test_data_file("test-data", "xr_engine", "grid", file))

    a = ds.to_xarray()
    assert a is not None

    for k, v in dims.items():
        assert a.dims[k] == v

    for k, v in coords.items():
        assert a.coords[k].dims == to_tuple(v[0])
        assert a.coords[k].shape == to_tuple(v[1])

    assert a.t.dims[-(len(dims)) :] == tuple(dims.keys())

    if "latitude" in a.coords and "longitude" in a.coords:
        if distinct_ll:
            lat, lon = ds[0].metadata(("distinctLatitudes", "distinctLongitudes"))
        else:
            ll = ds[0].to_latlon()
            lat = ll["lat"]
            lon = ll["lon"]

        assert np.allclose(a.latitude.values, lat)
        assert np.allclose(a.longitude.values, lon)


@pytest.mark.cache
@pytest.mark.parametrize(
    "add_geo_coords",
    [False, True],
)
def test_xr_engine_add_geo_coords(add_geo_coords):
    ds = from_source(
        "url", earthkit_remote_test_data_file("test-data", "xr_engine", "grid", "reduced_gg_O32.grib1")
    )

    a = ds.to_xarray(add_geo_coords=add_geo_coords)

    assert list(a.sizes.keys())[-1] == "values"

    if add_geo_coords:
        assert "latitude" in a.coords
        assert "longitude" in a.coords
    else:
        assert "latitude" not in a.coords
        assert "longitude" not in a.coords


@pytest.mark.cache
def test_xr_engine_gridspec():
    ds = from_source(
        "url", earthkit_remote_test_data_file("test-data", "xr_engine", "grid", "reduced_gg_O32.grib1")
    )

    r = ds.to_xarray()

    gs = r["r"].earthkit.grid_spec
    assert gs["type"] == "reduced_gg"
    assert gs["grid"] == "O32"

    gs = r["t"].earthkit.grid_spec
    assert gs["type"] == "reduced_gg"
    assert gs["grid"] == "O32"

    gs = r.earthkit.grid_spec
    assert gs["type"] == "reduced_gg"
    assert gs["grid"] == "O32"
