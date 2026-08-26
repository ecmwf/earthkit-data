#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Tests for CF-compliant daily climatology handling in the xarray engine."""

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_test_data_file


@pytest.fixture
def daily_clim_fl():
    """Load the ERA5 daily climatology temperature test data as a FieldList."""
    return from_source("file", earthkit_test_data_file("t-130-pl-em.grib")).to_fieldlist()


class TestDailyClimatologyXarray:
    """Tests for daily climatology conversion to xarray with CF attributes."""

    def test_day_of_year_dimension_present(self, daily_clim_fl):
        """day_of_year should appear as a dimension when specified in time_dims."""
        ds = daily_clim_fl.to_xarray(
            profile="earthkit",
            time_dims=["day_of_year"],
            ensure_dims=["day_of_year"],
        )
        assert "day_of_year" in ds.dims

    def test_day_of_year_coordinate_is_datetime64(self, daily_clim_fl):
        """day_of_year coordinate values should be datetime64 in reference year 2000."""
        ds = daily_clim_fl.to_xarray(
            profile="earthkit",
            time_dims=["day_of_year"],
            ensure_dims=["day_of_year"],
        )
        coord = ds.coords["day_of_year"]
        assert coord.dtype == np.dtype("datetime64[ns]")
        # DOY=1 → 2000-01-01
        assert coord.values[0] == np.datetime64("2000-01-01", "ns")

    def test_climatology_attribute(self, daily_clim_fl):
        """day_of_year coordinate should have CF 'climatology' attribute."""
        ds = daily_clim_fl.to_xarray(
            profile="earthkit",
            time_dims=["day_of_year"],
            ensure_dims=["day_of_year"],
        )
        coord = ds.coords["day_of_year"]
        assert "climatology" in coord.attrs
        assert coord.attrs["climatology"] == "climatology_bounds"

    def test_climatology_bounds_present(self, daily_clim_fl):
        """Climatology bounds auxiliary coordinate variable should exist."""
        ds = daily_clim_fl.to_xarray(
            profile="earthkit",
            time_dims=["day_of_year"],
            ensure_dims=["day_of_year"],
        )
        assert "climatology_bounds" in ds.coords

    def test_climatology_bounds_shape(self, daily_clim_fl):
        """Climatology bounds should have shape (day_of_year, 2)."""
        ds = daily_clim_fl.to_xarray(
            profile="earthkit",
            time_dims=["day_of_year"],
            ensure_dims=["day_of_year"],
        )
        bounds = ds.coords["climatology_bounds"]
        n_doy = ds.sizes["day_of_year"]
        assert bounds.shape == (n_doy, 2)

    def test_climatology_bounds_dimensions(self, daily_clim_fl):
        """Climatology bounds should have dims (day_of_year, nv)."""
        ds = daily_clim_fl.to_xarray(
            profile="earthkit",
            time_dims=["day_of_year"],
            ensure_dims=["day_of_year"],
        )
        bounds = ds.coords["climatology_bounds"]
        assert bounds.dims == ("day_of_year", "nv")

    def test_climatology_bounds_values_jan1(self, daily_clim_fl):
        """Bounds for DOY=1 (Jan 1) should span [2000-01-01, 2000-01-02)."""
        ds = daily_clim_fl.to_xarray(
            profile="earthkit",
            time_dims=["day_of_year"],
            ensure_dims=["day_of_year"],
        )
        bounds = ds.coords["climatology_bounds"].values
        # First day: start=2000-01-01, end=2000-01-02
        assert bounds[0, 0] == np.datetime64("2000-01-01", "ns")
        assert bounds[0, 1] == np.datetime64("2000-01-02", "ns")

    def test_climatology_bounds_dtype(self, daily_clim_fl):
        """Climatology bounds should be datetime64."""
        ds = daily_clim_fl.to_xarray(
            profile="earthkit",
            time_dims=["day_of_year"],
            ensure_dims=["day_of_year"],
        )
        bounds = ds.coords["climatology_bounds"]
        assert np.issubdtype(bounds.dtype, np.datetime64)

    def test_data_variable_has_day_of_year_dim(self, daily_clim_fl):
        """Data variables should have day_of_year as a dimension."""
        ds = daily_clim_fl.to_xarray(
            profile="earthkit",
            time_dims=["day_of_year"],
            ensure_dims=["day_of_year"],
        )
        assert "day_of_year" in ds["t"].dims

    def test_squeezed_no_day_of_year_dim(self, daily_clim_fl):
        """When squeeze=True and only 1 DOY value, dim is squeezed out."""
        ds = daily_clim_fl.to_xarray(
            profile="earthkit",
            time_dims=["day_of_year"],
            squeeze=True,
        )
        # With only 1 DOY value and squeeze=True (default), day_of_year is squeezed
        assert "day_of_year" not in ds.dims

    def test_other_time_dims_are_inactive(self, daily_clim_fl):
        """Standard time dims should not appear for climatology data."""
        ds = daily_clim_fl.to_xarray(
            profile="earthkit",
            time_dims=["day_of_year"],
            squeeze=False,
        )
        # Standard time dims should not be present
        assert "forecast_reference_time" not in ds.dims
        assert "step" not in ds.dims
        assert "valid_time" not in ds.dims

    def test_nv_dimension_exists(self, daily_clim_fl):
        """The 'nv' (number of vertices) dimension should exist for bounds."""
        ds = daily_clim_fl.to_xarray(
            profile="earthkit",
            time_dims=["day_of_year"],
            ensure_dims=["day_of_year"],
        )
        assert "nv" in ds.dims
        assert ds.sizes["nv"] == 2
