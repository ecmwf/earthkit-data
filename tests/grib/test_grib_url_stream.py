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
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_remote_test_data_file


def repeat_list_items(items, count):
    return sum([[x] * count for x in items], [])


@pytest.mark.parametrize(
    "_kwargs,error",
    [
        (dict(order_by="level"), TypeError),
        (dict(group_by=1), TypeError),
        (dict(group_by=["level", 1]), TypeError),
        # (dict(group_by="level", batch_size=1), TypeError),
        (dict(batch_size=-1), ValueError),
    ],
)
def test_grib_url_stream_invalid_args(_kwargs, error):
    with pytest.raises(error):
        from_source(
            "url",
            earthkit_remote_test_data_file("examples/test6.grib"),
            stream=True,
            **_kwargs,
        )


@pytest.mark.parametrize(
    "_kwargs",
    [
        {"group_by": "level"},
        {"group_by": "level", "batch_size": 0},
        {"group_by": "level", "batch_size": 1},
        {"group_by": ["level", "gridType"]},
    ],
)
def test_grib_url_stream_group_by(_kwargs):
    fs = from_source(
        "url",
        earthkit_remote_test_data_file("examples/test6.grib"),
        stream=True,
        **_kwargs,
    )

    # no methods are available
    with pytest.raises(TypeError):
        len(fs)

    ref = [
        [("t", 1000), ("u", 1000), ("v", 1000)],
        [("t", 850), ("u", 850), ("v", 850)],
    ]
    cnt = 0
    for i, f in enumerate(fs):
        assert len(f) == 3
        assert f.metadata(("param", "level")) == ref[i]
        assert f.to_fieldlist("numpy") is not f
        cnt += 1

    assert cnt == len(ref)

    # stream consumed, no data is available
    assert sum([1 for _ in fs]) == 0


@pytest.mark.parametrize(
    "_kwargs",
    [
        {},
        {"batch_size": 1},
    ],
)
def test_grib_url_stream_single_batch(_kwargs):
    ds = from_source(
        "url",
        earthkit_remote_test_data_file("examples/test6.grib"),
        stream=True,
        **_kwargs,
    )

    # no fieldlist methods are available
    with pytest.raises(TypeError):
        len(ds)

    ref = [
        ("t", 1000),
        ("u", 1000),
        ("v", 1000),
        ("t", 850),
        ("u", 850),
        ("v", 850),
    ]
    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == ref[i], i
        cnt += 1

    assert cnt == len(ref)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize(
    "_kwargs,expected_meta",
    [
        ({"batch_size": 3}, [["t", "u", "v"], ["t", "u", "v"]]),
        ({"batch_size": 4}, [["t", "u", "v", "t"], ["u", "v"]]),
    ],
)
def test_grib_url_stream_multi_batch(_kwargs, expected_meta):
    ds = from_source(
        "url",
        earthkit_remote_test_data_file("examples/test6.grib"),
        stream=True,
        **_kwargs,
    )

    # no methods are available
    with pytest.raises(TypeError):
        len(ds)

    cnt = 0
    for i, f in enumerate(ds):
        assert len(f) == len(expected_meta[i])
        f.metadata("param") == expected_meta[i]
        cnt += 1

    assert cnt == len(expected_meta)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


def test_grib_url_stream_in_memory():
    ds = from_source(
        "url",
        earthkit_remote_test_data_file("examples/test6.grib"),
        stream=True,
        batch_size=0,
    )

    assert len(ds) == 6

    expected_shape = (6, 7, 12)
    ref = ["t", "u", "v", "t", "u", "v"]
    val = []

    # iteration
    for f in ds:
        v = f.metadata("param")
        val.append(v)

    assert val == ref, "iteration"

    # metadata
    val = []
    val = ds.metadata("param")
    assert val == ref, "method"

    # data
    assert ds.to_numpy().shape == expected_shape

    ref = np.array(
        [
            272.56417847,
            -6.28688049,
            7.83348083,
            272.53916931,
            -4.89837646,
            8.66096497,
        ]
    )

    vals = ds.to_numpy()[:, 0, 0]
    assert np.allclose(vals, ref)


def test_grib_save_when_loaded_from_url_stream():
    ds = from_source(
        "url",
        earthkit_remote_test_data_file("examples/test6.grib"),
        stream=True,
        batch_size=0,
    )
    assert len(ds) == 6
    with temp_file() as tmp:
        ds.save(tmp)
        ds_saved = from_source("file", tmp)
        assert len(ds) == len(ds_saved)


@pytest.mark.parametrize(
    "_kwargs",
    [
        {},
        {"batch_size": 1},
    ],
)
def test_grib_multi_url_stream_single_batch(_kwargs):
    ds = from_source(
        "url",
        [
            earthkit_remote_test_data_file("examples/test.grib"),
            earthkit_remote_test_data_file("examples/test4.grib"),
        ],
        stream=True,
        **_kwargs,
    )

    # no fieldlist methods are available
    with pytest.raises(TypeError):
        len(ds)

    ref = [
        ("2t", 0),
        ("msl", 0),
        ("t", 500),
        ("z", 500),
        ("t", 850),
        ("z", 850),
    ]
    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == ref[i], i
        cnt += 1

    assert cnt == len(ref)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize(
    "_kwargs,expected_meta",
    [
        ({"batch_size": 2}, [["2t", "msl"], ["t", "z"], ["t", "z"]]),
        ({"batch_size": 3}, [["2t", "msl", "t"], ["z", "t", "z"]]),
        ({"batch_size": 4}, [["2t", "msl", "t", "z"], ["t", "z"]]),
    ],
)
def test_grib_multi_url_stream_batch(_kwargs, expected_meta):
    ds = from_source(
        "url",
        [
            earthkit_remote_test_data_file("examples/test.grib"),
            earthkit_remote_test_data_file("examples/test4.grib"),
        ],
        stream=True,
        **_kwargs,
    )

    # no methods are available
    with pytest.raises(TypeError):
        len(ds)

    cnt = 0
    for i, f in enumerate(ds):
        assert len(f) == len(expected_meta[i])
        f.metadata("param") == expected_meta[i]
        cnt += 1

    assert cnt == len(expected_meta)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


def test_grib_multi_url_stream_memory():
    ds = from_source(
        "url",
        [
            earthkit_remote_test_data_file("examples/test.grib"),
            earthkit_remote_test_data_file("examples/test4.grib"),
        ],
        stream=True,
        batch_size=0,
    )

    assert len(ds) == 6

    md_ref = [
        ("2t", 0),
        ("msl", 0),
        ("t", 500),
        ("z", 500),
        ("t", 850),
        ("z", 850),
    ]

    val = []

    # iteration
    for f in ds:
        v = f.metadata(("param", "level"))
        val.append(v)

    assert val == md_ref, "iteration"

    # metadata
    val = []
    val = ds.metadata(("param", "level"))
    assert val == md_ref, "method"

    # data
    with pytest.raises(ValueError):
        ds.to_numpy().shape

    # first part
    expected_shape = (2, 11, 19)
    assert ds[0:2].to_numpy().shape == expected_shape

    ref = np.array([262.78027344, 101947.8125])

    vals = ds[0:2].to_numpy()[:, 0, 0]
    assert np.allclose(vals, ref)

    # second part
    expected_shape = (4, 181, 360)
    assert ds[2:].to_numpy().shape == expected_shape

    ref = np.array([228.04600525, 48126.859375, 246.61032104, 11786.1132812])

    vals = ds[2:].to_numpy()[:, 0, 0]
    assert np.allclose(vals, ref)

    # slicing
    r = ds[0:3]
    assert len(r) == 3
    val = r.metadata(("param", "level"))
    assert val == md_ref[0:3]

    r = ds[-2:]
    assert len(r) == 2
    val = r.metadata(("param", "level"))
    assert val == md_ref[-2:]

    r = ds.sel(param="t")
    assert len(r) == 2
    val = r.metadata(("param", "level"))
    assert val == [
        ("t", 500),
        ("t", 850),
    ]


@pytest.mark.parametrize(
    "parts,expected_meta",
    [
        ([(0, 150)], [("t", 1000)]),
        ([(240, 150)], [("u", 1000)]),
        ([(240, 480)], [("u", 1000), ("v", 1000)]),
    ],
)
def test_grib_single_url_stream_parts(parts, expected_meta):
    ds = from_source(
        "url",
        earthkit_remote_test_data_file("examples/test6.grib"),
        parts=parts,
        stream=True,
    )

    # no fieldlist methods are available
    with pytest.raises(TypeError):
        len(ds)

    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == expected_meta[i], i
        cnt += 1

    assert cnt == len(expected_meta)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


@pytest.mark.parametrize(
    "parts1,parts2,expected_meta",
    [
        (
            [(240, 150)],
            None,
            [("u", 1000), ("2t", 0), ("msl", 0)],
        ),
        (
            None,
            [(0, 526)],
            [
                ("t", 1000),
                ("u", 1000),
                ("v", 1000),
                ("t", 850),
                ("u", 850),
                ("v", 850),
                ("2t", 0),
            ],
        ),
        (
            [(240, 150)],
            [(0, 526)],
            [("u", 1000), ("2t", 0)],
        ),
    ],
)
def test_grib_multi_url_stream_parts(parts1, parts2, expected_meta):
    ds = from_source(
        "url",
        [
            [earthkit_remote_test_data_file("examples/test6.grib"), parts1],
            [earthkit_remote_test_data_file("examples/test.grib"), parts2],
        ],
        stream=True,
    )

    # no fieldlist methods are available
    with pytest.raises(TypeError):
        len(ds)

    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == expected_meta[i], i
        cnt += 1

    assert cnt == len(expected_meta)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
