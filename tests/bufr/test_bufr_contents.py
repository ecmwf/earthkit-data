#!/usr/bin/env python3

# (C) Copyright 2022- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_remote_test_data_file


def test_bufr_iteration():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr"))
    assert len(ds) == 10
    assert len([x for x in ds]) == 10
    for f in ds:
        assert f.subset_count() == 1


def test_bufr_message_repr():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr"))
    assert "BUFRMessage" in ds[0].__repr__()


def test_bufr_metadata():
    ds = from_source("file", earthkit_examples_file("temp_10.bufr"))
    assert ds[0].subset_count() == 1
    assert ds[0].is_compressed() is False
    assert ds[0].is_uncompressed() is False

    assert ds[0].metadata("dataCategory") == 2

    assert ds.metadata("dataCategory") == [2] * 10


def test_bufr_metadata_uncompressed():
    ds = from_source(
        "url",
        earthkit_remote_test_data_file("test-data/synop_multi_subset_uncompressed.bufr"),
    )
    assert len(ds) == 1
    f = ds[0]
    assert f.subset_count() == 12
    assert f.is_compressed() is False
    assert f.is_uncompressed() is True


def test_bufr_metadata_compressed():
    ds = from_source(
        "url",
        earthkit_remote_test_data_file("test-data/ens_multi_subset_compressed.bufr"),
    )
    assert len(ds) == 1
    f = ds[0]
    assert f.subset_count() == 51
    assert f.is_compressed() is True
    assert f.is_uncompressed() is False


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
