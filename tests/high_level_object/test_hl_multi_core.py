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


def test_hl_multi_core():
    ds = from_source("file", [earthkit_test_data_file("binary_1"), earthkit_test_data_file("binary_2")], merger=False)

    assert ds._TYPE_NAME == "Multi"
    assert ds.is_stream() is False
    assert ds.available_types == []
    assert len(ds.path) == 2
    assert all(isinstance(p, str) for p in ds.path)
    assert ds.path[0].endswith("binary_1")
    assert ds.path[1].endswith("binary_2")


def test_hl_grib_multi_core_1():
    paths1 = [earthkit_examples_file("test.grib"), earthkit_examples_file("test4.grib")]
    d_a1 = from_source("file", paths1[0])
    d_a2 = from_source("file", paths1[1])
    d1 = from_source("multi", [d_a1, d_a2], merger="merge")

    paths2 = [earthkit_examples_file("test6.grib"), earthkit_examples_file("time_series.grib")]
    d_b1 = from_source("file", paths2[0])
    d2 = from_source("multi", [d_b1, from_source("file", paths2[1])], merger="merge")

    d = from_source("multi", [d1, d2])

    assert d._TYPE_NAME == "Multi"
    assert d.is_stream() is False
    assert "fieldlist" in d.available_types
    assert d.path == paths1 + paths2

    fl = d.to_fieldlist()
    assert len(fl) == 20
    assert fl[0].shape == (8, 13)
    assert fl[2].shape == (181, 360)

    items = [item for item in d]
    assert len(items) == 4
    assert all(item._TYPE_NAME == "GRIB" for item in items)


def test_hl_grib_multi_core_2():
    paths1 = [earthkit_examples_file("test.grib"), earthkit_examples_file("test4.grib")]
    d_a1 = from_source("file", paths1[0])
    d_a2 = from_source("file", paths1[1])
    d1 = from_source("multi", [d_a1, d_a2])

    paths2 = [earthkit_examples_file("test6.grib"), earthkit_examples_file("time_series.grib")]
    d_b1 = from_source("file", paths2[0])
    d2 = from_source("multi", [d_b1, from_source("file", paths2[1])])

    d = from_source("multi", [d1, d2])

    assert d._TYPE_NAME == "GRIB"
    assert d.is_stream() is False
    assert "fieldlist" in d.available_types
    assert d.path == paths1 + paths2

    fl = d.to_fieldlist()
    assert len(fl) == 20
    assert fl[0].shape == (8, 13)
    assert fl[2].shape == (181, 360)
