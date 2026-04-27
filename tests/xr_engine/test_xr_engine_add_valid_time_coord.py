#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Tests for add_valid_time_coord=True using the aux_coords-based implementation."""

import numpy as np
import pytest

from earthkit.data import from_source

# Expected valid_time values for pl.grib with 4 forecast_reference_times x 2 steps
VALID_TIME_FRT_STEP = np.array(
    [
        ["2024-06-03T00:00:00", "2024-06-03T06:00:00"],
        ["2024-06-03T12:00:00", "2024-06-03T18:00:00"],
        ["2024-06-04T00:00:00", "2024-06-04T06:00:00"],
        ["2024-06-04T12:00:00", "2024-06-04T18:00:00"],
    ],
    dtype="datetime64[ns]",
)

# Expected valid_time values for date x time x step (2x2x2)
VALID_TIME_DATE_TIME_STEP = np.array(
    [
        [
            ["2024-06-03T00:00:00", "2024-06-03T06:00:00"],
            ["2024-06-03T12:00:00", "2024-06-03T18:00:00"],
        ],
        [
            ["2024-06-04T00:00:00", "2024-06-04T06:00:00"],
            ["2024-06-04T12:00:00", "2024-06-04T18:00:00"],
        ],
    ],
    dtype="datetime64[ns]",
)


@pytest.fixture(scope="session")
def pl_fl():
    return from_source("sample", "pl.grib").to_fieldlist()


# -------------------------------------------------------------------------
# dim_name_from_role_name=True vs False
# -------------------------------------------------------------------------


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize("dim_name_from_role_name", [True, False])
def test_dim_name_from_role_name(pl_fl, lazy_load, allow_holes, dim_name_from_role_name):
    """valid_time aux coord should work regardless of dim_name_from_role_name."""
    ds = pl_fl.to_xarray(
        profile="earthkit",
        add_valid_time_coord=True,
        dim_name_from_role_name=dim_name_from_role_name,
        lazy_load=lazy_load,
        allow_holes=allow_holes,
    )

    assert "valid_time" in ds.coords
    assert "valid_time" not in ds.sizes
    assert ds.coords["valid_time"].dims == ("forecast_reference_time", "step")
    assert ds.coords["valid_time"].shape == (4, 2)
    np.testing.assert_array_equal(ds.coords["valid_time"].values, VALID_TIME_FRT_STEP)


# -------------------------------------------------------------------------
# Different time_dims variants
# -------------------------------------------------------------------------


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_time_dims_date_time_step(pl_fl, lazy_load, allow_holes):
    """time_dims=['date', 'time', 'step'] produces 3D valid_time."""
    ds = pl_fl.to_xarray(
        profile="earthkit",
        time_dims=["date", "time", "step"],
        add_valid_time_coord=True,
        lazy_load=lazy_load,
        allow_holes=allow_holes,
    )

    assert "valid_time" in ds.coords
    assert "valid_time" not in ds.sizes
    assert ds.coords["valid_time"].dims == ("date", "time", "step")
    assert ds.coords["valid_time"].shape == (2, 2, 2)
    np.testing.assert_array_equal(ds.coords["valid_time"].values, VALID_TIME_DATE_TIME_STEP)


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_time_dims_valid_time_no_aux(pl_fl, lazy_load, allow_holes):
    """When time_dims='valid_time', valid_time is a dimension, not an aux coord."""
    ds = pl_fl.to_xarray(
        profile="earthkit",
        time_dims="valid_time",
        add_valid_time_coord=True,
        lazy_load=lazy_load,
        allow_holes=allow_holes,
    )

    # valid_time should be a dimension, not an auxiliary coordinate
    assert "valid_time" in ds.sizes
    assert ds.sizes["valid_time"] == 8


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_time_dims_frt_only(pl_fl, lazy_load, allow_holes):
    """time_dims=['forecast_reference_time'] with step squeezed out => 1D valid_time."""
    # Select single step to avoid step dimension
    fl_single_step = pl_fl.sel({"metadata.step": 0})
    ds = fl_single_step.to_xarray(
        profile="earthkit",
        time_dims=["forecast_reference_time"],
        add_valid_time_coord=True,
        lazy_load=lazy_load,
        allow_holes=allow_holes,
    )

    assert "valid_time" in ds.coords
    assert "valid_time" not in ds.sizes
    assert ds.coords["valid_time"].dims == ("forecast_reference_time",)
    assert ds.coords["valid_time"].shape == (4,)


# -------------------------------------------------------------------------
# Custom dim_roles (GRIB metadata keys)
# -------------------------------------------------------------------------


@pytest.mark.parametrize("dim_name_from_role_name", [True, False])
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_custom_dim_roles(pl_fl, lazy_load, allow_holes, dim_name_from_role_name):
    """Custom dim_roles mapping time roles to GRIB metadata keys."""
    ds = pl_fl.to_xarray(
        profile="earthkit",
        add_valid_time_coord=True,
        dim_roles={
            "forecast_reference_time": "metadata.base_datetime",
            "step": "metadata.endStep",
        },
        lazy_load=lazy_load,
        allow_holes=allow_holes,
        dim_name_from_role_name=dim_name_from_role_name,
    )

    assert "valid_time" in ds.coords
    assert "valid_time" not in ds.sizes
    assert (
        ds.coords["valid_time"].dims == ("forecast_reference_time", "step")
        if dim_name_from_role_name
        else ("metadata.base_datetime", "metadata.endStep")
    )
    assert ds.coords["valid_time"].shape == (4, 2)
    np.testing.assert_array_equal(ds.coords["valid_time"].values, VALID_TIME_FRT_STEP)


# -------------------------------------------------------------------------
# fixed_dims with mono_variable=True and False
# -------------------------------------------------------------------------


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_fixed_dims_mono_variable_true(pl_fl, lazy_load, allow_holes):
    """fixed_dims with mono_variable=True."""
    ds = pl_fl.to_xarray(
        fixed_dims=[
            "parameter.variable",
            "time.forecast_reference_time",
            "time.step",
            "vertical.level",
        ],
        mono_variable=True,
        add_valid_time_coord=True,
        lazy_load=lazy_load,
        allow_holes=allow_holes,
    )

    assert "valid_time" in ds.coords
    assert "valid_time" not in ds.sizes
    assert ds.coords["valid_time"].dims == ("forecast_reference_time", "step")
    assert ds.coords["valid_time"].shape == (4, 2)
    np.testing.assert_array_equal(ds.coords["valid_time"].values, VALID_TIME_FRT_STEP)


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_fixed_dims_mono_variable_false(pl_fl, lazy_load, allow_holes):
    """fixed_dims with mono_variable=False (default)."""
    ds = pl_fl.to_xarray(
        fixed_dims=[
            "time.forecast_reference_time",
            "metadata.endStep",
            "vertical.level",
        ],
        mono_variable=False,
        add_valid_time_coord=True,
        lazy_load=lazy_load,
        allow_holes=allow_holes,
    )

    assert "valid_time" in ds.coords
    assert "valid_time" not in ds.sizes
    assert ds.coords["valid_time"].dims == ("forecast_reference_time", "endStep")
    assert ds.coords["valid_time"].shape == (4, 2)
    np.testing.assert_array_equal(ds.coords["valid_time"].values, VALID_TIME_FRT_STEP)


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_fixed_dims_different_order(pl_fl, lazy_load, allow_holes):
    """fixed_dims with time dims in reversed order."""
    ds = pl_fl.to_xarray(
        fixed_dims=[
            "vertical.level",
            "metadata.endStep",
            "time.forecast_reference_time",
        ],
        add_valid_time_coord=True,
        lazy_load=lazy_load,
        allow_holes=allow_holes,
        decode_times=False,
        decode_timedelta=False,
    )

    assert "valid_time" in ds.coords
    assert "valid_time" not in ds.sizes
    # Dims should follow the fixed_dims order
    assert ds.coords["valid_time"].dims == ("endStep", "forecast_reference_time")
    assert ds.coords["valid_time"].shape == (2, 4)


# -------------------------------------------------------------------------
# Edge case: add_valid_time_coord=False should not add it
# -------------------------------------------------------------------------


@pytest.mark.parametrize("allow_holes", [False, True])
def test_add_valid_time_coord_false(pl_fl, allow_holes):
    """add_valid_time_coord=False should not add valid_time as aux coord."""
    ds = pl_fl.to_xarray(
        profile="earthkit",
        add_valid_time_coord=False,
        allow_holes=allow_holes,
        decode_times=False,
    )

    assert "valid_time" not in ds.coords
