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
        ({}, "param", ["r", "t"], ["step_timedelta", "levelist"]),
        (
            {"time_dim_mode": "forecast", "dim_name_from_role_name": False},
            "param",
            ["r", "t"],
            ["step_timedelta", "levelist"],
        ),
        (
            {"squeeze": False, "time_dim_mode": "raw", "dim_name_from_role_name": False},
            "param",
            ["r", "t"],
            ["time", "step_timedelta", "levelist"],
        ),
    ],
)
def test_xr_dims_ds_lev(kwargs, var_key, variables, dim_keys):
    """Test for the internal profile/dimension object. Cannot use all the options since
    many tasks are performed elsewhere in the engine."""
    # TODO: consider removing this test
    prof = Profile.make("mars", **kwargs)
    ds = load_wrapped_fieldlist(DS_LEV, prof)
    # prof.update(ds, _attributes(ds))
    prof.update(ds)
    assert prof.variable.key == var_key
    assert prof.variable.variables == variables
    assert prof.dim_keys == dim_keys


@pytest.mark.parametrize(
    "kwargs,var_key,variables,dims",
    [
        (
            {"time_dim_mode": "forecast", "dim_name_from_role_name": False},
            "param",
            ["r", "t"],
            ["forecast_reference_time", "step_timedelta", "levelist", "levtype"],
        ),
        (
            {"time_dim_mode": "raw", "variable_key": "param_level", "dim_name_from_role_name": False},
            "param_level",
            ["r1000", "r850", "t1000", "t850"],
            ["date", "time", "step_timedelta", "levtype"],
        ),
        (
            {
                "time_dim_mode": "raw",
                "variable_key": "param_level",
                "remapping": {"param_level": "{param}_{level}"},
                "dim_name_from_role_name": False,
            },
            "param_level",
            ["r_1000", "r_850", "t_1000", "t_850"],
            ["date", "time", "step_timedelta", "levtype"],
        ),
        (
            {"time_dim_mode": "raw", "variable_key": "shortName", "dim_name_from_role_name": False},
            "shortName",
            ["r", "t"],
            ["date", "time", "step_timedelta", "levelist", "levtype"],
        ),
        (
            {
                "time_dim_mode": "raw",
                "variable_key": "shortName",
                "drop_variables": ["r"],
                "dim_name_from_role_name": False,
            },
            "shortName",
            ["t"],
            ["date", "time", "step_timedelta", "levelist", "levtype"],
        ),
        (
            {
                "time_dim_mode": "raw",
                "variable_key": "param_level",
                "drop_variables": ["r", "r1000"],
                "dim_name_from_role_name": False,
            },
            "param_level",
            ["r850", "t1000", "t850"],
            [
                "date",
                "time",
                "step_timedelta",
                "levtype",
            ],
        ),
        (
            {"time_dim_mode": "raw", "level_dim_mode": "level_and_type", "dim_name_from_role_name": False},
            "param",
            ["r", "t"],
            {
                "date": ["20210101", "20210102"],
                "time": ["12"],
                "step_timedelta": [datetime.timedelta(hours=0)],
                "level_and_type": ["1000pl", "850pl"],
            },
        ),
        (
            {"time_dim_mode": "raw", "extra_dims": "class", "dim_name_from_role_name": False},
            "param",
            ["r", "t"],
            {
                "class": ["od"],
                "date": ["20210101", "20210102"],
                "time": ["12"],
                "step_timedelta": [datetime.timedelta(hours=0)],
                "levelist": [850, 1000],
                "levtype": ["pl"],
            },
        ),
        (
            {"time_dim_mode": "raw", "ensure_dims": "class", "dim_name_from_role_name": False},
            "param",
            ["r", "t"],
            {
                "class": ["od"],
                "date": ["20210101", "20210102"],
                "time": ["12"],
                "step_timedelta": [datetime.timedelta(hours=0)],
                "levelist": [850, 1000],
                "levtype": ["pl"],
            },
        ),
        (
            {"time_dim_mode": "raw", "ensure_dims": ["class", "step"], "dim_name_from_role_name": False},
            "param",
            ["r", "t"],
            {
                "class": ["od"],
                "step": [0],
                "date": ["20210101", "20210102"],
                "time": ["12"],
                "step_timedelta": [datetime.timedelta(hours=0)],
                "levelist": [850, 1000],
                "levtype": ["pl"],
            },
        ),
        (
            {
                "time_dim_mode": "raw",
                "ensure_dims": ["class", "step_timedelta"],
                "dim_name_from_role_name": False,
            },
            "param",
            ["r", "t"],
            {
                "class": ["od"],
                "date": ["20210101", "20210102"],
                "time": ["12"],
                "step_timedelta": [datetime.timedelta(hours=0)],
                "levelist": [850, 1000],
                "levtype": ["pl"],
            },
        ),
        (
            {
                "time_dim_mode": "raw",
                "extra_dims": "class",
                "squeeze": False,
                "dim_name_from_role_name": False,
            },
            "param",
            ["r", "t"],
            {
                "class": ["od"],
                "date": ["20210101", "20210102"],
                "time": ["12"],
                "step_timedelta": [datetime.timedelta(hours=0)],
                "levelist": [850, 1000],
                "levtype": ["pl"],
            },
        ),
    ],
)
def test_xr_dims_ds_date_lev(kwargs, var_key, variables, dims):
    """Test for the internal profile/dimension object. Cannot use all the options since
    many tasks are performed elsewhere in the engine."""
    # TODO: consider removing this test

    prof = Profile.make("mars", **kwargs)
    ds = load_wrapped_fieldlist(DS_DATE_LEV, prof, remapping=prof.remapping.build())

    # print("remapping", prof.remapping.build())
    # print(f"ds: {ds.indices()}")

    # ds.load(prof.index_keys)
    # prof.update(ds, _attributes(ds))
    prof.update(ds)
    assert prof.variable.key == var_key
    assert prof.variable.variables == variables

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
            ["date", "time", "step_timedelta", "levelist", "levtype"],
        ),
        # ({"base_datetime_dim": True}, "param", ["r", "t"], ["levelist", "levtype"]),
        # ({"squeeze": False}, "param", ["r", "t"], ["time", "step", "levelist", "levtype"]),
    ],
)
def test_xr_dims_ds_sfc_and_pl(kwargs, var_key, variables, dim_keys):
    """Test for the internal profile/dimension object. Cannot use all the options since
    many tasks are performed elsewhere in the engine."""
    # TODO: consider removing this test
    prof = Profile.make("mars", **kwargs)
    ds = load_wrapped_fieldlist(DS_DATE_SFC_PL, prof)
    # prof.update(ds, _attributes(ds))
    prof.update(ds)
    assert prof.variable.key == var_key
    assert prof.variable.variables == variables
    assert prof.dim_keys == dim_keys


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dim_keys",
    [
        (
            {
                "profile": "mars",
                "time_dim_mode": "raw",
                "rename_dims": {"levelist": "zz"},
                "dim_name_from_role_name": False,
            },
            ["date", "time", "step_timedelta", "zz"],
        ),
        (
            {
                "profile": "mars",
                "time_dim_mode": "raw",
                "rename_dims": {"level": "zz"},
            },
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


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dim_keys",
    [
        (
            {
                "profile": "mars",
                "fixed_dims": ["date", "time", "step", "level"],
            },
            ["date", "time", "step", "level"],
        ),
        (
            {
                "profile": "mars",
                "fixed_dims": ["level", "date", "time", "step"],
            },
            ["level", "date", "time", "step"],
        ),
        (
            {
                "profile": "mars",
                "fixed_dims": [{"my_date": "date"}, ("my_time", "time"), "step", "level"],
            },
            ["my_date", "my_time", "step", "level"],
        ),
        (
            {
                "profile": "mars",
                "fixed_dims": ["forecast_reference_time", "endStep", "level"],
            },
            ["forecast_reference_time", "endStep", "level"],
        ),
        (
            {
                "profile": "mars",
                "fixed_dims": ["forecast_reference_time", ("step", "endStep"), "level"],
            },
            ["forecast_reference_time", "step", "level"],
        ),
    ],
)
def test_xr_fixed_dims(kwargs, dim_keys):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl.grib"))
    ds = ds_ek.to_xarray(**kwargs)
    num = len(ds)

    dim_keys = dim_keys + ["latitude", "longitude"]
    assert len(ds) == num

    for v in ds:
        compare_dim_order(ds, dim_keys, v)


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dim_keys",
    [
        (
            {
                "profile": "mars",
                "drop_dims": "number",
                "time_dim_mode": "raw",
                "squeeze": False,
                "dim_name_from_role_name": True,
            },
            ["date", "time", "step", "level", "level_type"],
        ),
        (
            {
                "profile": "mars",
                "drop_dims": ["level_type", "number"],
                "time_dim_mode": "raw",
                "squeeze": False,
                "dim_name_from_role_name": True,
            },
            ["date", "time", "step", "level"],
        ),
        (
            {
                "profile": "mars",
                "drop_dims": "number",
                "time_dim_mode": "raw",
                "squeeze": False,
                "dim_name_from_role_name": False,
            },
            ["date", "time", "step_timedelta", "levelist", "levtype"],
        ),
        (
            {
                "profile": "mars",
                "drop_dims": ["levtype", "number"],
                "time_dim_mode": "raw",
                "squeeze": False,
                "dim_name_from_role_name": False,
            },
            ["date", "time", "step_timedelta", "levelist"],
        ),
    ],
)
def test_xr_drop_dims(kwargs, dim_keys):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl.grib"))
    ds = ds_ek.to_xarray(**kwargs)
    num = len(ds)

    dim_keys = dim_keys + ["latitude", "longitude"]
    assert len(ds) == num

    for v in ds:
        compare_dim_order(ds, dim_keys, v)
