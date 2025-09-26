#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import pytest
from earthkit.utils.array import _TORCH
from earthkit.utils.testing import NO_TORCH
from earthkit.utils.testing import check_array_type

from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file


@pytest.mark.skipif(NO_TORCH, reason="No pytorch installed")
@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_torch_core(allow_holes, lazy_load):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib"))

    ds = ds_ek.to_xarray(array_backend="torch", allow_holes=allow_holes, lazy_load=lazy_load)
    check_array_type(ds["t"].data, _TORCH)


@pytest.mark.skipif(NO_TORCH, reason="No pytorch installed")
@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_torch_core_compat(allow_holes, lazy_load):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib"))

    ds = ds_ek.to_xarray(array_module="torch", allow_holes=allow_holes, lazy_load=lazy_load)
    check_array_type(ds["t"].data, _TORCH)


@pytest.mark.skipif(NO_TORCH, reason="No pytorch installed")
@pytest.mark.cache
@pytest.mark.parametrize("allow_holes", [False, True])
@pytest.mark.parametrize("lazy_load", [True, False])
def test_xr_engine_torch_dtype(allow_holes, lazy_load):
    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib"))

    def _check_dtype(dtype, expected_dtype):
        ds = ds_ek.to_xarray(array_backend="torch", dtype=dtype, allow_holes=allow_holes, lazy_load=lazy_load)
        assert ds["t"].data.dtype == expected_dtype

    dtype = _TORCH.float32
    expected_dtype = _TORCH.float32
    _check_dtype(dtype, expected_dtype)

    dtype = "float32"
    expected_dtype = _TORCH.float32
    _check_dtype(dtype, expected_dtype)

    dtype = _TORCH.float64
    expected_dtype = _TORCH.float64
    _check_dtype(dtype, expected_dtype)

    dtype = "float64"
    expected_dtype = _TORCH.float64
    _check_dtype(dtype, expected_dtype)
