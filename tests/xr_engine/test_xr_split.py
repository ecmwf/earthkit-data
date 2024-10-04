#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,num,variables,dim_keys,split_values",
    [
        (
            {"time_dim_mode": "raw", "split_dims": ["step"]},
            2,
            ["2t", "msl", "r", "t"],
            ["date", "time", "levelist"],
            {"step": [0, 6]},
        ),
        (
            {"time_dim_mode": "raw", "split_dims": ["step"], "ensure_dims": "step"},
            2,
            ["2t", "msl", "r", "t"],
            ["date", "time", "step", "levelist"],
            {"step": [0, 6]},
        ),
        # ({"base_datetime_dim": True}, "param", ["r", "t"], ["levelist"]),
        # ({"squeeze": False}, "param", ["r", "t"], ["time", "step", "levelist"]),
    ],
)
def test_xr_split(kwargs, num, variables, dim_keys, split_values):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data", "xr_engine", "level", "pl.grib"))

    dim_keys = dim_keys + ["latitude", "longitude"]
    ds_lst = ds_ek.to_xarray(**kwargs)
    assert len(ds_lst) == num
    for ds in ds_lst:
        assert list(ds.dims.keys()) == dim_keys
