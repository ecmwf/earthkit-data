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
import pytest

from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_examples_file


@pytest.mark.parametrize(
    "index,expected_meta",
    [
        (0, [2, "02836"]),
        (2, [2, "01415"]),
        (-1, [2, "02963"]),
        (-5, [2, "01241"]),
    ],
)
def test_bufr_single_index(index, expected_meta):
    ds = from_source("file", earthkit_examples_file("temp_10.bufr")).to_featurelist()

    r = ds[index]
    assert r.get(["dataCategory", "ident"]) == expected_meta


def test_grib_bufr_index_bad():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr")).to_featurelist()
    with pytest.raises(IndexError):
        ds[27]


@pytest.mark.parametrize(
    "indexes,expected_meta",
    [
        (slice(0, 4), [[2, "02836"], [2, "01400"], [2, "01415"], [2, "01001"]]),
        (slice(None, 4), [[2, "02836"], [2, "01400"], [2, "01415"], [2, "01001"]]),
        (slice(2, 9, 2), [[2, "01415"], [2, "01152"], [2, "03953"], [2, "11035"]]),
        (slice(8, 1, -2), [[2, "11035"], [2, "03953"], [2, "01152"], [2, "01415"]]),
        (slice(6, None), [[2, "03953"], [2, "11747"], [2, "11035"], [2, "02963"]]),
    ],
)
def test_bufr_slice_single_file(indexes, expected_meta):
    ds = from_source("file", earthkit_examples_file("temp_10.bufr")).to_featurelist()
    r = ds[indexes]
    assert len(r) == 4
    assert r.get(["dataCategory", "ident"]) == expected_meta
    # check the original featurelist
    assert len(ds) == 10
    assert ds.get("dataCategory") == [2] * 10


@pytest.mark.parametrize(
    "indexes,expected_meta",
    [
        (slice(1, 4), [[2, "01400"], [2, "01415"], [2, "01001"]]),
        (slice(7, 13, 2), [[2, "11747"], [2, "02963"], [0, "89514"]]),
        (slice(11, 6, -2), [[0, "89514"], [2, "02963"], [2, "11747"]]),
        # (slice(3, 6), [["z", 500], ["t", 850], ["z", 850]]),
    ],
)
def test_bufr_slice_multi_file(indexes, expected_meta):
    ds = from_source(
        "file",
        [earthkit_examples_file("temp_10.bufr"), earthkit_examples_file("synop_10.bufr")],
    ).to_featurelist()
    r = ds[indexes]
    assert len(r) == 3
    assert r.get(["dataCategory", "ident"]) == expected_meta
    # check the original featurelist
    assert len(ds) == 20


@pytest.mark.parametrize(
    "indexes1,indexes2",
    [
        (np.array([1, 5, 9]), np.array([1, 2])),
        ([1, 5, 9], [1, 2]),
        ((1, 5, 9), (1, 2)),
    ],
)
def test_bufr_array_indexing(indexes1, indexes2):
    ds = from_source("file", earthkit_examples_file("temp_10.bufr")).to_featurelist()

    r = ds[indexes1]
    assert len(r) == 3
    assert r.get("ident") == ["01400", "01241", "02963"]

    r1 = r[indexes2]
    assert len(r1) == 2
    assert r1.get("ident") == ["01241", "02963"]


def test_bufr_featurelist_iterator():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr")).to_featurelist()
    sn = ds.get("ident")
    assert len(sn) == 10
    iter_sn = [f.get("ident") for f in ds]
    assert iter_sn == sn
    # repeated iteration
    iter_sn = [f.get("ident") for f in ds]
    assert iter_sn == sn


def test_bufr_featurelist_iterator_with_zip():
    # test something different to the iterator - does not try to
    # 'go off the edge' of the featurelist, because the length is determined by
    # the list of metadata values, not the featurelist
    ds = from_source("file", earthkit_examples_file("temp_10.bufr")).to_featurelist()
    ref_levs = ds.get("ident")
    assert len(ref_levs) == 10
    levs1 = []
    levs2 = []
    for k, f in zip(ds.get("ident"), ds):
        levs1.append(k)
        levs2.append(f.get("ident"))
    assert levs1 == ref_levs
    assert levs2 == ref_levs


def test_bufr_featurelist_iterator_with_zip_multiple():
    # same as test_bufr_featurelist_iterator_with_zip() but multiple times
    ds = from_source("file", earthkit_examples_file("temp_10.bufr")).to_featurelist()
    ref_levs = ds.get("ident")
    assert len(ref_levs) == 10
    for i in range(2):
        levs1 = []
        levs2 = []
        for k, f in zip(ds.get("ident"), ds):
            levs1.append(k)
            levs2.append(f.get("ident"))
        assert levs1 == ref_levs, i
        assert levs2 == ref_levs, i


def test_bufr_featurelist_reverse_iterator():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr")).to_featurelist()
    sn = ds.get("ident")
    sn_reversed = list(reversed(sn))
    assert sn_reversed[0] == "02963"
    assert sn_reversed[9] == "02836"
    gr = reversed(ds)
    iter_sn = [f.get("ident") for f in gr]
    assert len(iter_sn) == len(sn_reversed)
    assert iter_sn == sn_reversed
