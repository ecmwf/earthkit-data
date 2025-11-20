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
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_test_data_file


def test_netcdf_vertical_1():
    ds = from_source("file", earthkit_test_data_file("test_single.nc"))
    f = ds[0]

    assert f.level == 0
    assert f.vertical.level == 0
    assert f.vertical_level == 0
    assert f.layer is None
    assert f.vertical.layer is None
    assert f.vertical_layer is None
    assert f.vertical.type == "surface"
    assert f.vertical_type == "surface"


def test_netcdf_vertical_2():
    ds = from_source("file", earthkit_examples_file("tuv_pl.nc"))
    f = ds[0]

    assert f.level == 1000
    assert f.vertical.type == "pressure"
    assert f.vertical.units == "hPa"
    assert f.vertical.abbreviation == "pl"
    assert f.vertical.positive == "down"
    assert f.vertical_units == "hPa"
    assert f.vertical_abbreviation == "pl"
    assert f.vertical_positive == "down"
