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
    "url_suffix,kwargs,num,variables,dim_keys,split_values",
    [
        (
            ["level", "pl.grib"],
            {"time_dim_mode": "raw", "split_dims": ["step"], "dim_name_from_role_name": False},
            2,
            ["2t", "msl", "r", "t"],
            ["date", "time", "levelist"],
            [{"step": 0}, {"step": 6}],
        ),
        (
            ["level", "pl.grib"],
            {
                "time_dim_mode": "raw",
                "split_dims": ["step"],
                "ensure_dims": "step",
                "dim_name_from_role_name": False,
            },
            2,
            ["2t", "msl", "r", "t"],
            ["date", "time", "step", "levelist"],
            [{"step": 0}, {"step": 6}],
        ),
        (
            ["cds-reanalysis-era5-single-levels-20230101-low-resol.grib"],
            {
                "time_dim_mode": "valid_time",
                "split_dims": ["stream", "dataType", "edition", "Ni"],
                "dim_name_from_role_name": False,
            },
            11,
            None,
            ["valid_time"],
            [
                {"stream": "enda", "dataType": "an", "edition": 1, "Ni": 18},
                {"stream": "enda", "dataType": "em", "edition": 1, "Ni": 18},
                {"stream": "enda", "dataType": "es", "edition": 1, "Ni": 18},
                {"stream": "enda", "dataType": "fc", "edition": 1, "Ni": 18},
                {"stream": "enda", "dataType": "fc", "edition": 2, "Ni": 18},
                {"stream": "ewda", "dataType": "an", "edition": 1, "Ni": 12},
                {"stream": "ewda", "dataType": "em", "edition": 1, "Ni": 12},
                {"stream": "ewda", "dataType": "es", "edition": 1, "Ni": 12},
                {"stream": "oper", "dataType": "an", "edition": 1, "Ni": 36},
                {"stream": "oper", "dataType": "fc", "edition": 1, "Ni": 36},
                {"stream": "wave", "dataType": "an", "edition": 1, "Ni": 18},
            ],
        ),
        (
            ["level", "pl.grib"],
            {"time_dim_mode": "raw", "split_dims": ["step"], "dim_name_from_role_name": True},
            2,
            ["2t", "msl", "r", "t"],
            ["date", "time", "level"],
            [{"step": 0}, {"step": 6}],
        ),
        (
            ["level", "pl.grib"],
            {
                "time_dim_mode": "raw",
                "split_dims": ["step"],
                "ensure_dims": "step",
                "dim_name_from_role_name": True,
            },
            2,
            ["2t", "msl", "r", "t"],
            ["date", "time", "step", "level"],
            [{"step": 0}, {"step": 6}],
        ),
        # ({"base_datetime_dim": True}, "param", ["r", "t"], ["levelist"]),
        # ({"squeeze": False}, "param", ["r", "t"], ["time", "step", "levelist"]),
    ],
)
def test_xr_split(url_suffix, kwargs, num, variables, dim_keys, split_values):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data", "xr_engine", *url_suffix))

    dim_keys = dim_keys + ["latitude", "longitude"]
    ds_lst, split_coords_lst = ds_ek.to_xarray(**kwargs)
    assert len(ds_lst) == num
    assert len(split_coords_lst) == len(split_values)

    def dict_to_frozenset_of_kvpairs(d):
        return frozenset(d.items())

    _split_coords_lst = frozenset(map(dict_to_frozenset_of_kvpairs, split_coords_lst))
    _split_values = frozenset(map(dict_to_frozenset_of_kvpairs, split_values))
    assert _split_coords_lst == _split_values
    for ds in ds_lst:
        assert sorted(ds.dims) == sorted(dim_keys)
