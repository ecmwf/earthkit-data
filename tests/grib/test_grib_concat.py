#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os

import pytest

from earthkit.data import concat
from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.indexing.fieldlist import FieldList
from earthkit.data.testing import earthkit_examples_file


def _check_save_to_disk(ds, len_ref, meta_ref):
    # save to disk
    tmp = temp_file()
    ds.to_target("file", tmp.path)
    assert os.path.exists(tmp.path)
    r_tmp = from_source("file", tmp.path)
    assert len(r_tmp) == len_ref
    assert r_tmp.get("grib.shortName") == meta_ref
    r_tmp = None


@pytest.mark.parametrize("mode", ["concat", "multi"])
def test_grib_concat_core(mode):
    ds1 = from_source("file", earthkit_examples_file("test.grib"))
    ds2 = from_source("file", earthkit_examples_file("test6.grib"))

    if mode == "concat":
        ds = concat(ds1, ds2)
    else:
        ds = from_source("multi", ds1, ds2)

    # check metadata
    assert len(ds) == 8
    md = ds1.get("parameter.variable") + ds2.get("parameter.variable")
    assert ds.get("parameter.variable") == md

    # check slice
    r = ds[1]
    assert r.get("parameter.variable") == "msl"

    r = ds[1:3]
    assert len(r) == 2
    assert r.get("parameter.variable") == ["msl", "t"]
    assert r[0].get("parameter.variable") == "msl"
    assert r[1].get("parameter.variable") == "t"

    # check sel
    r = ds.sel({"parameter.variable": "2t"})
    assert len(r) == 1
    assert r.get("parameter.variable") == ["2t"]
    assert r[0].get("parameter.variable") == "2t"

    # check saving to disk
    _check_save_to_disk(ds, 8, md)


@pytest.mark.parametrize("mode", ["concat", "multi"])
def test_grib_concat_3a(mode):
    ds1 = from_source("file", earthkit_examples_file("test.grib"))
    ds2 = from_source("file", earthkit_examples_file("test6.grib"))
    ds3 = from_source("file", earthkit_examples_file("tuv_pl.grib"))
    md = ds1.get("parameter.variable") + ds2.get("parameter.variable") + ds3.get("parameter.variable")

    if mode == "concat":
        ds = concat(ds1, ds2)
        ds = concat(ds, ds3)
    else:
        ds = from_source("multi", ds1, ds2)
        ds = from_source("multi", ds, ds3)

    assert len(ds) == 26
    assert ds.get("parameter.variable") == md
    _check_save_to_disk(ds, 26, md)


@pytest.mark.parametrize("mode", ["concat", "multi"])
def test_grib_concat_3b(mode):
    ds1 = from_source("file", earthkit_examples_file("test.grib"))
    ds2 = from_source("file", earthkit_examples_file("test6.grib"))
    ds3 = from_source("file", earthkit_examples_file("tuv_pl.grib"))
    md = ds1.get("parameter.variable") + ds2.get("parameter.variable") + ds3.get("parameter.variable")

    if mode == "concat":
        ds = concat(ds1, ds2, ds3)
    else:
        ds = from_source("multi", ds1, ds2, ds3)

    assert len(ds) == 26
    assert ds.get("parameter.variable") == md
    _check_save_to_disk(ds, 26, md)


@pytest.mark.parametrize("mode", ["concat", "multi"])
def test_grib_concat_mixed(mode):
    ds1 = from_source("file", earthkit_examples_file("test.grib"))
    ds2 = ds1.to_fieldlist()
    md = ds1.get("parameter.variable") + ds2.get("parameter.variable")
    if mode == "concat":
        ds = concat(ds1, ds2)
    else:
        ds = from_source("multi", ds1, ds2)

    assert len(ds) == 4
    assert ds.get("parameter.variable") == md
    _check_save_to_disk(ds, 4, md)


def test_grib_from_empty_1():
    ds_e = FieldList()
    ds = from_source("file", earthkit_examples_file("test.grib"))
    md = ds.get("parameter.variable")

    ds1 = concat(ds_e, ds)
    assert id(ds1) == id(ds)
    assert len(ds1) == 2
    _check_save_to_disk(ds1, 2, md)


def test_grib_from_empty_2():
    ds_e = FieldList()
    ds = from_source("file", earthkit_examples_file("test.grib"))
    md = ds.get("parameter.variable")

    ds1 = concat(ds_e, ds)
    assert id(ds1) == id(ds)
    assert len(ds1) == 2
    _check_save_to_disk(ds1, 2, md)


def test_grib_from_empty_3():
    ds_e = FieldList()
    ds1 = from_source("file", earthkit_examples_file("test.grib"))
    ds2 = from_source("file", earthkit_examples_file("test6.grib"))
    md = ds1.metadata("param") + ds2.metadata("param")

    ds3 = concat(ds_e, ds1, ds2)
    assert len(ds3) == 8
    _check_save_to_disk(ds3, 8, md)


# See github issue #588
def test_grib_concat_large():
    ds_e = from_source("empty")
    ds1 = from_source("file", earthkit_examples_file("test.grib"))

    for _ in range(2000):
        # ds_e += ds1.sel(param="msl")
        ds_e = concat(ds_e, ds1.sel({"parameter.variable": "msl"}))

    assert len(ds_e) == 2000


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
