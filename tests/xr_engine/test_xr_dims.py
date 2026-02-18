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

import pandas as pd
import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file
from earthkit.data.xr_engine.profile import Profile

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import compare_coords  # noqa: E402
from xr_engine_fixtures import compare_dim_order  # noqa: E402
from xr_engine_fixtures import compare_dims  # noqa: E402
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


@pytest.mark.skip(reason="New field implementation does not allow using time without date")
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
            ["forecast_reference_time", "step", "levelist", "levtype"],
        ),
        (
            {"time_dim_mode": "raw", "variable_key": "param_level", "dim_name_from_role_name": False},
            "param_level",
            ["r1000", "r850", "t1000", "t850"],
            ["date", "time", "step", "levtype"],
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
            ["date", "time", "step", "levtype"],
        ),
        (
            {"time_dim_mode": "raw", "variable_key": "shortName", "dim_name_from_role_name": False},
            "shortName",
            ["r", "t"],
            ["date", "time", "step", "levelist", "levtype"],
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
            ["date", "time", "step", "levelist", "levtype"],
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
                "step",
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
                "step": [datetime.timedelta(hours=0)],
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
                "step": [datetime.timedelta(hours=0)],
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
                "step": [datetime.timedelta(hours=0)],
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
                "date": ["20210101", "20210102"],
                "time": ["12"],
                "step": [datetime.timedelta(hours=0)],
                "levelist": [850, 1000],
                "levtype": ["pl"],
            },
        ),
        (
            {
                "time_dim_mode": "raw",
                "ensure_dims": ["class", "step"],
                "dim_name_from_role_name": False,
            },
            "param",
            ["r", "t"],
            {
                "class": ["od"],
                "date": ["20210101", "20210102"],
                "time": ["12"],
                "step": [datetime.timedelta(hours=0)],
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
                "step": [datetime.timedelta(hours=0)],
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
            ["date", "time", "step", "levelist", "levtype"],
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
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
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
def test_xr_rename_dims(allow_holes, lazy_load, kwargs, dim_keys):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib"))
    ds = ds_ek.to_xarray(allow_holes=allow_holes, lazy_load=lazy_load, **kwargs)
    num = len(ds)

    dim_keys = dim_keys + ["latitude", "longitude"]
    assert len(ds) == num

    for v in ds:
        compare_dim_order(ds, dim_keys, v)


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "kwargs,dim_keys",
    [
        (
            {
                "profile": "mars",
                "fixed_dims": ["metadata.date", "metadata.time", "metadata.step", "metadata.level"],
            },
            ["date", "time", "step", "level"],
        ),
        (
            {
                "profile": "mars",
                "fixed_dims": ["metadata.level", "metadata.date", "metadata.time", "metadata.step"],
            },
            ["level", "date", "time", "step"],
        ),
        (
            {
                "profile": "mars",
                "fixed_dims": [
                    {"my_date": "metadata.date"},
                    ("my_time", "metadata.time"),
                    "metadata.step",
                    "metadata.level",
                ],
            },
            ["my_date", "my_time", "step", "level"],
        ),
        (
            {
                "profile": "mars",
                "fixed_dims": ["time.forecast_reference_time", "metadata.endStep", "metadata.level"],
            },
            ["forecast_reference_time", "endStep", "level"],
        ),
        (
            {
                "profile": "mars",
                "fixed_dims": [
                    "time.forecast_reference_time",
                    ("step", "metadata.endStep"),
                    "metadata.level",
                ],
            },
            ["forecast_reference_time", "step", "level"],
        ),
    ],
)
def test_xr_fixed_dims(allow_holes, lazy_load, kwargs, dim_keys):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib"))
    ds = ds_ek.to_xarray(allow_holes=allow_holes, lazy_load=lazy_load, **kwargs)
    num = len(ds)

    dim_keys = dim_keys + ["latitude", "longitude"]
    assert len(ds) == num

    for v in ds:
        compare_dim_order(ds, dim_keys, v)


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
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
                "drop_dims": "metadata.number",
                "time_dim_mode": "raw",
                "squeeze": False,
                "dim_name_from_role_name": False,
            },
            ["date", "time", "step_timedelta", "levelist", "levtype"],
        ),
        (
            {
                "profile": "mars",
                "drop_dims": ["metadata.levtype", "metadata.number"],
                "time_dim_mode": "raw",
                "squeeze": False,
                "dim_name_from_role_name": False,
            },
            ["date", "time", "step_timedelta", "levelist"],
        ),
    ],
)
def test_xr_drop_dims(allow_holes, lazy_load, kwargs, dim_keys):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib"))
    ds = ds_ek.to_xarray(allow_holes=allow_holes, lazy_load=lazy_load, **kwargs)
    num = len(ds)

    dim_keys = dim_keys + ["latitude", "longitude"]
    assert len(ds) == num

    for v in ds:
        compare_dim_order(ds, dim_keys, v)


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "path,sel,kwargs,coords,dims,var_attrs,global_attrs",
    [
        (
            "level/pl_small.grib",
            {
                "metadata.shortName": "t",
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 1200,
                "metadata.level": 500,
            },
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "level_dim_mode": "level_and_type",
                "dim_name_from_role_name": True,
                "squeeze": True,
                "ensure_dims": ["level_and_type", "forecast_reference_time"],
                "dims_as_attrs": ["number", "level_and_type"],
                "rename_attrs": {"number": "realisation"},
                "rename_dims": {"step": "STEP", "level_and_type": "LEVEL_AND_TYPE"},
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [pd.Timestamp("2024-06-03 12:00:00")],
                "STEP": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "LEVEL_AND_TYPE": ["500isobaricInhPa"],
            },
            {"forecast_reference_time": 1, "STEP": 2, "LEVEL_AND_TYPE": 1},
            {
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "K",
                    "typeOfLevel": "isobaricInhPa",
                    "realisation": 0,
                    "level_and_type": "500isobaricInhPa",
                }
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
        (
            "level/pl_small.grib",
            {
                "metadata.shortName": "t",
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 1200,
                "metadata.level": 500,
            },
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "remapping": {"my_level": "{metadata.level}__{metadata.typeOfLevel}"},
                "ensure_dims": ["my_level", "metadata.expver"],
                "dims_as_attrs": ["forecast_reference_time", "number"],
                "add_earthkit_attrs": False,
            },
            {
                "my_level": ["500__isobaricInhPa"],
                "expver": ["0001"],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
            },
            {"my_level": 1, "expver": 1, "step": 2},
            {
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "K",
                    "typeOfLevel": "isobaricInhPa",
                    "number": 0,
                    "forecast_reference_time": "2024-06-03T12:00:00",
                }
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
    ],
)
def test_xr_ensure_dims(allow_holes, lazy_load, path, sel, kwargs, coords, dims, var_attrs, global_attrs):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", path))
    if sel:
        ds0 = ds0.sel(**sel)
    ds = ds0.to_xarray(lazy_load=lazy_load, allow_holes=allow_holes, **kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    for v in var_attrs:
        assert ds[v].attrs == var_attrs[v]
    assert ds.attrs == global_attrs


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "path,sel,kwargs,coords,dims,var_attrs,global_attrs",
    [
        (
            "level/pl_small.grib",
            None,
            {
                "profile": "grib",
                "extra_dims": [{"exp_version": "metadata.expver"}],
                "squeeze": False,
                "add_earthkit_attrs": False,
            },
            {
                "exp_version": ["0001"],
                "number": [0],
                "forecast_reference_time": [
                    pd.Timestamp("2024-06-03 00:00:00"),
                    pd.Timestamp("2024-06-03 12:00:00"),
                    pd.Timestamp("2024-06-04 00:00:00"),
                    pd.Timestamp("2024-06-04 12:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "level": [500, 700],
                "level_type": ["isobaricInhPa"],
            },
            {
                "exp_version": 1,
                "number": 1,
                "forecast_reference_time": 4,
                "step": 2,
                "level": 2,
                "level_type": 1,
            },
            {
                "r": {
                    "standard_name": "relative_humidity",
                    "long_name": "Relative humidity",
                    "units": "%",
                    "typeOfLevel": "isobaricInhPa",
                },
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "K",
                    "typeOfLevel": "isobaricInhPa",
                },
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
        (
            "level/pl_small.grib",
            None,
            {
                "profile": "grib",
                "extra_dims": [{"exp_version": "metadata.expver"}],
                "squeeze": True,
                "ensure_dims": ["exp_version"],
                "add_earthkit_attrs": False,
            },
            {
                "exp_version": ["0001"],
                "forecast_reference_time": [
                    pd.Timestamp("2024-06-03 00:00:00"),
                    pd.Timestamp("2024-06-03 12:00:00"),
                    pd.Timestamp("2024-06-04 00:00:00"),
                    pd.Timestamp("2024-06-04 12:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "level": [500, 700],
            },
            {"exp_version": 1, "forecast_reference_time": 4, "step": 2, "level": 2},
            {
                "r": {
                    "standard_name": "relative_humidity",
                    "long_name": "Relative humidity",
                    "units": "%",
                    "typeOfLevel": "isobaricInhPa",
                },
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "K",
                    "typeOfLevel": "isobaricInhPa",
                },
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
        (
            "level/pl_small.grib",
            None,
            {
                "profile": "grib",
                "remapping": {"my_ver": "GRIB{metadata.edition}_ver{metadata.expver}"},
                "extra_dims": ["my_ver"],
                "squeeze": True,
                "ensure_dims": ["my_ver"],
                "add_earthkit_attrs": False,
            },
            {
                "my_ver": ["GRIB1_ver0001"],
                "forecast_reference_time": [
                    pd.Timestamp("2024-06-03 00:00:00"),
                    pd.Timestamp("2024-06-03 12:00:00"),
                    pd.Timestamp("2024-06-04 00:00:00"),
                    pd.Timestamp("2024-06-04 12:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "level": [500, 700],
            },
            {"my_ver": 1, "forecast_reference_time": 4, "step": 2, "level": 2},
            {
                "r": {
                    "standard_name": "relative_humidity",
                    "long_name": "Relative humidity",
                    "units": "%",
                    "typeOfLevel": "isobaricInhPa",
                },
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "K",
                    "typeOfLevel": "isobaricInhPa",
                },
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
        (
            "ens/quantiles_pd.grib",
            None,
            {
                "profile": "grib",
                "time_dim_mode": "valid_time",
                "extra_dims": "metadata.quantile",
                "drop_dims": "number",
                "dims_as_attrs": ["level", "level_type", "valid_time"],
                "variable_attrs": "parameter.units",
                "add_earthkit_attrs": False,
            },
            {
                "quantile": [
                    "10:10",
                    "1:10",
                    "1:3",
                    "1:5",
                    "2:10",
                    "2:3",
                    "2:5",
                    "3:10",
                    "3:3",
                    "3:5",
                    "4:10",
                    "4:5",
                    "5:10",
                    "5:5",
                    "6:10",
                    "7:10",
                    "8:10",
                    "9:10",
                ],
            },
            {"quantile": 18},
            {"2tp": {"units": "%", "valid_time": "2025-12-16T00:00:00", "level": 0, "level_type": "surface"}},
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
        (
            "wave_spectra.grib",
            None,
            {
                "profile": "grib",
                "time_dim_mode": "valid_time",
                "extra_dims": ["metadata.directionNumber", "metadata.frequencyNumber"],
                "squeeze": False,
                "add_earthkit_attrs": False,
            },
            {
                "directionNumber": [6, 12, 18, 24, 30, 36],
                "frequencyNumber": [1, 15, 29],
                "number": [0],
                "valid_time": [pd.Timestamp("2025-12-10 00:00:00")],
                "level": [0],
                "level_type": ["meanSea"],
            },
            {
                "directionNumber": 6,
                "frequencyNumber": 3,
                "number": 1,
                "valid_time": 1,
                "level": 1,
                "level_type": 1,
            },
            {
                "2dfd": {
                    "standard_name": "unknown",
                    "long_name": "2D wave spectra (single)",
                    "units": "m**2 s radian**-1",
                    "typeOfLevel": "meanSea",
                }
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
    ],
)
def test_xr_extra_dims(allow_holes, lazy_load, path, sel, kwargs, coords, dims, var_attrs, global_attrs):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", path))
    if sel:
        ds0 = ds0.sel(**sel)
    ds = ds0.to_xarray(lazy_load=lazy_load, allow_holes=allow_holes, **kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    for v in var_attrs:
        assert ds[v].attrs == var_attrs[v]
    assert ds.attrs == global_attrs


@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "path,sel,kwargs,coords,dims,var_attrs,global_attrs",
    [
        (
            "level/pl_sfc.grib1",
            {
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 0,
                "metadata.step": 0,
                "metadata.level": [0, 850],
            },
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "level_dim_mode": "level_per_type",
                "dim_name_from_role_name": True,
                "squeeze": True,
                "ensure_dims": "<level_per_type>",
                "variable_attrs": [],
                "global_attrs": [],
                "add_earthkit_attrs": False,
            },
            {
                "isobaricInhPa": [850],
                "surface": [0],
            },
            {"isobaricInhPa": 1, "surface": 1},
            {"2t": {}, "msl": {}, "r": {}, "t": {}, "u": {}, "v": {}, "z": {}},
            {},
        ),
        (
            "level/pl_sfc.grib1",
            None,
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "level_dim_mode": "level_per_type",
                "dim_name_from_role_name": True,
                "squeeze": False,
                "dims_as_attrs": ["<level_per_type>"],
                "variable_attrs": ["parameter.units"],
                "global_attrs": ["metadata.gridType"],
                "add_earthkit_attrs": False,
            },
            {
                "number": [0],
                "forecast_reference_time": [
                    pd.Timestamp("2024-06-03 00:00:00"),
                    pd.Timestamp("2024-06-03 12:00:00"),
                    pd.Timestamp("2024-06-04 00:00:00"),
                    pd.Timestamp("2024-06-04 12:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "isobaricInhPa": [300, 400, 500, 700, 850, 1000],
            },
            {"number": 1, "forecast_reference_time": 4, "step": 2, "isobaricInhPa": 6},
            {
                "2t": {"units": "K", "surface": 0},
                "msl": {"units": "Pa", "surface": 0},
                "r": {"units": "%"},
                "t": {"units": "K"},
                "u": {"units": "m s**-1"},
                "v": {"units": "m s**-1"},
                "z": {"units": "m**2 s**-2"},
            },
            {"gridType": "regular_ll"},
        ),
        (
            "level/pl_sfc.grib1",
            {
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 0,
                "metadata.step": 0,
                "metadata.level": [0, 850],
            },
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "level_dim_mode": "level_per_type",
                "dim_name_from_role_name": True,
                "squeeze": True,
                "dims_as_attrs": ["<level_per_type>"],
                "variable_attrs": [],
                "global_attrs": [],
                "rename_attrs": {"isobaricInhPa": "pl"},
                "add_earthkit_attrs": False,
            },
            {},
            {},
            {
                "2t": {"surface": 0},
                "msl": {"surface": 0},
                "r": {"pl": 850},
                "t": {"pl": 850},
                "u": {"pl": 850},
                "v": {"pl": 850},
                "z": {"pl": 850},
            },
            {},
        ),
        (
            "level/pl_sfc.grib1",
            {
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 0,
                "metadata.step": 0,
                "metadata.level": [0, 850],
            },
            {
                "profile": "grib",
                "time_dim_mode": "forecast",
                "level_dim_mode": "level_per_type",
                "dim_name_from_role_name": True,
                "squeeze": True,
                "ensure_dims": ["<level_per_type>"],
                "dims_as_attrs": ["<level_per_type>"],
                "variable_attrs": [],
                "global_attrs": [],
                "rename_dims": {"surface": "SURFACE"},
                "rename_attrs": {"isobaricInhPa": "pl"},
                "add_earthkit_attrs": False,
            },
            {
                "SURFACE": [0],
                "isobaricInhPa": [850],
            },
            {"SURFACE": 1, "isobaricInhPa": 1},
            {
                "2t": {"surface": 0},
                "msl": {"surface": 0},
                "r": {"pl": 850},
                "t": {"pl": 850},
                "u": {"pl": 850},
                "v": {"pl": 850},
                "z": {"pl": 850},
            },
            {},
        ),
    ],
)
def test_xr_level_per_type_dim(lazy_load, path, sel, kwargs, coords, dims, var_attrs, global_attrs):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", path))
    if sel:
        ds0 = ds0.sel(**sel)
    ds = ds0.to_xarray(lazy_load=lazy_load, **kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    for v in var_attrs:
        assert ds[v].attrs == var_attrs[v]
    assert ds.attrs == global_attrs


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "path,sel,idx,kwargs,coords,dims,var_attrs,global_attrs",
    [
        (
            "level/pl_small.grib",
            {
                "metadata.shortName": ["t", "r"],
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 1200,
                "metadata.step": 0,
                "metadata.level": [500, 700],
            },
            [0, 3],  # gets t @ 700hPa and r @ 500hPa
            {
                "profile": "grib",
                "ensure_dims": ["metadata.expver"],
                "dims_as_attrs": ["level"],
                "add_earthkit_attrs": False,
            },
            {
                "expver": ["0001"],
            },
            {"expver": 1},
            {
                "r": {
                    "standard_name": "relative_humidity",
                    "long_name": "Relative humidity",
                    "units": "%",
                    "typeOfLevel": "isobaricInhPa",
                    "level": 500,
                },
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "K",
                    "typeOfLevel": "isobaricInhPa",
                    "level": 700,
                },
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
        (
            "level/pl_small.grib",
            {
                "metadata.shortName": ["t", "r"],
                "metadata.dataDate": 20240603,
                "metadata.dataTime": 1200,
                "metadata.step": 0,
                "metadata.level": [500, 700],
            },
            [0, 3],  # gets t @ 700hPa and r @ 500hPa
            {
                "profile": "grib",
                "remapping": {"my_level": "{metadata.level}__{metadata.typeOfLevel}"},
                "extra_dims": ["my_level"],
                "ensure_dims": ["metadata.expver"],
                "dims_as_attrs": ["my_level"],
                "add_earthkit_attrs": False,
            },
            {
                "expver": ["0001"],
            },
            {"expver": 1},
            {
                "r": {
                    "standard_name": "relative_humidity",
                    "long_name": "Relative humidity",
                    "units": "%",
                    "typeOfLevel": "isobaricInhPa",
                    "my_level": "500__isobaricInhPa",
                },
                "t": {
                    "standard_name": "air_temperature",
                    "long_name": "Temperature",
                    "units": "K",
                    "typeOfLevel": "isobaricInhPa",
                    "my_level": "700__isobaricInhPa",
                },
            },
            {"Conventions": "CF-1.8", "institution": "ECMWF"},
        ),
    ],
)
def test_xr_dims_as_attrs(
    allow_holes, lazy_load, path, sel, idx, kwargs, coords, dims, var_attrs, global_attrs
):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", path))
    if sel:
        ds0 = ds0.sel(**sel)
    if idx:
        ds0 = ds0[idx]
    ds = ds0.to_xarray(lazy_load=lazy_load, allow_holes=allow_holes, **kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    for v in var_attrs:
        assert ds[v].attrs == var_attrs[v]
    assert ds.attrs == global_attrs


@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "path,sel,idx,kwargs,coords,dims,var_attrs,global_attrs",
    [
        (
            "level/aifs-sfc.grib",
            None,
            None,
            {
                "profile": None,
                "level_dim_mode": "level",
                "dims_as_attrs": ["level", "level_type"],
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [
                    pd.Timestamp("2025-12-12 00:00:00"),
                    pd.Timestamp("2025-12-12 06:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
            },
            {"forecast_reference_time": 2, "step": 2},
            {
                "10u": {"level": 10, "level_type": "heightAboveGround"},
                "2t": {"level": 2, "level_type": "heightAboveGround"},
                "msl": {"level": 0, "level_type": "meanSea"},
                "tcw": {"level": 0, "level_type": "entireAtmosphere"},
                "tp": {"level": 0, "level_type": "surface"},
            },
            {},
        ),
        (
            "level/aifs-pl_sfc.grib",
            None,
            None,
            {
                "profile": None,
                "level_dim_mode": "level",
                "dims_as_attrs": ["level", "level_type"],
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [
                    pd.Timestamp("2025-12-12 00:00:00"),
                    pd.Timestamp("2025-12-12 06:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "level": [500, 850, 1000],
            },
            {"forecast_reference_time": 2, "step": 2, "level": 3},
            {
                "10u": {"level": 10, "level_type": "heightAboveGround"},
                "2t": {"level": 2, "level_type": "heightAboveGround"},
                "msl": {"level": 0, "level_type": "meanSea"},
                "tcw": {"level": 0, "level_type": "entireAtmosphere"},
                "tp": {"level": 0, "level_type": "surface"},
                "z": {"level_type": "isobaricInhPa"},
            },
            {},
        ),
        (
            "level/aifs-sfc.grib",
            None,
            None,
            {
                "profile": None,
                "level_dim_mode": "level_and_type",
                "dims_as_attrs": ["level_and_type"],
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [
                    pd.Timestamp("2025-12-12 00:00:00"),
                    pd.Timestamp("2025-12-12 06:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
            },
            {"forecast_reference_time": 2, "step": 2},
            {
                "10u": {"level_and_type": "10heightAboveGround"},
                "2t": {"level_and_type": "2heightAboveGround"},
                "msl": {"level_and_type": "0meanSea"},
                "tcw": {"level_and_type": "0entireAtmosphere"},
                "tp": {"level_and_type": "0surface"},
            },
            {},
        ),
        (
            "level/aifs-pl_sfc.grib",
            None,
            None,
            {
                "profile": None,
                "level_dim_mode": "level_and_type",
                "dims_as_attrs": ["level_and_type"],
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [
                    pd.Timestamp("2025-12-12 00:00:00"),
                    pd.Timestamp("2025-12-12 06:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "level_and_type": ["1000isobaricInhPa", "500isobaricInhPa", "850isobaricInhPa"],
            },
            {"forecast_reference_time": 2, "step": 2, "level_and_type": 3},
            {
                "10u": {"level_and_type": "10heightAboveGround"},
                "2t": {"level_and_type": "2heightAboveGround"},
                "msl": {"level_and_type": "0meanSea"},
                "tcw": {"level_and_type": "0entireAtmosphere"},
                "tp": {"level_and_type": "0surface"},
                "z": {},
            },
            {},
        ),
        (
            "level/aifs-sfc.grib",
            None,
            None,
            {
                "profile": None,
                "level_dim_mode": "level_per_type",
                "dims_as_attrs": ["<level_per_type>"],
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [
                    pd.Timestamp("2025-12-12 00:00:00"),
                    pd.Timestamp("2025-12-12 06:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
            },
            {"forecast_reference_time": 2, "step": 2},
            {
                "10u": {"heightAboveGround": 10},
                "2t": {"heightAboveGround": 2},
                "msl": {"meanSea": 0},
                "tcw": {"entireAtmosphere": 0},
                "tp": {"surface": 0},
            },
            {},
        ),
        (
            "level/aifs-pl_sfc.grib",
            None,
            None,
            {
                "profile": None,
                "level_dim_mode": "level_per_type",
                "dims_as_attrs": ["<level_per_type>"],
                "add_earthkit_attrs": False,
            },
            {
                "forecast_reference_time": [
                    pd.Timestamp("2025-12-12 00:00:00"),
                    pd.Timestamp("2025-12-12 06:00:00"),
                ],
                "step": [pd.Timedelta("0 days 00:00:00"), pd.Timedelta("0 days 06:00:00")],
                "isobaricInhPa": [500, 850, 1000],
            },
            {"forecast_reference_time": 2, "step": 2, "isobaricInhPa": 3},
            {
                "10u": {"heightAboveGround": 10},
                "2t": {"heightAboveGround": 2},
                "msl": {"meanSea": 0},
                "tcw": {"entireAtmosphere": 0},
                "tp": {"surface": 0},
                "z": {},
            },
            {},
        ),
    ],
)
def test_xr_dims_as_attrs2(lazy_load, path, sel, idx, kwargs, coords, dims, var_attrs, global_attrs):
    ds0 = from_source("url", earthkit_remote_test_data_file("xr_engine", path))
    if sel:
        ds0 = ds0.sel(**sel)
    if idx:
        ds0 = ds0[idx]
    ds = ds0.to_xarray(lazy_load=lazy_load, **kwargs)
    compare_coords(ds, coords)
    compare_dims(ds, dims, sizes=True)

    for v in var_attrs:
        assert ds[v].attrs == var_attrs[v]
    assert ds.attrs == global_attrs
