#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import numpy as np
import pytest
from grib_fixtures import (
    FL_TYPES,  # noqa: E402
    load_grib_data,  # noqa: E402
)

from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_remote_test_data_file


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_vertical_1(fl_type):
    ds, _ = load_grib_data("test_single.grib", fl_type, folder="data")
    f = ds[0]

    assert f.vertical.level() == 0
    assert f.vertical.layer() is None
    assert f.vertical.level_type() == "surface"
    assert f.vertical.number_of_levels() is None
    assert f.vertical.coefficients() is None
    assert f.get("vertical.level") == 0
    assert f.get("vertical.level_type") == "surface"
    assert f.get("vertical.layer") is None
    assert f.get("vertical.number_of_levels") is None
    assert f.get("vertical.coefficients") is None


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_vertical_2(fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)
    f = ds[0]

    assert f.vertical.level() == 1000
    assert f.vertical.level_type() == "pressure"
    assert f.vertical.units() == "hPa"
    assert f.vertical.abbreviation() == "pl"
    assert f.vertical.positive() == "down"
    assert f.vertical.number_of_levels() is None
    assert f.vertical.coefficients() is None


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
            [(100, "height_above_mean_sea_level"), (1000, "height_above_mean_sea_level")],
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
            (7, "depth_below_land_layer"),
        ),
        (
            "soil_7.grib2",
            (7, "depth_below_land_layer"),
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
        (
            "ocean_surface.grib2",
            (0, "ocean_surface"),
        ),
        ("depth_below_sea_layer.grib2", (0, "depth_below_sea_layer")),
        ("mixed_layer_depth_by_density.grib2", (0, "mixed_layer_depth_by_density")),
        ("isothermal.grib2", (287, "temperature")),
        ("medium_cloud_layer.grib2", (800, "medium_cloud_layer")),
        ("mixing_layer.grib2", (0, "mixing_layer")),
        ("water_surface_to_isothermal_ocean_layer.grib2", (0, "water_surface_to_isothermal_ocean_layer")),
        ("entire_lake.grib2", (0, "entire_lake")),
        ("sea_ice_layer.grib2", (1, "sea_ice_layer")),
        ("ice_top_on_water.grib2", (0, "ice_top_on_water")),
        ("entire_melt_pond.grib2", (0, "entire_melt_pond")),
        ("low_cloud_layer.grib2", (0, "low_cloud_layer")),
        ("most_unstable_parcel.grib2", (0, "most_unstable_parcel")),
        ("snow_layer_over_ice_on_water.grib2", (0, "snow_layer_over_ice_on_water")),
        ("stratosphere.grib2", (0, "stratosphere")),
        ("high_cloud_layer.grib2", (450, "high_cloud_layer")),
        ("soil_layer.grib2", (1, "soil_layer")),
        ("ocean_surface_to_bottom.grib2", (0, "ocean_surface_to_bottom")),
        ("lake_bottom.grib2", (0, "lake_bottom")),
        ("troposphere.grib2", (0, "troposphere")),
    ],
)
def test_grib_vertical_core(fname, expected_values):
    ds = from_source("url", earthkit_remote_test_data_file(f"xr_engine/level/{fname}")).to_fieldlist()

    ref = expected_values
    if not isinstance(ref, list):
        ref = [ref]

    for i, (level, level_type) in enumerate(ref):
        f = ds[i]
        assert np.isclose(f.vertical.level(), level)
        assert f.vertical.level_type() == level_type


@pytest.mark.cache
@pytest.mark.parametrize(
    "fname,expected_values",
    [
        ("depth_below_sea_layer.grib2", (0, 0, 300, "depth_below_sea_layer")),
    ],
)
def test_grib_vertical_layer(fname, expected_values):
    ds = from_source("url", earthkit_remote_test_data_file(f"xr_engine/level/{fname}")).to_fieldlist()

    ref = expected_values
    if not isinstance(ref, list):
        ref = [ref]

    for i, (level, bottom, top, level_type) in enumerate(ref):
        f = ds[i]
        assert np.isclose(f.vertical.level(), level)
        assert np.isclose(f.vertical.layer()[0], bottom)
        assert np.isclose(f.vertical.layer()[1], top)
        assert f.vertical.level_type() == level_type


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_vertical_hybrid(fl_type):
    ds, _ = load_grib_data("ml_data.grib", fl_type, folder="data")
    f = ds[0]

    assert f.vertical.level() == 1
    assert f.vertical.layer() is None
    assert f.vertical.level_type() == "hybrid"
    assert f.vertical.number_of_levels() == 137
    A, B = f.vertical.coefficients()
    assert len(A) == 138
    assert len(B) == 138
    assert np.allclose(
        A[:4],
        [
            0.0,
            2.000365,
            3.102241,
            4.666084,
        ],
    )
    assert np.allclose(B[:4], [0.0, 0.0, 0.0, 0.0])
    assert np.allclose(A[-4:], [22.835938, 3.757813, 0.0, 0.0])
    assert np.allclose(B[-4:], [0.9919840097, 0.9950025082, 0.9976301193, 1.0])

    assert f.vertical.coefficient_names() == ("A", "B")

    assert f.get("vertical.level") == 1
    assert f.get("vertical.level_type") == "hybrid"
    assert f.get("vertical.layer") is None
    assert f.get("vertical.number_of_levels") == 137
    A_get, B_get = f.get("vertical.coefficients")
    assert np.allclose(
        A_get[:4],
        [
            0.0,
            2.000365,
            3.102241,
            4.666084,
        ],
    )
    assert np.allclose(B_get[:4], [0.0, 0.0, 0.0, 0.0])
    assert np.allclose(A_get[-4:], [22.835938, 3.757813, 0.0, 0.0])
    assert np.allclose(B_get[-4:], [0.9919840097, 0.9950025082, 0.9976301193, 1.0])
