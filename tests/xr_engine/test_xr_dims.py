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
from earthkit.data.utils.xarray.profile import Profile

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import compare_dim_order  # noqa: E402
from xr_engine_fixtures import load_wrapped_fieldlist  # noqa: E402

DS_LEV = {
    "class": ["od"],
    "param": ["t", "r"],
    "levelist": [1000, 850],
    "level": [1000, 850],
    "time": ["12"],
    "step": [0],
}

DS_DATE_LEV = {
    "class": ["od"],
    "param": ["t", "r"],
    "shortName": ["t", "r"],
    "levelist": [1000, 850],
    "level": [1000, 850],
    "levtype": ["pl"],
    "date": ["20210101", "20210102"],
    "time": ["12"],
    "step": [0],
    # "base_datetime": ["2021-01-01T12:00:00", "2021-01-02T12:00:00"],
}

DS_DATE_STEPS_LEVEL = {
    "class": ["od"],
    "param": ["t", "r"],
    "shortName": ["t", "r"],
    "levelist": [1000, 850],
    "level": [1000, 850],
    "levtype": ["pl"],
    "date": ["20210101", "20210102"],
    "time": ["12"],
    "step": [0, 6],
    # "base_datetime": ["2021-01-01T12:00:00", "2021-01-02T12:00:00"],
}

DS_DATE_SFC_PL = [
    {
        "class": ["od"],
        "param": ["2t", "msl"],
        "shortName": ["2t", "msl"],
        "levelist": [None],
        "level": [None],
        "levtype": ["sfc"],
        "date": ["20210101", "20210102"],
        "time": ["12"],
        "step": [0],
    },
    {
        "class": ["od"],
        "param": ["t", "r"],
        "shortName": ["t", "r"],
        "levelist": [1000, 850],
        "level": [1000, 850],
        "levtype": ["pl"],
        "date": ["20210101", "20210102"],
        "time": ["12"],
        "step": [0],
    },
]


def _attributes(ds):
    return {k: v[0] for k, v in ds.indices().items() if len(v) == 1}


def test_xr_dims_input_fieldlist():
    prof = Profile.make("mars")
    ds = load_wrapped_fieldlist(DS_DATE_LEV, prof)
    assert ds.index("param") == ["r", "t"]
    assert ds.index("param_level") == ["r1000", "r850", "t1000", "t850"]

    remapping = {"param_level": "{param}_{level}"}
    prof = Profile.make("mars", variable_key="param_level", remapping=remapping)
    ds = load_wrapped_fieldlist(DS_DATE_LEV, prof, remapping=prof.remapping.build())
    assert ds.index("param") == ["r", "t"]
    assert ds.index("param_level") == ["r_1000", "r_850", "t_1000", "t_850"]

    remapping = {
        "_class": "_{class}",
        "level_and_type": "{level}_{levtype}",
    }
    prof = Profile.make(
        "mars", variable_key="param", remapping=remapping, extra_dims=["_class", "level_and_type"]
    )
    ds = load_wrapped_fieldlist(DS_DATE_LEV, prof, remapping=prof.remapping.build())
    assert ds.index("param") == ["r", "t"]
    assert ds.index("_class") == ["_od"]
    assert ds.index("level_and_type") == ["1000_pl", "850_pl"]


@pytest.mark.parametrize(
    "kwargs,var_key,variables,dim_keys",
    [
        ({}, "param", ["r", "t"], ["step", "levelist"]),
        (
            {"time_dim_mode": "forecast"},
            "param",
            ["r", "t"],
            ["step", "levelist"],
        ),
        (
            {"squeeze": False, "time_dim_mode": "raw"},
            "param",
            ["r", "t"],
            ["time", "step", "levelist"],
        ),
    ],
)
def test_xr_dims_ds_lev(kwargs, var_key, variables, dim_keys):
    prof = Profile.make("mars", **kwargs)
    ds = load_wrapped_fieldlist(DS_LEV, prof)
    # prof.update(ds, _attributes(ds))
    prof.update(ds)
    assert prof.variable_key == var_key
    assert prof.variables == variables
    assert prof.dim_keys == dim_keys


@pytest.mark.parametrize(
    "kwargs,var_key,variables,dims",
    [
        # ({"time_dim_mode": "raw"}, "param", ["r", "t"], ["date", "time", "step", "levelist"]),
        (
            {"time_dim_mode": "forecast"},
            "param",
            ["r", "t"],
            ["forecast_reference_time", "step", "levelist", "levtype"],
        ),
        (
            {"time_dim_mode": "raw", "variable_key": "param_level"},
            "param_level",
            ["r1000", "r850", "t1000", "t850"],
            ["date", "time", "step", "levtype"],
        ),
        # (
        #     {"time_dim_mode": "raw", "extra_dims": "param_level"},
        #     "param_level",
        #     [
        #         "r1000",
        #         "r850",
        #         "t1000",
        #         "t850",
        #     ],
        #     ["date"],
        # ),
        (
            {
                "time_dim_mode": "raw",
                "variable_key": "param_level",
                "remapping": {"param_level": "{param}_{level}"},
            },
            "param_level",
            ["r_1000", "r_850", "t_1000", "t_850"],
            ["date", "time", "step", "levtype"],
        ),
        (
            {"time_dim_mode": "raw", "variable_key": "shortName"},
            "shortName",
            ["r", "t"],
            ["date", "time", "step", "levelist", "levtype"],
        ),
        (
            {"time_dim_mode": "raw", "variable_key": "shortName", "drop_variables": ["r"]},
            "shortName",
            ["t"],
            ["date", "time", "step", "levelist", "levtype"],
        ),
        (
            {"time_dim_mode": "raw", "variable_key": "param_level", "drop_variables": ["r", "r1000"]},
            "param_level",
            ["r850", "t1000", "t850"],
            [
                "date",
                "time",
                "step",
                "levtype",
            ],
        ),
        # (
        #     {"use_level_per_type_dim": True},
        #     "param",
        #     ["r", "t"],
        #     {"date": ["20210101", "20210102"], "level_per_type": ["850pl", "1000pl"]},
        # ),
        (
            {"time_dim_mode": "raw", "level_dim_mode": "level_and_type"},
            "param",
            ["r", "t"],
            {
                "date": ["20210101", "20210102"],
                "time": ["12"],
                "step": [0],
                "level_and_type": ["1000pl", "850pl"],
            },
        ),
        (
            {"time_dim_mode": "raw", "extra_dims": "class"},
            "param",
            ["r", "t"],
            {
                "class": ["od"],
                "date": ["20210101", "20210102"],
                "time": ["12"],
                "step": [0],
                "levelist": [850, 1000],
                "levtype": ["pl"],
            },
        ),
        (
            {"time_dim_mode": "raw", "ensure_dims": "class"},
            "param",
            ["r", "t"],
            {
                "class": ["od"],
                "date": ["20210101", "20210102"],
                "time": ["12"],
                "step": [0],
                "levelist": [850, 1000],
                "levtype": ["pl"],
            },
        ),
        (
            {"time_dim_mode": "raw", "ensure_dims": ["class", "step"]},
            "param",
            ["r", "t"],
            {
                "class": ["od"],
                "date": ["20210101", "20210102"],
                "time": ["12"],
                "step": [0],
                "levelist": [850, 1000],
                "levtype": ["pl"],
            },
        ),
        (
            {"time_dim_mode": "raw", "extra_dims": "class", "squeeze": False},
            "param",
            ["r", "t"],
            {
                "class": ["od"],
                "date": ["20210101", "20210102"],
                "time": ["12"],
                "step": [0],
                "levelist": [850, 1000],
                "levtype": ["pl"],
            },
        ),
    ],
)
def test_xr_dims_ds_date_lev(kwargs, var_key, variables, dims):

    prof = Profile.make("mars", **kwargs)
    ds = load_wrapped_fieldlist(DS_DATE_LEV, prof, remapping=prof.remapping.build())

    # print("remapping", prof.remapping.build())
    # print(f"ds: {ds.indices()}")

    # ds.load(prof.index_keys)
    # prof.update(ds, _attributes(ds))
    prof.update(ds)
    assert prof.variable_key == var_key
    assert prof.variables == variables

    if isinstance(dims, list):
        assert prof.dim_keys == dims
    elif isinstance(dims, dict):
        assert prof.dim_keys == list(dims.keys())
        for k in prof.dim_keys:
            assert ds.index(k) == dims[k]
    else:
        raise ValueError(f"Unsupported dims: {dims}")


@pytest.mark.parametrize(
    "kwargs,var_key,variables,dim_keys",
    [
        (
            {"time_dim_mode": "raw"},
            "param",
            ["2t", "msl", "r", "t"],
            ["date", "time", "step", "levelist", "levtype"],
        ),
        # ({"base_datetime_dim": True}, "param", ["r", "t"], ["levelist", "levtype"]),
        # ({"squeeze": False}, "param", ["r", "t"], ["time", "step", "levelist", "levtype"]),
    ],
)
def test_xr_dims_ds_sfc_and_pl(kwargs, var_key, variables, dim_keys):
    prof = Profile.make("mars", **kwargs)
    ds = load_wrapped_fieldlist(DS_DATE_SFC_PL, prof)
    # prof.update(ds, _attributes(ds))
    prof.update(ds)
    assert prof.variable_key == var_key
    assert prof.variables == variables
    assert prof.dim_keys == dim_keys


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dim_keys",
    [
        (
            {"profile": "mars", "time_dim_mode": "raw", "rename_dims": {"levelist": "zz"}},
            ["date", "time", "step", "zz"],
        ),
    ],
)
def test_xr_rename_dims(kwargs, dim_keys):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl.grib"))
    ds = ds_ek.to_xarray(**kwargs)
    num = len(ds)

    dim_keys = dim_keys + ["latitude", "longitude"]
    assert len(ds) == num

    for v in ds:
        compare_dim_order(ds, dim_keys, v)
