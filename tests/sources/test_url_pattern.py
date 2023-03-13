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

from emohawk import load_from


def test_url_pattern_source_1():
    load_from(
        "url-pattern",
        "https://get.ecmwf.int/repository/test-data/emohawk/examples/test.{format}",
        {"format": ["nc", "grib"]},
    )
    # source.to_xarray()


def test_url_pattern_int():

    fs = load_from(
        "url-pattern",
        "https://get.ecmwf.int/repository/test-data/emohawk/examples/test{id}.grib",
        {"id": [4, 6]},
    )

    assert len(fs) == 10


def test_url_pattern_date():

    fs = load_from(
        "url-pattern",
        "https://get.ecmwf.int/repository/test-data/emohawk/test-data/"
        "test_{my_date:date(%Y-%m-%d)}_{name}.grib",
        {"my_date": datetime.datetime(2020, 5, 13), "name": ["t2", "msl"]},
    )

    assert len(fs) == 2


if __name__ == "__main__":
    from emohawk.testing import main

    main(__file__)
