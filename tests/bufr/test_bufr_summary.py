#!/usr/bin/env python3

# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_remote_test_data_file


def test_bufr_ls_invalid_num():
    f = from_source("file", earthkit_examples_file("temp_10.bufr"))
    with pytest.raises(ValueError):
        f.ls(n=0)

    with pytest.raises(ValueError):
        f.ls(0)


def test_bufr_ls_num():
    f = from_source("file", earthkit_examples_file("temp_10.bufr"))

    # default keys

    # head
    df = f.ls(n=2)
    ref = {
        "edition": {0: 3, 1: 3},
        "type": {0: 2, 1: 2},
        "subtype": {0: 101, 1: 101},
        "c": {0: 98, 1: 98},
        "mv": {0: 13, 1: 13},
        "lv": {0: 1, 1: 1},
        "subsets": {0: 1, 1: 1},
        "compr": {0: 0, 1: 0},
        "typicalDate": {0: "20081208", 1: "20081208"},
        "typicalTime": {0: "120000", 1: "120000"},
        "ident": {0: "02836", 1: "01400"},
        "lat": {0: 67.37, 1: 56.9},
        "lon": {0: 26.63, 1: 3.35},
    }

    assert ref == df.to_dict()

    # t tail
    df = f.ls(-2)
    ref = {
        "edition": {0: 3, 1: 3},
        "type": {0: 2, 1: 2},
        "subtype": {0: 101, 1: 101},
        "c": {0: 98, 1: 98},
        "mv": {0: 13, 1: 13},
        "lv": {0: 1, 1: 1},
        "subsets": {0: 1, 1: 1},
        "compr": {0: 0, 1: 0},
        "typicalDate": {0: "20081208", 1: "20081208"},
        "typicalTime": {0: "120000", 1: "120000"},
        "ident": {0: "11035", 1: "02963"},
        "lat": {0: 48.25, 1: 60.82},
        "lon": {0: 16.37, 1: 23.5},
    }

    assert ref == df.to_dict()

    df = f.ls(-2)
    assert ref == df.to_dict()


def test_bufr_head_num():
    f = from_source("file", earthkit_examples_file("temp_10.bufr"))

    # default keys
    df = f.head(n=2)
    ref = {
        "edition": {0: 3, 1: 3},
        "type": {0: 2, 1: 2},
        "subtype": {0: 101, 1: 101},
        "c": {0: 98, 1: 98},
        "mv": {0: 13, 1: 13},
        "lv": {0: 1, 1: 1},
        "subsets": {0: 1, 1: 1},
        "compr": {0: 0, 1: 0},
        "typicalDate": {0: "20081208", 1: "20081208"},
        "typicalTime": {0: "120000", 1: "120000"},
        "ident": {0: "02836", 1: "01400"},
        "lat": {0: 67.37, 1: 56.9},
        "lon": {0: 26.63, 1: 3.35},
    }

    assert ref == df.to_dict()

    df = f.head(2)
    assert ref == df.to_dict()


def test_bufr_tail_num():
    f = from_source("file", earthkit_examples_file("temp_10.bufr"))

    # default keys
    df = f.tail(n=2)
    ref = {
        "edition": {0: 3, 1: 3},
        "type": {0: 2, 1: 2},
        "subtype": {0: 101, 1: 101},
        "c": {0: 98, 1: 98},
        "mv": {0: 13, 1: 13},
        "lv": {0: 1, 1: 1},
        "subsets": {0: 1, 1: 1},
        "compr": {0: 0, 1: 0},
        "typicalDate": {0: "20081208", 1: "20081208"},
        "typicalTime": {0: "120000", 1: "120000"},
        "ident": {0: "11035", 1: "02963"},
        "lat": {0: 48.25, 1: 60.82},
        "lon": {0: 16.37, 1: 23.5},
    }

    assert ref == df.to_dict()

    df = f.tail(2)
    assert ref == df.to_dict()


def test_bufr_dump():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr"))
    r = ds[0].dump()
    assert isinstance(r, dict)
    assert "header" in r
    assert "data" in r


@pytest.mark.parametrize("_kwargs,expected_val", [({"subset": 1}, 1), ({}, 1), ({"subset": 2}, 2)])
def test_bufr_dump_uncompressed(_kwargs, expected_val):
    ds = from_source(
        "url",
        earthkit_remote_test_data_file("test-data/synop_multi_subset_uncompressed.bufr"),
    )
    n = ds[0].subset_count()
    assert n == 12

    r = ds[0].dump(**_kwargs)
    assert isinstance(r, dict)
    assert "header" in r
    assert "data" in r
    assert r["data"][0] == dict(key="subsetNumber", value=expected_val, units=None)


@pytest.mark.parametrize("_kwargs", [{"subset": 0}, {"subset": None}])
def test_bufr_dump_uncompressed_full(_kwargs):
    ds = from_source(
        "url",
        earthkit_remote_test_data_file("test-data/synop_multi_subset_uncompressed.bufr"),
    )

    n = ds[0].subset_count()
    assert n == 12

    r = ds[0].dump(**_kwargs)
    assert isinstance(r, dict)
    assert "header" in r
    assert "data" in r
    d = r["data"]
    for i in range(n):
        assert d[i][0] == dict(key="subsetNumber", value=i + 1, units=None)


@pytest.mark.parametrize(
    "_kwargs, expected_val",
    [
        ({"subset": 0}, "[0, ...] (51 items)"),
        ({"subset": None}, "[0, ...] (51 items)"),
        ({"subset": 1}, "0 (51 items)"),
        ({}, "0 (51 items)"),
        ({"subset": 2}, "1 (51 items)"),
    ],
)
def test_bufr_dump_compressed(_kwargs, expected_val):
    ds = from_source(
        "url",
        earthkit_remote_test_data_file("test-data/ens_multi_subset_compressed.bufr"),
    )
    n = ds[0].subset_count()
    assert n == 51

    r = ds[0].dump(**_kwargs)
    assert isinstance(r, dict)
    assert "header" in r
    assert "data" in r
    assert r["data"][1] == dict(key="ensembleMemberNumber", value=expected_val, units="Numeric")


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
