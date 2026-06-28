#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime

from earthkit.data import from_source
from earthkit.data.utils.testing import earthkit_remote_examples_file, earthkit_remote_test_data_file


def test_url_pattern_source_1():
    ds = from_source(
        "url-pattern",
        earthkit_remote_examples_file("test.{format}"),
        {"format": ["nc", "grib"]},
    )
    assert ds

    fl = ds.to_fieldlist()
    assert len(fl) == 4

    # source.to_xarray()


def test_url_pattern_int():
    fs = from_source(
        "url-pattern",
        earthkit_remote_examples_file("test{id}.grib"),
        {"id": [4, 6]},
    ).to_fieldlist()

    assert len(fs) == 10


def test_url_pattern_date():
    fs = from_source(
        "url-pattern",
        earthkit_remote_test_data_file("test_{my_date:date(%Y-%m-%d)}_{name}.grib"),
        {"my_date": datetime.datetime(2020, 5, 13), "name": ["t2", "msl"]},
    ).to_fieldlist()

    assert len(fs) == 2


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
