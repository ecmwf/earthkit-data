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

import pytest

from earthkit.data import from_source
from earthkit.data.utils import ensure_iterable

SAMPLE_DATA_FOLDER = "~/git/cfgrib/tests/sample-data"
SAMPLE_DATA_FOLDER = "/Users/cgr/metview/python_test/earthkit_data/engine/new"


def to_tuple(x):
    x = tuple(ensure_iterable(x))


@pytest.mark.parametrize(
    "grib_name,dims,coords",
    [
        (
            "regular_ll.grib1",
            {"latitude": 19, "longitude": 36},
            {"latitude": ["latitude", 19], "longitude": ["longitude", 36]},
        ),
        (
            "regular_ll.grib2",
            {"latitude": 19, "longitude": 36},
            {"latitude": ["latitude", 19], "longitude": ["longitude", 36]},
        ),
        # "era5-levels-members",
        # "fields_with_missing_values",
        # "lambert_grid",
        # "reduced_gg",
        # "regular_gg_sfc",
        # "regular_gg_pl",
        # "regular_gg_ml",
        # "regular_gg_ml_g2",
        # "regular_ll_sfc",
        # "regular_ll_msl",
        # "scanning_mode_64",
        # "single_gridpoint",
        # "spherical_harmonics",
        # "t_analysis_and_fc_0",
    ],
)
def test_xr_engine_geo(grib_name, dims, coords):
    grib_path = os.path.join(SAMPLE_DATA_FOLDER, grib_name)
    print(f"Reading {grib_path}")
    ds = from_source("file", grib_path)

    a = ds.to_xarray()
    assert a is not None

    for k, v in dims.items():
        assert a.dims[k] == v

    for k, v in coords.items():
        assert a.coords[k].dims == to_tuple(v[0])
        assert a.coords[k].shape == to_tuple(v[1])

    assert a.t.dims[-2:] == tuple(dims.keys())

    # if "latitude" in a.coords and "longitude" in a.coords:
    #     assert a.latitude.shape == (19,)

    # assert r.dims["latitude"] == 19
    # assert r.dims["longitude"] == 36
    # assert r.coords["latitude"].shape == (19,)
    # assert r.coords["longitude"].shape == (36,)
    # assert r.t.dims[-2:] == ("latitude", "longitude")
