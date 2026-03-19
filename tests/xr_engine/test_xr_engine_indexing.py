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
