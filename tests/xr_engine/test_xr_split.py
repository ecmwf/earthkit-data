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

import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize(
    "url_suffix,kwargs,num,variables,dim_keys,split_values",
    [
        (
            ["level", "pl.grib"],
            {"time_dim_mode": "raw", "split_dims": ["time.step"], "dim_name_from_role_name": False},
            2,
            ["2t", "msl", "r", "t"],
            ["date", "time", "levelist"],
            [{"time.step": datetime.timedelta(hours=0)}, {"time.step": datetime.timedelta(hours=6)}],
        ),
        (
            ["level", "pl.grib"],
            {
                "time_dim_mode": "raw",
                "split_dims": ["metadata.step"],
                "ensure_dims": "metadata.step",
                "dim_name_from_role_name": False,
            },
            2,
            ["2t", "msl", "r", "t"],
            ["date", "time", "step", "levelist"],
            [{"metadata.step": 0}, {"metadata.step": 6}],
        ),
        (
            ["cds-reanalysis-era5-single-levels-20230101-low-resol.grib"],
            {
                "time_dim_mode": "valid_time",
                "split_dims": ["metadata.stream", "metadata.dataType", "metadata.edition", "metadata.Ni"],
                "dim_name_from_role_name": False,
            },
            11,
            None,
            ["valid_time"],
            [
                {
                    "metadata.stream": "enda",
                    "metadata.dataType": "an",
                    "metadata.edition": 1,
                    "metadata.Ni": 18,
                },
                {
                    "metadata.stream": "enda",
                    "metadata.dataType": "em",
                    "metadata.edition": 1,
                    "metadata.Ni": 18,
                },
                {
                    "metadata.stream": "enda",
                    "metadata.dataType": "es",
                    "metadata.edition": 1,
                    "metadata.Ni": 18,
                },
                {
                    "metadata.stream": "enda",
                    "metadata.dataType": "fc",
                    "metadata.edition": 1,
                    "metadata.Ni": 18,
                },
                {
                    "metadata.stream": "enda",
                    "metadata.dataType": "fc",
                    "metadata.edition": 2,
                    "metadata.Ni": 18,
                },
                {
                    "metadata.stream": "ewda",
                    "metadata.dataType": "an",
                    "metadata.edition": 1,
                    "metadata.Ni": 12,
                },
                {
                    "metadata.stream": "ewda",
                    "metadata.dataType": "em",
                    "metadata.edition": 1,
                    "metadata.Ni": 12,
                },
                {
                    "metadata.stream": "ewda",
                    "metadata.dataType": "es",
                    "metadata.edition": 1,
                    "metadata.Ni": 12,
                },
                {
                    "metadata.stream": "oper",
                    "metadata.dataType": "an",
                    "metadata.edition": 1,
                    "metadata.Ni": 36,
                },
                {
                    "metadata.stream": "oper",
                    "metadata.dataType": "fc",
                    "metadata.edition": 1,
                    "metadata.Ni": 36,
                },
                {
                    "metadata.stream": "wave",
                    "metadata.dataType": "an",
                    "metadata.edition": 1,
                    "metadata.Ni": 18,
                },
            ],
        ),
        (
            ["level", "pl.grib"],
            {"time_dim_mode": "raw", "split_dims": ["time.step"], "dim_name_from_role_name": True},
            2,
            ["2t", "msl", "r", "t"],
            ["date", "time", "level"],
            [{"time.step": datetime.timedelta(hours=0)}, {"time.step": datetime.timedelta(hours=6)}],
        ),
        (
            ["level", "pl.grib"],
            {"time_dim_mode": "raw", "split_dims": ["metadata.step"], "dim_name_from_role_name": True},
            2,
            ["2t", "msl", "r", "t"],
            ["date", "time", "level"],
            [{"metadata.step": 0}, {"metadata.step": 6}],
        ),
        (
            ["level", "pl.grib"],
            {
                "time_dim_mode": "raw",
                "split_dims": ["time.step"],
                "ensure_dims": "step",
                "dim_name_from_role_name": True,
            },
            2,
            ["2t", "msl", "r", "t"],
            ["date", "time", "step", "level"],
            [{"time.step": datetime.timedelta(hours=0)}, {"time.step": datetime.timedelta(hours=6)}],
        ),
        # ({"base_datetime_dim": True}, "param", ["r", "t"], ["levelist"]),
        # ({"squeeze": False}, "param", ["r", "t"], ["time", "step", "levelist"]),
    ],
)
def test_xr_split(allow_holes, url_suffix, kwargs, num, variables, dim_keys, split_values):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine", *url_suffix))

    dim_keys = dim_keys + ["latitude", "longitude"]
    ds_lst, split_coords_lst = ds_ek.to_xarray(allow_holes=allow_holes, **kwargs)
    assert len(ds_lst) == num
    assert len(split_coords_lst) == len(split_values)

    def dict_to_frozenset_of_kvpairs(d):
        return frozenset(d.items())

    _split_coords_lst = frozenset(map(dict_to_frozenset_of_kvpairs, split_coords_lst))
    _split_values = frozenset(map(dict_to_frozenset_of_kvpairs, split_values))
    assert _split_coords_lst == _split_values
    for ds in ds_lst:
        assert sorted(ds.dims) == sorted(dim_keys)
