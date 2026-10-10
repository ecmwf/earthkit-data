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
from earthkit.data.utils.testing import earthkit_remote_examples_file, earthkit_remote_file

TEMP_10_IDENTS = [
    "02836",
    "01400",
    "01415",
    "01001",
    "01152",
    "01241",
    "03953",
    "11747",
    "11035",
    "02963",
]

SYNOP_10_IDENTS = [
    "91648",
    "89514",
    "60545",
    "30823",
    "30846",
    "48352",
    "98747",
    "68267",
    "68592",
    "91701",
]


def test_bufr_url_stream_iter():
    ds = from_source(
        "url",
        earthkit_remote_examples_file("temp_10.bufr"),
        stream=True,
    ).to_featurelist()

    # no featurelist methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata("dataCategory") == 2
        assert f.metadata("ident") == TEMP_10_IDENTS[i]
        cnt += 1

    assert cnt == 10

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize("n,expected_sizes", [(1, [1] * 10), (3, [3, 3, 3, 1]), (4, [4, 4, 2])])
def test_bufr_url_stream_batched(n, expected_sizes):
    ds = from_source(
        "url",
        earthkit_remote_examples_file("temp_10.bufr"),
        stream=True,
    ).to_featurelist()

    # no methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    sizes = [len(b) for b in ds.batched(n)]
    assert sizes == expected_sizes

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


def test_bufr_url_stream_group_by():
    ds = from_source("url", earthkit_remote_examples_file("temp_10.bufr"), stream=True).to_featurelist()

    # no methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    groups = [g for g in ds.group_by("dataCategory")]
    assert len(groups) == 1
    assert len(groups[0]) == 10
    assert groups[0].metadata("dataCategory") == [2] * 10

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


def test_bufr_url_stream_in_memory():
    ds = from_source(
        "url",
        earthkit_remote_examples_file("temp_10.bufr"),
        stream=True,
    ).to_featurelist(read_all=True)

    assert len(ds) == 10
    assert ds.metadata("dataCategory") == [2] * 10
    assert ds.metadata("ident") == TEMP_10_IDENTS

    # slicing
    r = ds[0:3]
    assert len(r) == 3
    assert r.metadata("ident") == TEMP_10_IDENTS[0:3]

    r = ds[-2:]
    assert len(r) == 2
    assert r.metadata("ident") == TEMP_10_IDENTS[-2:]


def test_bufr_save_when_loaded_from_url_stream():
    ds = from_source(
        "url",
        earthkit_remote_examples_file("temp_10.bufr"),
        stream=True,
    ).to_featurelist(read_all=True)
    assert len(ds) == 10
    with temp_file() as tmp:
        ds.to_target("file", tmp)
        ds_saved = from_source("file", tmp).to_featurelist()
        assert len(ds) == len(ds_saved)
        assert ds_saved.metadata("ident") == TEMP_10_IDENTS


def test_bufr_url_stream_multi_urls_iter():
    ds = from_source(
        "url",
        [
            earthkit_remote_examples_file("temp_10.bufr"),
            earthkit_remote_examples_file("synop_10.bufr"),
        ],
        stream=True,
    ).to_featurelist()

    assert isinstance(ds, StreamFeatureList)
    assert len(ds._source.sources) == 2

    # no featurelist methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    ref_category = [2] * 10 + [0] * 10
    ref_ident = TEMP_10_IDENTS + SYNOP_10_IDENTS

    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata("dataCategory") == ref_category[i], i
        assert f.metadata("ident") == ref_ident[i], i
        cnt += 1

    assert cnt == len(ref_ident)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize(
    "n,expected_sizes",
    [
        (1, [1] * 20),
        (10, [10, 10]),
        (7, [7, 7, 6]),
    ],
)
def test_bufr_url_stream_multi_urls_batched(n, expected_sizes):
    ds = from_source(
        "url",
        [
            earthkit_remote_examples_file("temp_10.bufr"),
            earthkit_remote_examples_file("synop_10.bufr"),
        ],
        stream=True,
    ).to_featurelist()

    # no methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    sizes = [len(b) for b in ds.batched(n)]
    assert sizes == expected_sizes

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


def test_bufr_url_stream_multi_urls_memory():
    ds = from_source(
        "url",
        [
            earthkit_remote_examples_file("temp_10.bufr"),
            earthkit_remote_examples_file("synop_10.bufr"),
        ],
        stream=True,
    ).to_featurelist(read_all=True)

    assert len(ds) == 20

    ref_category = [2] * 10 + [0] * 10
    assert ds.metadata("dataCategory") == ref_category

    # first part
    r = ds[0:10]
    assert len(r) == 10
    assert r.metadata("ident") == TEMP_10_IDENTS

    # second part
    r = ds[10:]
    assert len(r) == 10
    assert r.metadata("ident") == SYNOP_10_IDENTS

    # slicing
    r = ds[0:3]
    assert len(r) == 3
    assert r.metadata("ident") == TEMP_10_IDENTS[0:3]

    r = ds[-2:]
    assert len(r) == 2
    assert r.metadata("ident") == SYNOP_10_IDENTS[-2:]

    # selection
    r = ds.sel(dataCategory=0)
    assert len(r) == 10
    assert r.metadata("ident") == SYNOP_10_IDENTS


@pytest.mark.parametrize(
    "parts,expected_idents",
    [
        ([(0, 1596)], [TEMP_10_IDENTS[0]]),
        ([(1596, 1308)], [TEMP_10_IDENTS[1]]),
        ([(1596, 1308 + 1166)], [TEMP_10_IDENTS[1], TEMP_10_IDENTS[2]]),
        ([(1596, 1308), (4070, 1276)], [TEMP_10_IDENTS[1], TEMP_10_IDENTS[3]]),
    ],
)
def test_bufr_url_stream_single_url_parts_core(parts, expected_idents):
    ds = from_source(
        "url",
        earthkit_remote_file("examples/temp_10.bufr"),
        parts=parts,
        stream=True,
    ).to_featurelist()

    # no featurelist methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata("ident") == expected_idents[i], i
        cnt += 1

    assert cnt == len(expected_idents)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize(
    "parts,expected_idents",
    [
        ([(0, 1596)], [TEMP_10_IDENTS[0]]),
        (None, TEMP_10_IDENTS),
    ],
)
def test_bufr_url_stream_single_url_parts_as_arg_valid(parts, expected_idents):
    ds = from_source(
        "url",
        [earthkit_remote_examples_file("temp_10.bufr"), parts],
        stream=True,
    ).to_featurelist()

    # no featurelist methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata("ident") == expected_idents[i], i
        cnt += 1

    assert cnt == len(expected_idents)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


def test_bufr_url_stream_single_url_parts_as_arg_invalid():
    with pytest.raises(ValueError):
        from_source(
            "url",
            [earthkit_remote_examples_file("temp_10.bufr"), [(0, 1596)]],
            parts=[(0, 1600)],
            stream=True,
        ).to_featurelist()


@pytest.mark.parametrize(
    "parts1,parts2,expected_idents",
    [
        (
            [(1596, 1308)],
            None,
            [TEMP_10_IDENTS[1]] + SYNOP_10_IDENTS,
        ),
        (
            None,
            [(0, 220)],
            TEMP_10_IDENTS + [SYNOP_10_IDENTS[0]],
        ),
        (
            [(1596, 1308)],
            [(0, 220)],
            [TEMP_10_IDENTS[1], SYNOP_10_IDENTS[0]],
        ),
        (
            [(1596, 1308), (4070, 1276)],
            [(0, 220)],
            [TEMP_10_IDENTS[1], TEMP_10_IDENTS[3], SYNOP_10_IDENTS[0]],
        ),
    ],
)
def test_bufr_url_stream_multi_urls_parts(parts1, parts2, expected_idents):
    ds = from_source(
        "url",
        [
            [earthkit_remote_examples_file("temp_10.bufr"), parts1],
            [earthkit_remote_examples_file("synop_10.bufr"), parts2],
        ],
        stream=True,
    ).to_featurelist()

    # no featurelist methods are available
    with pytest.raises((TypeError, NotImplementedError)):
        len(ds)

    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata("ident") == expected_idents[i], i
        cnt += 1

    assert cnt == len(expected_idents)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main()
