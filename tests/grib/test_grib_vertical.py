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

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_TYPES  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_vertical_1(fl_type):
    ds, _ = load_grib_data("test_single.grib", fl_type, folder="data")
    f = ds[0]

    assert f.level == 0
    assert f.level_type == "sfc"


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_vertical_2(fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)
    f = ds[0]

    assert f.level == 1000
    assert f.level_type == "pl"


@pytest.mark.cache
@pytest.mark.parametrize(
    "fname,expected_values",
    [
        ("pl.grib", (1000, "pl")),
        (
            "pl_80_Pa.grib2",
            (0.8, "pl"),
        ),
        (
            "hpa_and_pa.grib",
            [(1, "pl"), (0.1, "pl"), (0.01, "pl")],
        ),
        # (
        #     "hl_1000_m_asl.grib2",
        #     {
        #         "profile": "grib",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "level",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"level": [100, 1000, 2000, 3000]},
        #     "heightAboveSea",
        # ),
        # (
        #     "hl_1000_m_agr.grib2",
        #     {
        #         "profile": "grib",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "level",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"level": [500, 1000, 2500, 10000]},
        #     "heightAboveGround",
        # ),
        # (
        #     "pt_320_K.grib1",
        #     {
        #         "profile": "grib",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "level",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"level": [320]},
        #     "theta",
        # ),
        # (
        #     "pv_1500.grib1",
        #     {
        #         "profile": "grib",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "level",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"level": [1500]},
        #     "potentialVorticity",
        # ),
        # (
        #     "soil_7.grib1",
        #     {
        #         "profile": "grib",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "level",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"level": [7]},
        #     "depthBelowLand",
        # ),
        # (
        #     "sol_3.grib2",
        #     {
        #         "profile": "grib",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "level",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"level": [3]},
        #     "snowLayer",
        # ),
        # (
        #     "ml_77.grib2",
        #     {
        #         "profile": "grib",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "level",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"level": [77]},
        #     "hybrid",
        # ),
        # (
        #     "sfc.grib1",
        #     {
        #         "profile": "grib",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "level",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"level": [0]},
        #     "surface",
        # ),
        # # (
        # #     "sfc.grib2",
        # #     {"profile": "grib", "level_dim_mode": "level", "ensure_dims": "level"},
        # #     {"level": [0]},
        # #     "surface",
        # # ),
        # (
        #     "mean_sea_level_reduced_ll.grib1",
        #     {
        #         "profile": "grib",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "level",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"level": [0]},
        #     "meanSea",
        # ),
        # (
        #     "gen_vert_layer.grib",
        #     {
        #         "profile": "grib",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "level",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"level": [1]},
        #     "generalVerticalLayer",
        # ),
        # (
        #     "pl.grib",
        #     {"profile": "mars", "level_dim_mode": "level", "dim_name_from_role_name": False},
        #     {"levelist": [300, 400, 500, 700, 850, 1000]},
        #     "pl",
        # ),
        # (
        #     "pl_80_Pa.grib2",
        #     {
        #         "profile": "mars",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "levelist",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"levelist": [0.8]},
        #     "pl",
        # ),
        # (
        #     "pt_320_K.grib1",
        #     {
        #         "profile": "mars",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "levelist",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"levelist": [320]},
        #     "pt",
        # ),
        # (
        #     "pv_1500.grib1",
        #     {
        #         "profile": "mars",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "levelist",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"levelist": [1500]},
        #     "pv",
        # ),
        # (
        #     "sol_3.grib2",
        #     {
        #         "profile": "grib",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "levelist",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"levelist": [3]},
        #     "sol",
        # ),
        # (
        #     "hpa_and_pa.grib",
        #     {
        #         "profile": "mars",
        #         "level_dim_mode": "level",
        #         "ensure_dims": "levelist",
        #         "dim_name_from_role_name": False,
        #     },
        #     {"levelist": [0.01, 0.1, 1]},
        #     "pl",
        # ),
    ],
)
def test_grib_vertical_core(fname, expected_values):
    ds = from_source("url", earthkit_remote_test_data_file(f"xr_engine/level/{fname}"))

    ref = expected_values
    if not isinstance(ref, list):
        ref = [ref]

    for i, (level, level_type) in enumerate(ref):
        f = ds[i]
        assert np.isclose(f.level, level)
        assert f.level_type == level_type
