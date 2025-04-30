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

from earthkit.data.utils.patterns import Function
from earthkit.data.utils.patterns import Pattern
from earthkit.data.utils.patterns import Variable


@pytest.mark.parametrize(
    "pattern,values,expected_value,error",
    [
        ("level", {"level": "500"}, "500", None),
        ("level:int", {"level": 500}, "500", None),
        ("level:int(%04d)", {"level": 500}, "0500", None),
        ("level:int", {"level": "500"}, None, ValueError),
        ("level:float", {"level": 500}, "500", None),
        ("level:float", {"level": 500.0}, "500", None),
        ("level:float", {"level": 500.1}, "500.1", None),
        ("level:float(%.02f)", {"level": 500.1}, "500.10", None),
        ("level:enum(925,500,700)", {"level": "500"}, "500", None),
        ("level:enum(925,500,700)", {"level": 500}, "500", ValueError),
        ("level:enum(925,500,700)", {"level": "1000"}, None, ValueError),
        ("my_date:date(%Y-%m-%d)", {"my_date": "20200513"}, "2020-05-13", None),
        ("my_date:date(%Y-%m-%d)", {"my_date": datetime.datetime(2020, 5, 13)}, "2020-05-13", None),
        ("my_date:strftime(%Y-%m-%d)", {"my_date": datetime.datetime(2020, 5, 13)}, "2020-05-13", None),
        (
            "my_date:date(%Y%m%d_%H:%M)",
            {"my_date": datetime.datetime(2020, 5, 13, 11, 23, 0)},
            "20200513_11:23",
            None,
        ),
    ],
)
def test_pattern_variable_substitute(pattern, values, expected_value, error):
    v = Variable(pattern)
    if not error:
        assert v.substitute(values) == expected_value
    else:
        with pytest.raises(error):
            v.substitute(values)


@pytest.mark.parametrize(
    "pattern,values,expected_value,error",
    [
        ("level", {"level": "500"}, ["500"], None),
        ("level", {"level": ["500", "300"]}, ["500", "300"], None),
        ("level:int", {"level": 500}, ["500"], None),
        ("level:int", {"level": [500, 300]}, ["500", "300"], None),
        ("level:int", {"level": "500"}, None, ValueError),
        ("level:enum(925,500,700)", {"level": ["500", "700"]}, ["500", "700"], None),
        ("level:enum(925,500,700)", {"level": ["700", "500"]}, ["700", "500"], None),
        ("level:enum(925,500,700)", {"level": 500}, "500", ValueError),
        ("level:enum(925,500,700)", {"level": ["1000", "500"]}, None, ValueError),
        ("my_date:date(%Y-%m-%d)", {"my_date": datetime.datetime(2020, 5, 13)}, ["2020-05-13"], None),
        ("my_date:strftime(%Y-%m-%d)", {"my_date": datetime.datetime(2020, 5, 13)}, ["2020-05-13"], None),
        (
            "my_date:date(%Y%m%d_%H:%M)",
            {"my_date": datetime.datetime(2020, 5, 13, 11, 23, 0)},
            ["20200513_11:23"],
            None,
        ),
    ],
)
def test_pattern_variable_substitute_many(pattern, values, expected_value, error):
    v = Variable(pattern)
    if not error:
        assert v.substitute_many(values) == expected_value
    else:
        with pytest.raises(error):
            v.substitute_many(values)


@pytest.mark.parametrize(
    "pattern,values,expected_value,error",
    [
        ("param|lower", {"param": "TeST"}, "test", None),
    ],
)
def test_pattern_function_substitute(pattern, values, expected_value, error):
    v = Function(pattern)
    if not error:
        assert v.substitute(values) == expected_value
    else:
        with pytest.raises(error):
            v.substitute(values)


@pytest.mark.parametrize(
    "pattern,value,expected_value",
    [
        ("level", "level", {}),
        ("level", "level1", None),
        ("{level}", "500", {"level": "500"}),
        ("_{level}_", "_500_", {"level": "500"}),
        ("_{level}_{date:date(%Y-%m-%d)}.grib", "_500_", None),
        (
            "_{level}_{date:date(%Y-%m-%d)}.grib",
            "_500_2000-01-02.grib",
            {"level": "500", "date": "2000-01-02"},
        ),
    ],
)
def test_pattern_match(pattern, value, expected_value):
    p = Pattern(pattern)
    m = p.match(value)
    if expected_value is None:
        assert m is None
    else:
        assert m.groupdict() == expected_value


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
        ("test_{param|lower}", {"param": ["T", "z"]}, ["test_t", "test_z"]),
    ],
)
def test_pattern_core(pattern, values, expected_value):
    p = Pattern(pattern)
    assert p.substitute(values) == expected_value
