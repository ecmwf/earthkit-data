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
from earthkit.data.testing import NO_S3_AUTH


def _check_s3_credentials():
    import os

    key_id = os.environ.get("AWS_ACCESS_KEY_ID", None)
    key = os.environ.get("AWS_SECRET_ACCESS_KEY", None)
    if key_id and key:
        return True
    return False


NO_S3_CREDENTIALS = not _check_s3_credentials()


@pytest.mark.parametrize(
    "objects,expected_len",
    [
        ("test6.grib", 6),
        ({"object": "test6.grib"}, 6),
        ([{"object": "test6.grib"}], 6),
        ([{"object": "test6.grib"}, {"object": "tuv_pl.grib"}], 24),
    ],
)
def test_s3_ewc_request(objects, expected_len):
    r = {
        "endpoint": "object-store.os-api.cci1.ecmwf.int",
        "bucket": "earthkit-test-data-public",
        "objects": objects,
    }

    ds = from_source("s3", r, stream=False, anon=True)
    assert len(ds) == expected_len


def test_s3_ewc_public_core():
    r = {
        "endpoint": "object-store.os-api.cci1.ecmwf.int",
        "bucket": "earthkit-test-data-public",
        "objects": [{"object": "test6.grib"}],
    }

    ds = from_source("s3", r, stream=False, anon=True)

    assert len(ds) == 6

    ref = [
        ("t", 1000),
        ("u", 1000),
        ("v", 1000),
        ("t", 850),
        ("u", 850),
        ("v", 850),
    ]

    assert ds.metadata(("param", "level")) == ref


@pytest.mark.skipif(NO_S3_AUTH, reason="No S3 authenticator")
@pytest.mark.skipif(NO_S3_CREDENTIALS, reason="No S3 credentials available")
def test_s3_ewc_private_core():
    r = {
        "endpoint": "object-store.os-api.cci1.ecmwf.int",
        "bucket": "earthkit-test-data",
        "objects": [{"object": "test6.grib"}],
    }

    ds = from_source("s3", r, stream=False, anon=False)

    assert len(ds) == 6

    ref = [
        ("t", 1000),
        ("u", 1000),
        ("v", 1000),
        ("t", 850),
        ("u", 850),
        ("v", 850),
    ]

    assert ds.metadata(("param", "level")) == ref


@pytest.mark.parametrize(
    "parts,expected_meta",
    [
        ((0, 150), [("t", 1000)]),
        ((240, 150), [("u", 1000)]),
        ((240, 480), [("u", 1000), ("v", 1000)]),
    ],
)
def test_s3_ewc_public_single_parts(parts, expected_meta):
    r = {
        "endpoint": "object-store.os-api.cci1.ecmwf.int",
        "bucket": "earthkit-test-data-public",
        "objects": [{"object": "test6.grib", "parts": parts}],
    }

    ds = from_source("s3", r, stream=False, anon=True)

    assert len(ds) == len(expected_meta)
    assert ds.metadata(("param", "level")) == expected_meta


@pytest.mark.skipif(NO_S3_AUTH, reason="No S3 authenticator")
@pytest.mark.skipif(NO_S3_CREDENTIALS, reason="No S3 credentials available")
@pytest.mark.parametrize(
    "parts,expected_meta",
    [
        ((0, 150), [("t", 1000)]),
        ((240, 150), [("u", 1000)]),
        ((240, 480), [("u", 1000), ("v", 1000)]),
    ],
)
def test_s3_ewc_private_single_parts(parts, expected_meta):
    r = {
        "endpoint": "object-store.os-api.cci1.ecmwf.int",
        "bucket": "earthkit-test-data",
        "objects": [{"object": "test6.grib", "parts": parts}],
    }

    ds = from_source("s3", r, stream=False, anon=False)

    assert len(ds) == len(expected_meta)
    assert ds.metadata(("param", "level")) == expected_meta


def test_s3_ewc_public_stream_core():
    r = {
        "endpoint": "object-store.os-api.cci1.ecmwf.int",
        "bucket": "earthkit-test-data-public",
        "objects": [{"object": "test6.grib"}],
    }

    ds = from_source("s3", r, stream=True, anon=True)

    # no fieldlist methods are available
    with pytest.raises(NotImplementedError):
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


@pytest.mark.skipif(NO_S3_AUTH, reason="No S3 authenticator")
@pytest.mark.skipif(NO_S3_CREDENTIALS, reason="No S3 credentials available")
def test_s3_ewc_private_stream():
    r = {
        "endpoint": "object-store.os-api.cci1.ecmwf.int",
        "bucket": "earthkit-test-data",
        "objects": [{"object": "test6.grib"}],
    }

    ds = from_source("s3", r, stream=True, anon=False)

    # no fieldlist methods are available
    with pytest.raises(NotImplementedError):
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
    "parts,expected_meta",
    [
        ((0, 150), [("t", 1000)]),
        ((240, 150), [("u", 1000)]),
        ((240, 480), [("u", 1000), ("v", 1000)]),
    ],
)
def test_s3_ewc_public_stream_single_parts(parts, expected_meta):
    r = {
        "endpoint": "object-store.os-api.cci1.ecmwf.int",
        "bucket": "earthkit-test-data-public",
        "objects": [{"object": "test6.grib", "parts": parts}],
    }

    ds = from_source("s3", r, stream=True, anon=True)

    # no fieldlist methods are available
    with pytest.raises(NotImplementedError):
        len(ds)

    cnt = 0
    for i, f in enumerate(ds):
        assert f.metadata(("param", "level")) == expected_meta[i], i
        cnt += 1

    assert cnt == len(expected_meta)

    # stream consumed, no data is available
    assert sum([1 for _ in ds]) == 0


@pytest.mark.skipif(NO_S3_AUTH, reason="No S3 authenticator")
@pytest.mark.skipif(NO_S3_CREDENTIALS, reason="No S3 credentials available")
@pytest.mark.parametrize(
    "parts,expected_meta",
    [
        ((0, 150), [("t", 1000)]),
        ((240, 150), [("u", 1000)]),
        ((240, 480), [("u", 1000), ("v", 1000)]),
    ],
)
def test_s3_ewc_private_stream_single_parts(parts, expected_meta):
    r = {
        "endpoint": "object-store.os-api.cci1.ecmwf.int",
        "bucket": "earthkit-test-data",
        "objects": [{"object": "test6.grib", "parts": parts}],
    }

    ds = from_source("s3", r, stream=True, anon=False)

    # no fieldlist methods are available
    with pytest.raises(NotImplementedError):
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

    main(__file__)
