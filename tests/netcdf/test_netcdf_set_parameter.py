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

from earthkit.data.utils.testing import earthkit_examples_file, earthkit_test_data_file, load_nc_or_xr_source


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_set_parameter_1(mode):
    ds = load_nc_or_xr_source(earthkit_test_data_file("test_single.nc"), mode)
    f = ds[0]

    assert f.parameter.variable() == "t2m"
    assert f.parameter.standard_name() == "unknown"
    assert f.parameter.long_name() == "2 metre temperature"
    assert f.parameter.param() == "t2m"
    assert f.parameter.units() == "K"


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_set_parameter_2(mode):
    ds = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.grib"), mode)
    f = ds[0]

    assert f.parameter.variable() == "t"
    assert f.parameter.standard_name() == "air_temperature"
    assert f.parameter.long_name() == "Temperature"
    assert f.parameter.param() == "t"
    assert f.parameter.units() == "K"
