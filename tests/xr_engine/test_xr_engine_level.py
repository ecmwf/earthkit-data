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
from earthkit.data.utils.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import compare_dims  # noqa: E402


def _get_level_type_attr(level_dim, levtype):
    from earthkit.data.field.component.level_type import get_level_type

    t = get_level_type(levtype)
    return {
        "standard_name": t.standard_name,
        "long_name": t.long_name,
        "units": t.units,
        "positive": t.positive,
    }


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
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
def test_xr_level_dim(allow_holes, lazy_load, kwargs, dims):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib")).to_fieldlist()

    ds = ds_ek.to_xarray(allow_holes=allow_holes, lazy_load=lazy_load, **kwargs)
    compare_dims(ds, dims, order_ref_var="t")


@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "fname,kwargs,dims,levtype",
    [
        (
            "pl.grib",
            {"level_dim_mode": "level", "dim_name_from_role_name": True},
            {"level": [300, 400, 500, 700, 850, 1000]},
            "pressure",
        ),
        (
            "pl.grib",
            {"level_dim_mode": "level", "dim_name_from_role_name": False},
            {"level": [300, 400, 500, 700, 850, 1000]},
            "pressure",
        ),
        (
            "pl_80_Pa.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [80]},
            "pressure",
        ),
        (
            "hl_1000_m_asl.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "metadata.level",
            },
            {"level": [100, 1000, 2000, 3000]},
            "height_above_mean_sea_level",
        ),
        (
            "hl_1000_m_agr.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "metadata.level",
            },
            {"level": [500, 1000, 2500, 10000]},
            "height_above_ground_level",
        ),
        (
            "pt_320_K.grib1",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [320]},
            "potential_temperature",
        ),
        (
            "pv_1500.grib1",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [1500]},
            "potential_vorticity",
        ),
        (
            "soil_7.grib1",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [7]},
            "depth_below_ground_level",
        ),
        (
            "sol_3.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [3]},
            "snow",
        ),
        (
            "ml_77.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [77]},
            "hybrid",
        ),
        (
            "sfc.grib1",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0]},
            "surface",
        ),
        (
            "t2m_2m_agr.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [2]},
            "height_above_ground_level",
        ),
        (
            "msl_mean_sea_level.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0]},
            "mean_sea",
        ),
        (
            "mean_sea_level_reduced_ll.grib1",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0]},
            "mean_sea",
        ),
        (
            "gen_vert_layer.grib",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [1]},
            "general",
        ),
        (
            "tcw_entire_atmosphere.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0]},
            "entire_atmosphere",
        ),
        (
            "ocean_surface.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0]},
            "ocean_surface",
        ),
    ],
)
def test_xr_engine_level_attr_grib(allow_holes, lazy_load, fname, kwargs, dims, levtype):
    ds_ek = from_source("url", earthkit_remote_test_data_file(f"xr_engine/level/{fname}")).to_fieldlist()

    ds = ds_ek.to_xarray(profile="grib", allow_holes=allow_holes, lazy_load=lazy_load, **kwargs)

    compare_dims(ds, dims)

    level_dim = next(iter(dims))
    assert ds.coords[level_dim].attrs == _get_level_type_attr(level_dim, levtype)


@pytest.mark.cache
@pytest.mark.parametrize(
    "fname,kwargs,dims,levtype",
    [
        (
            "pl.grib",
            {"level_dim_mode": "level", "dim_name_from_role_name": False},
            {"levelist": [300, 400, 500, 700, 850, 1000]},
            "pressure",
        ),
        (
            "pl.grib",
            {"level_dim_mode": "level", "dim_name_from_role_name": True},
            {"level": [300, 400, 500, 700, 850, 1000]},
            "pressure",
        ),
        (
            "pl_80_Pa.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0.8]},
            "pressure",
        ),
        (
            "hpa_and_pa.grib",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0.01, 0.1, 1]},
            "pressure",
        ),
        (
            "pt_320_K.grib1",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [320]},
            "potential_temperature",
        ),
        (
            "pv_1500.grib1",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [1500]},
            "potential_vorticity",
        ),
        (
            "sol_3.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [3]},
            "snow",
        ),
    ],
)
def test_xr_engine_level_attr_mars(fname, kwargs, dims, levtype):
    ds_ek = from_source("url", earthkit_remote_test_data_file(f"xr_engine/level/{fname}")).to_fieldlist()

    ds = ds_ek.to_xarray(profile="mars", allow_holes=False, lazy_load=True, **kwargs)

    compare_dims(ds, dims)

    level_dim = next(iter(dims))
    assert ds.coords[level_dim].attrs == _get_level_type_attr(level_dim, levtype)


@pytest.mark.cache
@pytest.mark.parametrize(
    "fname,kwargs,dims,levtype",
    [
        (
            "pl.grib",
            {"level_dim_mode": "level"},
            {"level": [300, 400, 500, 700, 850, 1000]},
            "pressure",
        ),
        (
            "pl_80_Pa.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0.8]},
            "pressure",
        ),
        (
            "hpa_and_pa.grib",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0.01, 0.1, 1]},
            "pressure",
        ),
        (
            "hl_1000_m_asl.grib2",
            {
                "level_dim_mode": "level",
            },
            {"level": [100, 1000, 2000, 3000]},
            "height_above_mean_sea_level",
        ),
        (
            "hl_1000_m_agr.grib2",
            {
                "level_dim_mode": "level",
            },
            {"level": [500, 1000, 2500, 10000]},
            "height_above_ground_level",
        ),
        (
            "pt_320_K.grib1",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [320]},
            "potential_temperature",
        ),
        (
            "pv_1500.grib1",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [1500]},
            "potential_vorticity",
        ),
        (
            "soil_7.grib1",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [7]},
            "depth_below_ground_level",
        ),
        (
            "sol_3.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [3]},
            "snow",
        ),
        (
            "ml_77.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [77]},
            "hybrid",
        ),
        (
            "sfc.grib1",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0]},
            "surface",
        ),
        (
            "t2m_2m_agr.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [2]},
            "height_above_ground_level",
        ),
        (
            "msl_mean_sea_level.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0]},
            "mean_sea",
        ),
        (
            "gen_vert_layer.grib",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [1]},
            "general",
        ),
        (
            "tcw_entire_atmosphere.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0]},
            "entire_atmosphere",
        ),
        (
            "ocean_surface.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0]},
            "ocean_surface",
        ),
        (
            "depth_below_sea_layer.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0]},
            "depth_below_sea_layer",
        ),
        (
            "mixed_layer_depth_by_density.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [0]},
            "mixed_layer_depth_by_density",
        ),
        (
            "isothermal.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [287]},
            "temperature",
        ),
        (
            "ice_layer_on_water.grib2",
            {
                "level_dim_mode": "level",
                "ensure_dims": "level",
            },
            {"level": [1]},
            "ice_layer_on_water",
        ),
    ],
)
def test_xr_engine_level_attr_earthkit(fname, kwargs, dims, levtype):
    ds_ek = from_source("url", earthkit_remote_test_data_file(f"xr_engine/level/{fname}")).to_fieldlist()
    ds = ds_ek.to_xarray(profile="earthkit", allow_holes=False, lazy_load=True, **kwargs)

    compare_dims(ds, dims)

    level_dim = next(iter(dims))
    assert ds.coords[level_dim].attrs == _get_level_type_attr(level_dim, levtype)


@pytest.mark.cache
@pytest.mark.parametrize(
    "fname,kwargs,dims,levtype",
    [
        (
            "sfc.grib2",
            {"level_dim_mode": "level_per_type", "squeeze": False},
            {"heightAboveGround": [2], "meanSea": [0]},
            ("height_above_ground_level", "mean_sea"),
        ),
    ],
)
def test_xr_engine_grib2_sfc_level_attr_grib(fname, kwargs, dims, levtype):
    ds_ek = from_source("url", earthkit_remote_test_data_file(f"xr_engine/level/{fname}")).to_fieldlist()
    ds = ds_ek.to_xarray(profile="grib", allow_holes=False, lazy_load=True, **kwargs)

    compare_dims(ds, dims)

    for level_dim, level_type_name in zip(dims.keys(), levtype):
        assert ds.coords[level_dim].attrs == _get_level_type_attr(level_dim, level_type_name)


@pytest.mark.cache
@pytest.mark.parametrize(
    "fname,kwargs,dims,levtype",
    [
        (
            "sfc.grib2",
            {"level_dim_mode": "level_per_type", "squeeze": False},
            {"height_above_ground_level": [2], "mean_sea": [0]},
            ("height_above_ground_level", "mean_sea"),
        ),
    ],
)
def test_xr_engine_grib2_sfc_level_attr_earthkit(fname, kwargs, dims, levtype):
    ds_ek = from_source("url", earthkit_remote_test_data_file(f"xr_engine/level/{fname}")).to_fieldlist()
    ds = ds_ek.to_xarray(profile="earthkit", allow_holes=False, lazy_load=True, **kwargs)

    compare_dims(ds, dims)

    for level_dim, level_type_name in zip(dims.keys(), levtype):
        assert ds.coords[level_dim].attrs == _get_level_type_attr(level_dim, level_type_name)
