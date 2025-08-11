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
from xr_engine_fixtures import compare_dims  # noqa: E402


@pytest.mark.cache
@pytest.mark.parametrize(
    "_kwargs,dims,coords",
    [
        ({"fixed_dims": ["valid_time", "param"]}, {"valid_time": 732, "param": 1}, {"param": ["2t"]}),
        ({"fixed_dims": ["param", "valid_time"]}, {"param": 1, "valid_time": 732}, {"param": ["2t"]}),
    ],
)
def test_xr_engine_mono_variable_1(_kwargs, dims, coords):
    ds_in = from_source(
        "url", earthkit_remote_test_data_file("test-data", "xr_engine", "date", "t2_1_year.grib")
    )

    ds = ds_in.to_xarray(
        mono_variable=True,
        chunks={"valid_time": 1},
        add_earthkit_attrs=False,
        **_kwargs,
    )

    assert ds is not None

    dims["latitude"] = 3
    dims["longitude"] = 3

    compare_dims(ds, dims, order_ref_var="data", sizes=True)
    compare_coords(ds, coords)


@pytest.mark.cache
@pytest.mark.parametrize(
    "_kwargs,dims,coords",
    [
        ({"fixed_dims": ["valid_time", "param"]}, {"valid_time": 732, "param": 2}, {"param": ["2d", "2t"]}),
        ({"fixed_dims": ["param", "valid_time"]}, {"param": 2, "valid_time": 732}, {"param": ["2d", "2t"]}),
    ],
)
def test_xr_engine_mono_variable_2(_kwargs, dims, coords):
    ds_in = from_source(
        "url", earthkit_remote_test_data_file("test-data", "xr_engine", "date", "t2_td2_1_year.grib")
    )

    ds = ds_in.to_xarray(
        mono_variable=True,
        chunks={"valid_time": 1},
        add_earthkit_attrs=False,
        **_kwargs,
    )

    assert ds is not None

    dims["latitude"] = 3
    dims["longitude"] = 3

    compare_dims(ds, dims, order_ref_var="data", sizes=True)
    compare_coords(ds, coords)
