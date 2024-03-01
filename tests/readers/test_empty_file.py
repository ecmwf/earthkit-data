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

import earthkit.data
from earthkit.data.testing import earthkit_test_data_file


def test_empty_file_reader():
    with pytest.raises(Exception):
        earthkit.data.from_source("file", earthkit_test_data_file("empty_file.grib"))


def test_nonexisting_file_reader():
    with pytest.raises(FileExistsError):
        earthkit.data.from_source("file", "__nonexistingfile__")


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
