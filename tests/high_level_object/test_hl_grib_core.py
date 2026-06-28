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
from earthkit.data.utils.testing import earthkit_examples_file


def test_hl_grib_single_core():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    assert ds._TYPE_NAME == "GRIB"
    assert ds.is_stream() is False
    assert "fieldlist" in ds.available_types

    fl = ds.to_fieldlist()
    assert len(fl) == 2
    assert fl.get("parameter.variable") == ["2t", "msl"]

    fl1 = ds.to("fieldlist")
    assert len(fl1) == 2
    assert fl1.get("parameter.variable") == ["2t", "msl"]

    fl2 = ds.to(fl)
    assert len(fl2) == 2
    assert fl2.get("parameter.variable") == ["2t", "msl"]

    a = ds.to_xarray()
    assert "2t" in a.data_vars
    assert "msl" in a.data_vars
    assert a["2t"].shape == (8, 13)
    assert a["msl"].shape == (8, 13)

    v = ds.to_numpy()
    assert v.shape == (2, 8, 13)

    v = ds.to_array()
    assert v.shape == (2, 8, 13)


def test_hl_grib_stream_1():
    ds = from_source("file", earthkit_examples_file("test.grib"), stream=True)

    assert ds._TYPE_NAME == "StreamFieldList"
    assert ds.is_stream() is True
    assert "fieldlist" in ds.available_types

    fl = ds.to_fieldlist()
    cnt = 0
    for f in fl:
        assert f.get("parameter.variable") in ["2t", "msl"]
        cnt += 1

    assert cnt == 2


def test_hl_grib_stream_memory():
    ds = from_source("file", earthkit_examples_file("test.grib"), stream=True)

    assert ds._TYPE_NAME == "StreamFieldList"
    assert ds.is_stream() is True
    assert "fieldlist" in ds.available_types

    fl = ds.to_fieldlist(read_all=True)
    assert len(fl) == 2
    assert fl.get("parameter.variable") == ["2t", "msl"]


def test_hl_grib_multi_core():
    paths = [earthkit_examples_file("test.grib"), earthkit_examples_file("test4.grib")]
    ds = from_source("file", paths)

    assert ds._TYPE_NAME == "GRIB"
    assert ds.is_stream() is False
    assert "fieldlist" in ds.available_types

    fl = ds.to_fieldlist()
    assert len(fl) == 6
    assert fl.get("parameter.variable") == ["2t", "msl", "t", "z", "t", "z"]
    assert fl[0].shape == (8, 13)
    assert fl[2].shape == (181, 360)
