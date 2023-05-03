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
from earthkit.data.testing import earthkit_test_data_file


def test_icon_to_xarray():
    # test the conversion to xarray for an icon (unstructured grid) grib file.
    g = from_source("file", earthkit_test_data_file("test_icon.grib"))
    ds = g.to_xarray()
    assert len(ds.data_vars) == 1
    # Dataset contains 9 levels and 9 grid points per level
    ref_levs = g.metadata("level")
    assert ds["pres"].sizes["generalVerticalLayer"] == len(ref_levs)
    assert ds["pres"].sizes["values"] == 6
