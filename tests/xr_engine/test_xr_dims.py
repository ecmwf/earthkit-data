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

from earthkit.data.utils.xarray.profile import MarsProfile

here = os.path.dirname(__file__)
sys.path.insert(0, here)
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
        "level": [FileNotFoundError],
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
    prof = MarsProfile()
    ds = load_wrapped_fieldlist(DS_DATE_LEV, prof)
    assert ds.index("param") == ["r", "t"]
    assert ds.index("param_level") == ["r1000", "r850", "t1000", "t850"]
    assert ds.index("level_and_type") == ["1000pl", "850pl"]

    remapping = {"param_level": "{param}_{level}"}
    prof = MarsProfile(remapping=remapping)
    ds = load_wrapped_fieldlist(DS_DATE_LEV, prof, remapping=remapping)
    assert ds.index("param") == ["r", "t"]
    assert ds.index("param_level") == ["r_1000", "r_850", "t_1000", "t_850"]

    remapping = {
        "param_level": "{param}_{level}",
        "level_and_type": "{level}_{levtype}",
    }
    prof = MarsProfile(remapping=remapping)
    ds = load_wrapped_fieldlist(DS_DATE_LEV, prof, remapping=remapping)
    assert ds.index("param") == ["r", "t"]
    assert ds.index("param_level") == ["r_1000", "r_850", "t_1000", "t_850"]
    assert ds.index("level_and_type") == ["1000_pl", "850_pl"]


@pytest.mark.parametrize(
    "kwargs,variable_key,variables,dim_keys",
    [
        ({}, "param", ["r", "t"], ["levelist"]),
        ({"base_datetime_dim": True}, "param", ["r", "t"], ["levelist"]),
        ({"squeeze": False}, "param", ["r", "t"], ["time", "step", "levelist"]),
    ],
)
def test_xr_dims_ds_lev(kwargs, variable_key, variables, dim_keys):
    prof = MarsProfile(**kwargs)
    ds = load_wrapped_fieldlist(DS_LEV, prof)
    prof.update(ds, _attributes(ds))
    assert prof.variable_key == variable_key
    assert prof.variables == variables
    assert prof.dim_keys == dim_keys


@pytest.mark.parametrize(
    "kwargs,variable_key,variables,dims",
    [
        ({}, "param", ["r", "t"], ["date", "levelist"]),
        (
            {"base_datetime_dim": True},
            "param",
            ["r", "t"],
            ["base_datetime", "levelist"],
        ),
        (
            {"variable_key": "param_level"},
            "param_level",
            ["r1000", "r850", "t1000", "t850"],
            ["date"],
        ),
        (
            {"extra_index_keys": "param_level"},
            "param_level",
            [
                "r1000",
                "r850",
                "t1000",
                "t850",
            ],
            ["date"],
        ),
        (
            {"remapping": {"param_level": "{param}_{level}"}},
            "param_level",
            ["r_1000", "r_850", "t_1000", "t_850"],
            ["date"],
        ),
        (
            {"variable_key": "shortName"},
            "shortName",
            ["r", "t"],
            ["date", "levelist"],
        ),
        (
            {"variable_key": "shortName", "drop_variables": ["r"]},
            "shortName",
            ["t"],
            ["date", "levelist"],
        ),
        (
            {"variable_key": "param_level", "drop_variables": ["r", "r1000"]},
            "param_level",
            ["r850", "t1000", "t850"],
            ["date"],
        ),
        # (
        #     {"use_level_per_type_dim": True},
        #     "param",
        #     ["r", "t"],
        #     {"date": ["20210101", "20210102"], "level_per_type": ["850pl", "1000pl"]},
        # ),
        (
            {"extra_index_keys": "level_and_type"},
            "param",
            ["r", "t"],
            {"date": ["20210101", "20210102"], "level_and_type": ["1000pl", "850pl"]},
        ),
    ],
)
def test_xr_dims_ds_date_lev(kwargs, variable_key, variables, dims):

    remapping = None
    if "remapping" in kwargs:
        remapping = dict(kwargs["remapping"])

    prof = MarsProfile(**kwargs)
    ds = load_wrapped_fieldlist(DS_DATE_LEV, prof, remapping=remapping)

    # ds.load(prof.index_keys)
    prof.update(ds, _attributes(ds))
    assert prof.variable_key == variable_key
    assert prof.variables == variables

    if isinstance(dims, list):
        assert prof.dim_keys == dims
    elif isinstance(dims, dict):
        assert len(prof.dim_keys) == len(dims)
        for k in prof.dim_keys:
            assert ds.index(k) == dims[k]
    else:
        raise ValueError(f"Unsupported dims: {dims}")


@pytest.mark.parametrize(
    "kwargs,variable_key,variables,dim_keys",
    [
        ({}, "param", ["2t", "msl", "r", "t"], ["date", "levelist", "levtype"]),
        # ({"base_datetime_dim": True}, "param", ["r", "t"], ["levelist"]),
        # ({"squeeze": False}, "param", ["r", "t"], ["time", "step", "levelist"]),
    ],
)
def test_xr_dims_ds_sfc_and_pl(kwargs, variable_key, variables, dim_keys):
    prof = MarsProfile(**kwargs)
    ds = load_wrapped_fieldlist(DS_DATE_SFC_PL, prof)
    prof.update(ds, _attributes(ds))
    assert prof.variable_key == variable_key
    assert prof.variables == variables
    assert prof.dim_keys == dim_keys
