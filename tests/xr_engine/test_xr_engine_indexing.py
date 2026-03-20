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

from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_remote_test_data_file


@pytest.mark.cache
@pytest.mark.long_test
@pytest.mark.timeout(30)
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize(
    "kwargs",
    [
        {},
        {"chunks": "auto"},
        {"chunks": {"valid_time": 100}},
    ],
)
def test_xr_engine_daily_mean(allow_holes, kwargs):
    ds_ek = from_source(
        "url", earthkit_remote_test_data_file("era5-Europe-sfc-2m-temperature-3deg-2015-2017.grib")
    ).to_fieldlist()
    ds = ds_ek.to_xarray(time_dim_mode="valid_time", allow_holes=allow_holes, **kwargs)

    daily_mean_ds = ds.groupby("valid_time.dayofyear").mean()
    temp_variability_ds = daily_mean_ds.mean(["longitude", "latitude"]).std("dayofyear").compute()
    assert np.allclose(temp_variability_ds["2t"].values, 5.840784279794131)

    daily_anomaly_from_daily_mean_ds = (
        ds.resample({"valid_time": "24h"}).mean().groupby("valid_time.dayofyear")
        - ds.groupby("valid_time.dayofyear").mean()
    )
    max_abs_anomaly_ds = np.abs(daily_anomaly_from_daily_mean_ds).max().compute()
    assert np.allclose(max_abs_anomaly_ds["2t"].values, 22.586798350016267)

    monthly_mean_ds = ds.groupby("valid_time.month").mean()
    daily_anomaly_from_monthly_mean_ds = (
        ds.resample({"valid_time": "24h"}).mean().groupby("valid_time.month") - monthly_mean_ds
    )
    assert np.allclose(np.abs(daily_anomaly_from_monthly_mean_ds).max()["2t"].values, 28.98466590143022)


@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_groupby_forecast_valid_time(allow_holes, lazy_load):
    """Test that groupby on a 2-D valid_time coordinate works without error.

    Regression test for: xarray-based computations fail after latest code update
    in xarray engine. When ``time_dim_mode="forecast"`` is used the ``valid_time``
    coordinate is 2-D (it spans both ``forecast_time`` and ``step``). Calling
    ``groupby("valid_time.day")`` used to raise an ``IndexError`` because xarray
    internally stacks the lat/lon field dimensions using OUTER indexing (passing
    independent 1-D index arrays of different sizes), which numpy cannot handle
    without :func:`numpy.ix_`.
    """
    lats = [10.0, 0.0, -10.0]
    lons = [20.0, 40.0]
    n_pts = len(lats) * len(lons)

    prototype = {
        "geography": {"latitudes": lats, "longitudes": lons},
        "values": list(range(n_pts)),
    }

    # Two base dates, three steps -> valid_time spans multiple calendar days
    records = []
    for base_date in ["2018-08-01", "2018-08-02"]:
        for step in [0, 6, 12]:
            records.append(
                {
                    "parameter": {"variable": "t"},
                    "time": {"base_datetime": f"{base_date}T00:00:00", "step": step},
                    **prototype,
                }
            )

    ds_in = from_source("list-of-dicts", records).to_fieldlist()

    # add_valid_time_coord=True is not yet supported when allow_holes=True
    add_valid_time_coord = not allow_holes

    ds = ds_in.to_xarray(
        profile="earthkit",
        time_dim_mode="forecast",
        add_valid_time_coord=add_valid_time_coord,
        allow_holes=allow_holes,
        lazy_load=lazy_load,
    )

    if add_valid_time_coord:
        assert "valid_time" in ds.coords
        # valid_time is 2-D: (forecast_time, step)
        assert ds["valid_time"].ndim == 2

        # This groupby triggers xarray's internal stacking of lat/lon dimensions,
        # which previously caused an IndexError when outer-style index arrays with
        # incompatible shapes (3,) and (2,) were passed to field.to_array().
        grouped = ds.groupby("valid_time.day")
        result = grouped.mean().compute()
        assert result is not None
        assert "t" in result
