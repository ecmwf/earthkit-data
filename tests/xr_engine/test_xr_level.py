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

import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import compare_coords  # noqa: E402


@pytest.mark.parametrize(
    "kwargs,dims",
    [
        (
            {"level_dim_mode": "level"},
            {"levelist": [300, 400, 500, 700, 850, 1000]},
        ),
    ],
)
def test_xr_level(kwargs, dims):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl_regular_ll.grib"))

    ds = ds_ek.to_xarray(**kwargs)

    dim_order = []
    for d in ds["t"].dims:
        if d in dims:
            dim_order.append(d)
    assert dim_order == list(dims.keys())

    compare_coords(ds, dims)
