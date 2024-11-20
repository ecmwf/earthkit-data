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
from earthkit.data.testing import earthkit_remote_test_data_file


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs",
    [
        {"profile": "mars", "time_dim_mode": "raw"},
        {"profile": "mars", "time_dim_mode": "forecast"},
        {"profile": "mars", "time_dim_mode": "raw", "decode_times": False, "decode_timedelta": False},
        {"profile": "mars", "time_dim_mode": "forecast", "decode_times": False, "decode_timedelta": False},
    ],
)
def test_xr_write_1(kwargs):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl.grib"))
    ds_ek = ds_ek.sel(param=["t", "r"], level=[500, 850])

    ref_t_vals = ds_ek.sel(param="t", step=6, level=500).to_numpy()
    ref_r_vals = ds_ek.sel(param="r", step=6, level=500).to_numpy()

    import xarray as xr

    xr.set_options(keep_attrs=True)

    ds = ds_ek.to_xarray(**kwargs)
    ds += 1

    # data-array
    r = ds["t"].earthkit.to_fieldlist()
    assert len(r) == 16
    assert r.index("shortName") == ["t"]
    assert np.allclose(ref_t_vals + 1.0, r.sel(param="t", step=6, level=500).to_numpy())

    ref_base = [
        "2024-06-03T00:00:00",
        "2024-06-03T00:00:00",
        "2024-06-03T00:00:00",
        "2024-06-03T00:00:00",
        "2024-06-03T12:00:00",
        "2024-06-03T12:00:00",
        "2024-06-03T12:00:00",
        "2024-06-03T12:00:00",
        "2024-06-04T00:00:00",
        "2024-06-04T00:00:00",
        "2024-06-04T00:00:00",
        "2024-06-04T00:00:00",
        "2024-06-04T12:00:00",
        "2024-06-04T12:00:00",
        "2024-06-04T12:00:00",
        "2024-06-04T12:00:00",
    ]

    ref_valid = [
        "2024-06-03T00:00:00",
        "2024-06-03T00:00:00",
        "2024-06-03T06:00:00",
        "2024-06-03T06:00:00",
        "2024-06-03T12:00:00",
        "2024-06-03T12:00:00",
        "2024-06-03T18:00:00",
        "2024-06-03T18:00:00",
        "2024-06-04T00:00:00",
        "2024-06-04T00:00:00",
        "2024-06-04T06:00:00",
        "2024-06-04T06:00:00",
        "2024-06-04T12:00:00",
        "2024-06-04T12:00:00",
        "2024-06-04T18:00:00",
        "2024-06-04T18:00:00",
    ]

    assert r.metadata("base_datetime") == ref_base
    assert r.metadata("valid_datetime") == ref_valid

    # dataset
    r = ds.earthkit.to_fieldlist()
    assert len(r) == 16 * 2
    assert set(r.index("shortName")) == set(["t", "r"])
    assert np.allclose(ref_t_vals + 1.0, r.sel(param="t", step=6, level=500).to_numpy())
    assert np.allclose(ref_r_vals + 1.0, r.sel(param="r", step=6, level=500).to_numpy())

    assert sorted(r.metadata("base_datetime")) == sorted(ds_ek.metadata("base_datetime"))
    assert sorted(r.metadata("valid_datetime")) == sorted(ds_ek.metadata("valid_datetime"))


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs",
    [
        {"profile": "mars", "time_dim_mode": "valid_time"},
        {"profile": "mars", "time_dim_mode": "valid_time", "decode_times": False, "decode_timedelta": False},
    ],
)
def test_xr_write_2(kwargs):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl.grib"))
    ds_ek = ds_ek.sel(date=20240603, time=0, param=["t", "r"], level=[500, 850])

    ref_t_vals = ds_ek.sel(param="t", step=6, level=500).to_numpy()
    ref_r_vals = ds_ek.sel(param="r", step=6, level=500).to_numpy()

    import xarray as xr

    xr.set_options(keep_attrs=True)

    # NOTE: the basetime and step are lost when using valid_time dim
    ds = ds_ek.to_xarray(**kwargs)
    ds += 1

    # TODO: currently base_time + step is lost when valid_time dim is used
    # Once we have a solution for this, we need to update the test

    # data-array
    r = ds["t"].earthkit.to_fieldlist()
    assert len(r) == 4
    assert r.index("shortName") == ["t"]
    assert r.index("step") == [0]
    assert np.allclose(ref_t_vals + 1.0, r.sel(param="t", time=600, level=500).to_numpy())

    ref_base = [
        "2024-06-03T00:00:00",
        "2024-06-03T00:00:00",
        "2024-06-03T06:00:00",
        "2024-06-03T06:00:00",
    ]

    assert r.metadata("base_datetime") == ref_base
    assert r.metadata("valid_datetime") == ref_base

    # # dataset
    r = ds.earthkit.to_fieldlist()
    assert len(r) == 4 * 2
    assert set(r.index("shortName")) == set(["t", "r"])
    assert np.allclose(ref_t_vals + 1.0, r.sel(param="t", time=600, level=500).to_numpy())
    assert np.allclose(ref_r_vals + 1.0, r.sel(param="r", time=600, level=500).to_numpy())

    assert sorted(r.metadata("base_datetime")) == sorted(ds_ek.metadata("valid_datetime"))
    assert sorted(r.metadata("valid_datetime")) == sorted(ds_ek.metadata("valid_datetime"))


@pytest.mark.cache
def test_xr_write_level_and_type():
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl.grib"))
    ds_ek = ds_ek.sel(date=20240603, time=0, param=["t", "r"], level=[500, 850])

    ref_t_vals = ds_ek.sel(param="t", step=6, level=500).to_numpy()
    ref_r_vals = ds_ek.sel(param="r", step=6, level=500).to_numpy()

    import xarray as xr

    xr.set_options(keep_attrs=True)

    ds = ds_ek.to_xarray(level_dim_mode="level_and_type")
    ds += 1

    # TODO: currently base_time + step is lost when valid_time dim is used
    # Once we have a solution for this, we need to update the test

    # data-array
    r = ds["t"].earthkit.to_fieldlist()
    assert len(r) == 4
    assert r.index("shortName") == ["t"]
    assert r.index("step") == [0, 6]
    assert np.allclose(ref_t_vals + 1.0, r.sel(param="t", step=6, level=500).to_numpy())

    ref_base = ["2024-06-03T00:00:00"] * 4
    ref_valid = [
        "2024-06-03T00:00:00",
        "2024-06-03T00:00:00",
        "2024-06-03T06:00:00",
        "2024-06-03T06:00:00",
    ]

    assert r.metadata("base_datetime") == ref_base
    assert r.metadata("valid_datetime") == ref_valid

    # dataset
    r = ds.earthkit.to_fieldlist()
    assert len(r) == 4 * 2
    assert set(r.index("shortName")) == set(["t", "r"])
    assert np.allclose(ref_t_vals + 1.0, r.sel(param="t", step=6, level=500).to_numpy())
    assert np.allclose(ref_r_vals + 1.0, r.sel(param="r", step=6, level=500).to_numpy())

    assert sorted(r.metadata("base_datetime")) == sorted(ds_ek.metadata("base_datetime"))
    assert sorted(r.metadata("valid_datetime")) == sorted(ds_ek.metadata("valid_datetime"))


@pytest.mark.cache
def test_xr_write_seasonal():
    ds_ek = from_source(
        "url",
        earthkit_remote_test_data_file("test-data/xr_engine/date/jma_seasonal_fc_ref_time_per_member.grib"),
    )
    ds_ek = ds_ek.sel(param="2t")
    assert len(ds_ek) == 60

    ds = ds_ek.to_xarray(
        time_dim_mode="forecast",
        dim_roles={"date": "indexingDate", "time": "indexingTime", "step": "forecastMonth"},
    )

    import xarray as xr

    xr.set_options(keep_attrs=True)
    ds += 1

    # dataset
    r = ds.earthkit.to_fieldlist()
    assert len(r) == 60

    assert sorted(r.metadata(["indexingDate", "indexingTime", "forecastMonth"])) == sorted(
        ds_ek.metadata(["indexingDate", "indexingTime", "forecastMonth"])
    )