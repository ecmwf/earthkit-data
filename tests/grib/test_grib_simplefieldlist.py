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

from earthkit.data import ArrayField
from earthkit.data import SimpleFieldList
from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file


def _check(ds, group):
    assert len(ds) == 6

    ref = [("t", 1000), ("u", 1000), ("v", 1000), ("t", 850), ("u", 850), ("v", 850)]

    assert ds.metadata(("param", "level")) == ref

    ref = [
        [("t", 1000), ("t", 850)],
        [("u", 1000), ("u", 850)],  #
        [("v", 1000), ("v", 850)],
    ]
    cnt = 0
    for i, f in enumerate(ds.group_by(group)):
        assert len(f) == 2
        assert f.metadata(("param", "level")) == ref[i]
        afl = f.to_fieldlist()
        assert afl is not f
        assert len(afl) == 2
        cnt += len(f)

    assert cnt == len(ds)


@pytest.mark.parametrize("group", ["param"])
def test_grib_simple_fl_1(group):
    ds_in = from_source("file", earthkit_examples_file("test6.grib"))

    ds = SimpleFieldList()
    for f in ds_in:
        ds.append(f)

    _check(ds, group)


@pytest.mark.parametrize("group", ["param"])
def test_grib_simple_fl_2(group):
    ds = from_source("file", earthkit_examples_file("test6.grib"))

    ds = SimpleFieldList([f for f in ds])

    _check(ds, group)


@pytest.mark.parametrize("group", ["param"])
def test_grib_simple_fl_3(group):
    ds_in = from_source("file", earthkit_examples_file("test6.grib"))

    ds = SimpleFieldList()
    for f in ds_in:
        ds.append(ArrayField(f.to_numpy(), f.metadata()))

    _check(ds, group)
