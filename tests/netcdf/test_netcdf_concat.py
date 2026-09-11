#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime

import pytest

from earthkit.data import concat
from earthkit.data.utils.testing import earthkit_test_data_file, load_nc_or_xr_source


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_concat_fieldlist_core(mode):
    fl1 = load_nc_or_xr_source(earthkit_test_data_file("era5_2t_1.nc"), mode)
    fl2 = load_nc_or_xr_source(earthkit_test_data_file("era5_2t_2.nc"), mode)
    fl = concat(fl1, fl2)

    assert len(fl) == 2
    md = fl1.get("parameter.variable") + fl2.get("parameter.variable")
    assert fl.get("parameter.variable") == md

    assert fl[0].get("time.base_datetime") == datetime.datetime(2021, 3, 1, 12, 0)
    assert fl[0].get("time.valid_datetime") == datetime.datetime(2021, 3, 1, 12, 0)
    assert fl[0].get("time.step") == datetime.timedelta(0)
    assert fl[1].get("time.base_datetime") == datetime.datetime(2021, 3, 2, 12, 0)
    assert fl[1].get("time.valid_datetime") == datetime.datetime(2021, 3, 2, 12, 0)
    assert fl[1].get("time.step") == datetime.timedelta(0)


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_concat_fieldlist_to_xarray(mode):
    fl1 = load_nc_or_xr_source(earthkit_test_data_file("era5_2t_1.nc"), mode)
    fl2 = load_nc_or_xr_source(earthkit_test_data_file("era5_2t_2.nc"), mode)
    fl = concat(fl1, fl2)

    assert len(fl) == 2

    import xarray as xr

    target = xr.merge([fl1.to_xarray(), fl2.to_xarray()])
    merged = fl.to_xarray()
    assert target.identical(merged)
