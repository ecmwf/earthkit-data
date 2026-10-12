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

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.featurelist.stream import StreamFeatureList
from earthkit.data.utils.concat import concat
from earthkit.data.utils.testing import earthkit_examples_file, earthkit_remote_examples_file


def test_bufr_from_stream_iter():
    with open(earthkit_examples_file("temp_10.bufr"), "rb") as stream:
        ds = from_source("stream", stream).to_featurelist()

        # no featurelist methods are available
        with pytest.raises((TypeError, NotImplementedError)):
            len(ds)

        cnt = 0
        for f in ds:
            assert f.subset_count() == 1
            assert f.metadata("dataCategory") == 2
            cnt += 1

        assert cnt == 10

        # stream consumed, no data is available
        assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize("n,expected_sizes", [(1, [1] * 10), (3, [3, 3, 3, 1]), (4, [4, 4, 2])])
def test_bufr_from_stream_batched(n, expected_sizes):
    with open(earthkit_examples_file("temp_10.bufr"), "rb") as stream:
        ds = from_source("stream", stream).to_featurelist()

        with pytest.raises((TypeError, NotImplementedError)):
            len(ds)

        sizes = [len(b) for b in ds.batched(n)]
        assert sizes == expected_sizes

        # stream consumed, no data is available
        assert sum([1 for _ in ds]) == 0


def test_bufr_from_stream_group_by():
    with open(earthkit_examples_file("temp_10.bufr"), "rb") as stream:
        ds = from_source("stream", stream).to_featurelist()

        groups = [g for g in ds.group_by("dataCategory")]
        assert len(groups) == 1
        assert len(groups[0]) == 10
        assert groups[0].metadata("dataCategory") == [2] * 10


def test_bufr_from_stream_in_memory():
    with open(earthkit_examples_file("temp_10.bufr"), "rb") as stream:
        ds = from_source("stream", stream).to_featurelist(read_all=True)

        assert len(ds) == 10
        assert ds.metadata("dataCategory") == [2] * 10

        # slicing
        r = ds[0:3]
        assert len(r) == 3
        assert r.metadata("dataCategory") == [2, 2, 2]

        r = ds[-2:]
        assert len(r) == 2

        # selection
        r = ds.sel(dataCategory=2)
        assert len(r) == 10
        r = ds.sel(dataCategory=1)
        assert len(r) == 0


def test_bufr_save_when_loaded_from_stream():
    with open(earthkit_examples_file("temp_10.bufr"), "rb") as stream:
        fs = from_source("stream", stream).to_featurelist(read_all=True)
        assert len(fs) == 10
        with temp_file() as tmp:
            fs.to_target("file", tmp)
            fs_saved = from_source("file", tmp).to_featurelist()
            assert len(fs) == len(fs_saved)
            assert fs_saved.metadata("dataCategory") == [2] * 10


def test_bufr_file_stream_iter():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr"), stream=True).to_featurelist()

    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    cnt = 0
    for f in ds:
        assert f.metadata("dataCategory") == 2
        cnt += 1
    assert cnt == 10

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


def test_bufr_file_stream_in_memory():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr"), stream=True).to_featurelist(read_all=True)
    assert len(ds) == 10
    assert ds.metadata("dataCategory") == [2] * 10


def test_bufr_multi_from_stream_iter():
    stream1 = open(earthkit_examples_file("temp_10.bufr"), "rb")
    stream2 = open(earthkit_examples_file("temp_10.bufr"), "rb")
    ds = from_source("stream", [stream1, stream2]).to_featurelist()

    assert isinstance(ds, StreamFeatureList)

    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    cnt = 0
    for f in ds:
        assert f.metadata("dataCategory") == 2
        cnt += 1
    assert cnt == 20

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


def test_bufr_multi_stream_memory():
    stream1 = open(earthkit_examples_file("temp_10.bufr"), "rb")
    stream2 = open(earthkit_examples_file("temp_10.bufr"), "rb")
    ds = from_source("stream", [stream1, stream2]).to_featurelist(read_all=True)

    assert len(ds) == 20
    assert ds.metadata("dataCategory") == [2] * 20

    r = ds[0:3]
    assert len(r) == 3


def test_bufr_concat_stream():
    ds1 = from_source("stream", open(earthkit_examples_file("temp_10.bufr"), "rb")).to_featurelist()
    ds2 = from_source("file", earthkit_examples_file("temp_10.bufr"), stream=True).to_featurelist()
    ds3 = from_source("url", earthkit_remote_examples_file("synop_10.bufr"), stream=True).to_featurelist()

    ds = concat(ds1, ds2, ds3)

    cnt = 0
    for f in ds:
        cnt += 1
    assert cnt == 30

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main()
