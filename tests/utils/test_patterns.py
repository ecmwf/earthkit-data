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

import pytest

from earthkit.data.utils.patterns import Pattern


@pytest.mark.parametrize(
    "pattern,values,expected_value",
    [
        ("test.{format}", {"format": ["nc", "grib"]}, ["test.nc", "test.grib"]),
        ("test_{id}.grib", {"id": [2, 3, "AA"]}, ["test_2.grib", "test_3.grib", "test_AA.grib"]),
        (
            "test_{my_date:date(%Y-%m-%d)}_{name}.grib",
            {"my_date": datetime.datetime(2020, 5, 13), "name": ["t2", "msl"]},
            ["test_2020-05-13_t2.grib", "test_2020-05-13_msl.grib"],
        ),
        (
            "test_{date:strftimedelta(-6;%Y-%m-%d_%H)}.grib",
            {"date": [datetime.datetime(2020, 5, 11), datetime.datetime(2020, 5, 11, 6)]},
            ["test_2020-05-10_18.grib", "test_2020-05-11_00.grib"],
        ),
        (
            "test_{date:strftimedelta(60m;%Y-%m-%d_%H)}.grib",
            {"date": [datetime.datetime(2020, 5, 11), datetime.datetime(2020, 5, 11, 6)]},
            ["test_2020-05-11_01.grib", "test_2020-05-11_07.grib"],
        ),
    ],
)
def test_pattern_core(pattern, values, expected_value):
    p = Pattern(pattern)
    assert p.substitute(values) == expected_value
