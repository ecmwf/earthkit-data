#!/usr/bin/env python3

# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os

from earthkit.data import download_example_file
from earthkit.data import remote_example_file


def test_download_example_file_single(tmpdir):
    filename = "test.grib"
    with tmpdir.as_cwd():
        download_example_file(filename)
        path = os.path.join(tmpdir.realpath(), filename)
        assert os.path.exists(path)

        mtime = os.stat(path).st_mtime_ns
        download_example_file(filename, force=True)
        assert os.path.exists(path)
        assert os.stat(path).st_mtime_ns > mtime


def test_download_example_file_multi(tmpdir):
    filenames = ["test.grib", "test6.grib"]
    with tmpdir.as_cwd():
        download_example_file(filenames)

        paths = [os.path.join(tmpdir.realpath(), f) for f in filenames]
        for path in paths:
            assert os.path.exists(path)

        mtimes = [os.stat(p).st_mtime_ns for p in paths]
        download_example_file(filenames, force=True)
        for i, p in enumerate(paths):
            assert os.path.exists(p)
            assert os.stat(p).st_mtime_ns > mtimes[i]


def test_remote_example_file_path():
    filename = "test.grib"
    assert (
        remote_example_file(filename)
        == "https://get.ecmwf.int/repository/test-data/earthkit-data/examples/" + filename
    )


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
