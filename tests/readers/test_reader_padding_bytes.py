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

from earthkit.data import config, from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.utils.testing import earthkit_examples_file


@pytest.mark.parametrize(
    "file_path,expected_len",
    [
        ("test.grib", 2),
    ],
)
def test_reader_padding_bytes_grib(file_path, expected_len):
    path = earthkit_examples_file(file_path)
    tmp = temp_file()

    # note: "reader-type-check-bytes" is 64 by default

    # prepend padding
    with open(tmp.path, "wb") as f_tmp, open(path, "rb") as f:
        b = bytes([0 for _ in range(20)])
        f_tmp.write(b)
        f_tmp.write(f.read())

    ds = from_source("file", tmp.path)
    assert ds._TYPE_NAME == "GRIB"
    ds = ds.to_fieldlist()
    if expected_len is not None:
        assert len(ds) == expected_len

    # prepend padding
    tmp = temp_file()
    with open(tmp.path, "wb") as f_tmp, open(path, "rb") as f:
        b = bytes([0 for _ in range(80)])
        f_tmp.write(b)
        f_tmp.write(f.read())

    ds = from_source("file", tmp.path)
    assert ds._TYPE_NAME == "Unknown"

    with config.temporary("reader-type-check-bytes", 100):
        ds = from_source("file", tmp.path)
        assert ds._TYPE_NAME == "GRIB"
        ds = ds.to_fieldlist()
        if expected_len is not None:
            assert len(ds) == expected_len


@pytest.mark.parametrize(
    "file_path,expected_len",
    [
        ("temp_10.bufr", 10),
    ],
)
def test_reader_padding_bytes_bufr(file_path, expected_len):
    path = earthkit_examples_file(file_path)
    tmp = temp_file()

    # note: "reader-type-check-bytes" is 64 by default

    # prepend padding
    with open(tmp.path, "wb") as f_tmp, open(path, "rb") as f:
        b = bytes([0 for _ in range(20)])
        f_tmp.write(b)
        f_tmp.write(f.read())

    ds = from_source("file", tmp.path)
    assert ds._TYPE_NAME == "BUFR"
    ds = ds.to_featurelist()
    if expected_len is not None:
        assert len(ds) == expected_len

    # prepend padding
    tmp = temp_file()
    with open(tmp.path, "wb") as f_tmp, open(path, "rb") as f:
        b = bytes([0 for _ in range(80)])
        f_tmp.write(b)
        f_tmp.write(f.read())

    ds = from_source("file", tmp.path)
    assert ds._TYPE_NAME == "Unknown"

    with config.temporary("reader-type-check-bytes", 100):
        ds = from_source("file", tmp.path)
        assert ds._TYPE_NAME == "BUFR"
        ds = ds.to_featurelist()
        if expected_len is not None:
            assert len(ds) == expected_len


@pytest.mark.parametrize(
    "file_path,expected_len",
    [
        ("test.odb", None),
    ],
)
def test_reader_padding_bytes_odb(file_path, expected_len):
    path = earthkit_examples_file(file_path)
    tmp = temp_file()

    # note: "reader-type-check-bytes" is 64 by default

    # prepend padding
    with open(tmp.path, "wb") as f_tmp, open(path, "rb") as f:
        b = bytes([0 for _ in range(20)])
        f_tmp.write(b)
        f_tmp.write(f.read())

    ds = from_source("file", tmp.path)
    assert ds._TYPE_NAME == "ODB"
    if expected_len is not None:
        assert len(ds.to_pandas()) == expected_len

    # prepend padding
    tmp = temp_file()
    with open(tmp.path, "wb") as f_tmp, open(path, "rb") as f:
        b = bytes([0 for _ in range(80)])
        f_tmp.write(b)
        f_tmp.write(f.read())

    ds = from_source("file", tmp.path)
    assert ds._TYPE_NAME == "Unknown"

    with config.temporary("reader-type-check-bytes", 100):
        ds = from_source("file", tmp.path)
        assert ds._TYPE_NAME == "ODB"
        if expected_len is not None:
            assert len(ds.to_pandas()) == expected_len
