#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import mimetypes
import tarfile

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.utils.testing import check_unsafe_archives


@pytest.mark.skip
def test_tar_safety():
    check_unsafe_archives(".tar")


def test_tar_mimetypes():
    assert mimetypes.guess_type("x.tar") == ("application/x-tar", None)
    assert mimetypes.guess_type("x.tgz") == ("application/x-tar", "gzip")

    assert mimetypes.guess_type("x.tar.gz") == ("application/x-tar", "gzip")
    assert mimetypes.guess_type("x.tar.bz2") == ("application/x-tar", "bzip2")


@pytest.mark.parametrize("name", ["data.tar", "data"])
def test_tar_reader(tmp_path, name):
    expected = np.array([[1, 2], [3, 4]])
    np.save(tmp_path / "data.npy", expected)

    path = tmp_path / name
    with tarfile.open(path, "w") as archive:
        archive.add(tmp_path / "data.npy", arcname="data.npy")

    np.testing.assert_array_equal(from_source("file", path).to_numpy(), expected)


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
