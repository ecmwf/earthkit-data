#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_examples_file, earthkit_test_data_file


def test_hl_netcdf_single_core():
    ds = from_source("file", earthkit_examples_file("test.nc"))

    assert ds._TYPE_NAME == "NetCDF"
    assert ds.is_stream() is False
    assert "xarray" in ds.available_types
    assert "fieldlist" in ds.available_types

    a = ds.to_xarray()
    assert "t2m" in a.data_vars
    assert "msl" in a.data_vars
    assert a.t2m.shape == (8, 13)
    assert a.msl.shape == (8, 13)

    fl = ds.to_fieldlist()
    assert len(fl) == 2
    assert fl.get("parameter.variable") == ["t2m", "msl"]


def test_hl_netcdf_multi_core():
    paths = [earthkit_test_data_file("era5_2t_1.nc"), earthkit_test_data_file("era5_2t_2.nc")]
    ds = from_source("file", paths)

    assert ds._TYPE_NAME == "NetCDF"
    assert ds.is_stream() is False
    assert "xarray" in ds.available_types
    assert "fieldlist" in ds.available_types

    a = ds.to_xarray()
    assert "t2m" in a.data_vars
    assert a.t2m.shape == (2, 9, 18)

    fl = ds.to_fieldlist()
    assert len(fl) == 2
    assert fl.get("parameter.variable") == ["t2m", "t2m"]
