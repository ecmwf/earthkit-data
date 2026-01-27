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

from earthkit.data import concat
from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file


def test_empty_source_len():
    ds = from_source("empty")
    assert len(ds) == 0


def test_empty_source_concat1():
    ds = from_source("empty")
    assert len(ds) == 0

    ds1 = from_source("file", earthkit_examples_file("test.grib"))

    ds2 = concat(ds, ds1)
    assert len(ds2) == 2
    meta = ds2.get("parameter.variable")
    assert meta == ["2t", "msl"]


def test_empty_source_concat2():
    ds = from_source("empty")
    assert len(ds) == 0

    ds1 = from_source("file", earthkit_examples_file("test.grib"))

    ds = concat(ds1, ds)
    assert len(ds) == 2
    meta = ds.get("parameter.variable")
    assert meta == ["2t", "msl"]


@pytest.mark.skip("Currently fails because of += is not implemented")
def test_empty_source_concat3():
    ds = from_source("empty")
    assert len(ds) == 0

    ds1 = from_source("file", earthkit_examples_file("test.grib"))

    ds += ds1
    assert len(ds) == 2
    meta = ds.get("variable")
    assert meta == ["2t", "msl"]


def test_empty_source_iterate():
    ds = from_source("empty")
    for _ in ds:
        assert False, "Empty source should not iterate"
