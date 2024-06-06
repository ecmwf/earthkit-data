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
from earthkit.data import settings
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_examples_file


@pytest.mark.parametrize(
    "file_path,expected_type,expected_len",
    [
        ("test.grib", "grib", 2),
        ("temp_10.bufr", "bufr", 10),
        ("test.odb", "odb", None),
    ],
)
def test_reader_padding_bytes(file_path, expected_type, expected_len):
    path = earthkit_examples_file(file_path)
    tmp = temp_file()

    # note: "reader-type-check-bytes" is 64 by default

    # prepend padding
    with open(tmp.path, "wb") as f_tmp, open(path, "rb") as f:
        b = bytes([0 for _ in range(20)])
        f_tmp.write(b)
        f_tmp.write(f.read())

    ds = from_source("file", tmp.path)
    if hasattr(ds, "_reader"):
        assert expected_type in str(type(ds._reader)).lower()
    else:
        assert expected_type in str(type(ds)).lower()
    if expected_len is not None:
        assert len(ds) == expected_len

    # prepend padding
    tmp = temp_file()
    with open(tmp.path, "wb") as f_tmp, open(path, "rb") as f:
        b = bytes([0 for _ in range(80)])
        f_tmp.write(b)
        f_tmp.write(f.read())

    ds = from_source("file", tmp.path)
    assert "file.File" in str(type(ds))
    assert "unknown" in str(type(ds._reader)).lower()

    with settings.temporary("reader-type-check-bytes", 100):
        ds = from_source("file", tmp.path)
        if hasattr(ds, "_reader"):
            assert expected_type in str(type(ds._reader)).lower()
        else:
            assert expected_type in str(type(ds)).lower()
        if expected_len is not None:
            assert len(ds) == expected_len


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
