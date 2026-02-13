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

    assert f.vertical.level() == 0
    assert f.vertical.layer() is None
    assert f.vertical.level_type() == "surface"


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_vertical_2(fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)
    f = ds[0]

    assert f.vertical.level() == 1000
    assert f.vertical.level_type() == "pressure"
    assert f.vertical.units() == "hPa"
    assert f.vertical.abbreviation() == "pl"
    assert f.vertical.positive() == "down"


@pytest.mark.cache
@pytest.mark.parametrize(
    "fname,expected_values",
    [
        ("pl.grib", (1000, "pressure")),
        (
            "pl_80_Pa.grib2",
            (0.8, "pressure"),
        ),
        (
            "hpa_and_pa.grib",
            [(1, "pressure"), (0.1, "pressure"), (0.01, "pressure")],
        ),
        (
            "hl_1000_m_asl.grib2",
            [(100, "height_above_sea_level"), (1000, "height_above_sea_level")],
        ),
        (
            "hl_1000_m_agr.grib2",
            [(1000, "height_above_ground_level"), (500, "height_above_ground_level")],
        ),
        (
            "pt_320_K.grib1",
            (320, "potential_temperature"),
        ),
        (
            "pv_1500.grib1",
            (1500, "potential_vorticity"),
        ),
        (
            "soil_7.grib1",
            (7, "depth_below_ground_level"),
        ),
        (
            "sol_3.grib2",
            (3, "snow"),
        ),
        (
            "ml_77.grib2",
            (77, "hybrid"),
        ),
        (
            "sfc.grib1",
            (0, "surface"),
        ),
        (
            "sfc.grib2",
            (2, "height_above_ground_level"),
        ),
        (
            "mean_sea_level_reduced_ll.grib1",
            (0, "mean_sea"),
        ),
        (
            "gen_vert_layer.grib",
            (1, "general"),
        ),
    ],
)
def test_grib_vertical_core(fname, expected_values):
    ds = from_source("url", earthkit_remote_test_data_file(f"xr_engine/level/{fname}"))

    ref = expected_values
    if not isinstance(ref, list):
        ref = [ref]

    for i, (level, level_type) in enumerate(ref):
        f = ds[i]
        assert np.isclose(f.vertical.level(), level)
        assert f.vertical.level_type() == level_type
