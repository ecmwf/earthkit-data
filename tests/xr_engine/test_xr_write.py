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
        {"profile": "mars", "time_dim_mode": "raw", "decode_time": False},
        {"profile": "mars", "time_dim_mode": "forecast", "decode_time": False},
    ],
)
def test_xr_write(kwargs):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl_regular_ll.grib"))

    ref_t_vals = ds_ek.sel(param="t", step=6, level=500).to_numpy()
    ref_r_vals = ds_ek.sel(param="r", step=6, level=500).to_numpy()

    import xarray as xr

    xr.set_options(keep_attrs=True)

    ds = ds_ek.to_xarray(**kwargs)
    ds += 1

    # data-array
    r = ds["t"].earthkit.to_fieldlist()
    assert len(r) == 48
    assert r.index("shortName") == ["t"]
    assert np.allclose(ref_t_vals + 1.0, r.sel(param="t", step=6, level=500).to_numpy())

    # dataset
    r = ds.earthkit.to_fieldlist()
    assert len(r) == 48 * 5
    assert set(r.index("shortName")) == set(["t", "r", "u", "v", "z"])
    assert np.allclose(ref_t_vals + 1.0, r.sel(param="t", step=6, level=500).to_numpy())
    assert np.allclose(ref_r_vals + 1.0, r.sel(param="r", step=6, level=500).to_numpy())
