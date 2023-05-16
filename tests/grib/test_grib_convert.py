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


def test_grib_to_pandas():
    f = from_source("file", earthkit_test_data_file("test_single.grib"))

    # all points
    df = f.to_pandas()
    assert len(df) == 84
    cols = [
        "lat",
        "lon",
        "value",
        "datetime",
        "domain",
        "levtype",
        "date",
        "time",
        "step",
        "param",
        "class",
        "type",
        "stream",
        "expver",
    ]
    assert list(df.columns) == cols
    assert np.allclose(df["lat"][0:2], [90, 90])
    assert np.allclose(df["lon"][0:2], [0, 30])
    assert np.allclose(df["value"][0:2], [260.435608, 260.435608])

    # specific location
    df = f.to_pandas(latitude=90, longitude=30)
    assert len(df) == 1
    assert list(df.columns) == cols
    assert np.isclose(df["lat"][0], 90)
    assert np.isclose(df["lon"][0], 30)
    assert np.isclose(df["value"][0], 260.435608)
