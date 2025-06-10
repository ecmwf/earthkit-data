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
def test_xr_remapping_1():
    ds0 = from_source(
        "url", earthkit_remote_test_data_file("test-data/xr_engine/level/mixed_pl_ml_small.grib")
    )
    ds = ds0.to_xarray(variable_key="_k", remapping={"_k": "{param}_{levelist}_{levtype}"})

    data_vars = ["t_137_ml", "t_500_pl", "t_700_pl", "t_90_ml", "u_137_ml", "u_500_pl", "u_700_pl", "u_90_ml"]
    assert [v for v in ds.data_vars] == data_vars

    dims = {"forecast_reference_time": 4, "step": 2, "latitude": 19, "longitude": 36}
    compare_dims(ds, dims, sizes=True)


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,coords,dims",
    [
        (
            dict(
                dim_roles={"level": "_k"},
                level_dim_mode="level",
                remapping={"_k": "{levelist}_{levtype}"},
                dim_name_from_role_name=False,
            ),
            {"_k": ["500_pl", "700_pl"]},
            {"forecast_reference_time": 4, "step_timedelta": 2, "_k": 2, "latitude": 19, "longitude": 36},
        ),
        (
            dict(
                dim_roles={"level": "_k"},
                level_dim_mode="level",
                remapping={"_k": "{levelist}_{levtype}"},
                dim_name_from_role_name=True,
            ),
            {"level": ["500_pl", "700_pl"]},
            {"forecast_reference_time": 4, "step": 2, "level": 2, "latitude": 19, "longitude": 36},
        ),
        (
            dict(
                dim_roles={"level": "_k"},
                level_dim_mode="level",
                remapping={"_k": "{levelist}_{levtype}"},
                rename_dims={"level": "_k"},
                dim_name_from_role_name=True,
            ),
            {"_k": ["500_pl", "700_pl"]},
            {"forecast_reference_time": 4, "step": 2, "_k": 2, "latitude": 19, "longitude": 36},
        ),
    ],
)
def test_xr_remapping_2(kwargs, coords, dims):
    ds0 = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl_small.grib"))
    ds = ds0.to_xarray(**kwargs)

    data_vars = ["r", "t"]

    assert [v for v in ds.data_vars] == data_vars

    # coords = {"_k": ["500_pl", "700_pl"]}
    compare_coords(ds, coords)

    # dims = {"forecast_reference_time": 4, "step_timedelta": 2, "_k": 2, "latitude": 19, "longitude": 36}
    compare_dims(ds, dims, sizes=True)
