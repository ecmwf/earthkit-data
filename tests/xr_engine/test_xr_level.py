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
from earthkit.data.utils.xarray.profile import PROFILE_CONF

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import compare_dims  # noqa: E402


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs,dims",
    [
        (
            {"profile": "mars", "level_dim_mode": "level", "dim_name_from_role_name": False},
            {"levelist": [300, 400, 500, 700, 850, 1000]},
        ),
        (
            {"profile": "mars", "level_dim_mode": "level_and_type", "dim_name_from_role_name": False},
            {"level_and_type": ["1000pl", "300pl", "400pl", "500pl", "700pl", "850pl"]},
        ),
    ],
)
def test_xr_level_dim(kwargs, dims):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl.grib"))

    ds = ds_ek.to_xarray(**kwargs)
    compare_dims(ds, dims, order_ref_var="t")


@pytest.mark.cache
@pytest.mark.parametrize(
    "fname,kwargs,dims,levtype",
    [
        (
            "pl.grib",
            {"profile": "grib", "level_dim_mode": "level", "dim_name_from_role_name": False},
            {"level": [300, 400, 500, 700, 850, 1000]},
            "isobaricInhPa",
        ),
        (
            "pl_80_Pa.grib2",
            {
                "profile": "grib",
                "level_dim_mode": "level",
                "ensure_dims": "level",
                "dim_name_from_role_name": False,
            },
            {"level": [80]},
            "isobaricInPa",
        ),
        (
            "hpa_and_pa.grib",
            {
                "profile": "mars",
                "level_dim_mode": "level",
                "ensure_dims": "levelist",
                "dim_name_from_role_name": False,
            },
            {"levelist": [0.01, 0.1, 1]},
            "pl",
        ),
        (
            "hl_1000_m_asl.grib2",
            {
                "profile": "grib",
                "level_dim_mode": "level",
                "ensure_dims": "level",
                "dim_name_from_role_name": False,
            },
            {"level": [100, 1000, 2000, 3000]},
            "heightAboveSea",
        ),
        (
            "hl_1000_m_agr.grib2",
            {
                "profile": "grib",
                "level_dim_mode": "level",
                "ensure_dims": "level",
                "dim_name_from_role_name": False,
            },
            {"level": [500, 1000, 2500, 10000]},
            "heightAboveGround",
        ),
        (
            "pt_320_K.grib1",
            {
                "profile": "grib",
                "level_dim_mode": "level",
                "ensure_dims": "level",
                "dim_name_from_role_name": False,
            },
            {"level": [320]},
            "theta",
        ),
        (
            "pv_1500.grib1",
            {
                "profile": "grib",
                "level_dim_mode": "level",
                "ensure_dims": "level",
                "dim_name_from_role_name": False,
            },
            {"level": [1500]},
            "potentialVorticity",
        ),
        (
            "soil_7.grib1",
            {
                "profile": "grib",
                "level_dim_mode": "level",
                "ensure_dims": "level",
                "dim_name_from_role_name": False,
            },
            {"level": [7]},
            "depthBelowLand",
        ),
        (
            "sol_3.grib2",
            {
                "profile": "grib",
                "level_dim_mode": "level",
                "ensure_dims": "level",
                "dim_name_from_role_name": False,
            },
            {"level": [3]},
            "snowLayer",
        ),
        (
            "ml_77.grib2",
            {
                "profile": "grib",
                "level_dim_mode": "level",
                "ensure_dims": "level",
                "dim_name_from_role_name": False,
            },
            {"level": [77]},
            "hybrid",
        ),
        (
            "sfc.grib1",
            {
                "profile": "grib",
                "level_dim_mode": "level",
                "ensure_dims": "level",
                "dim_name_from_role_name": False,
            },
            {"level": [0]},
            "surface",
        ),
        # (
        #     "sfc.grib2",
        #     {"profile": "grib", "level_dim_mode": "level", "ensure_dims": "level"},
        #     {"level": [0]},
        #     "surface",
        # ),
        (
            "mean_sea_level_reduced_ll.grib1",
            {
                "profile": "grib",
                "level_dim_mode": "level",
                "ensure_dims": "level",
                "dim_name_from_role_name": False,
            },
            {"level": [0]},
            "meanSea",
        ),
        (
            "gen_vert_layer.grib",
            {
                "profile": "grib",
                "level_dim_mode": "level",
                "ensure_dims": "level",
                "dim_name_from_role_name": False,
            },
            {"level": [1]},
            "generalVerticalLayer",
        ),
        (
            "pl.grib",
            {"profile": "mars", "level_dim_mode": "level", "dim_name_from_role_name": False},
            {"levelist": [300, 400, 500, 700, 850, 1000]},
            "pl",
        ),
        (
            "pl_80_Pa.grib2",
            {
                "profile": "mars",
                "level_dim_mode": "level",
                "ensure_dims": "levelist",
                "dim_name_from_role_name": False,
            },
            {"levelist": [0.8]},
            "pl",
        ),
        (
            "pt_320_K.grib1",
            {
                "profile": "mars",
                "level_dim_mode": "level",
                "ensure_dims": "levelist",
                "dim_name_from_role_name": False,
            },
            {"levelist": [320]},
            "pt",
        ),
        (
            "pv_1500.grib1",
            {
                "profile": "mars",
                "level_dim_mode": "level",
                "ensure_dims": "levelist",
                "dim_name_from_role_name": False,
            },
            {"levelist": [1500]},
            "pv",
        ),
        (
            "sol_3.grib2",
            {
                "profile": "grib",
                "level_dim_mode": "level",
                "ensure_dims": "levelist",
                "dim_name_from_role_name": False,
            },
            {"levelist": [3]},
            "sol",
        ),
        (
            "hpa_and_pa.grib",
            {
                "profile": "mars",
                "level_dim_mode": "level",
                "ensure_dims": "levelist",
                "dim_name_from_role_name": False,
            },
            {"levelist": [0.01, 0.1, 1]},
            "pl",
        ),
    ],
)
def test_xr_level_attr(fname, kwargs, dims, levtype):
    ds_ek = from_source("url", earthkit_remote_test_data_file(f"test-data/xr_engine/level/{fname}"))

    ds = ds_ek.to_xarray(**kwargs)
    compare_dims(ds, dims)

    level_dim = next(iter(dims))
    ds.coords[level_dim].attrs == PROFILE_CONF.defaults["coord_attrs"][level_dim][levtype]
