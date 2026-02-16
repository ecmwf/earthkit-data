#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import sys

import numpy as np
import pytest

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_TYPES  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402


def check_array(v, shape=None, first=None, last=None, meanv=None, eps=1e-3):
    assert v.shape == shape
    assert np.isclose(v[0], first, eps)
    assert np.isclose(v[-1], last, eps)
    assert np.isclose(v.mean(), meanv, eps)


def repeat_list_items(items, count):
    return sum([[x] * count for x in items], [])


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,expected_value,error",
    [
        ("shortName", "2t", None),
        ("units", "K", None),
        ("level", 0, None),
        ("level:l", 0, None),
        ("level:int", 0, None),
        ("shortName:s", "2t", None),
        ("shortName:str", "2t", None),
        ("centre", "ecmf", None),
        ("centre:l", 98, None),
        (["shortName"], ["2t"], None),
        (["shortName", "level"], ["2t", 0], None),
        (("shortName"), "2t", None),
        (("shortName", "level"), ("2t", 0), None),
        ("time.base_datetime", None, KeyError),  # time part of field
        ("vertical.level", 0, None),  # vertical GRIB namespace! not the vertical component of field
        ("time.dataDate", 20170427, None),  # time GRIB namespace
        ("mars.date", 20170427, None),  # mars GRIB namespace
    ],
)
def test_grib_metadata_core_field(fl_type, key, expected_value, error):
    ds, _ = load_grib_data("test_single.grib", fl_type, folder="data")

    if error:
        with pytest.raises(error):
            ds[0].metadata(key)
    else:
        res = ds[0].metadata(key)
        assert res == expected_value, f"{key=}"


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,expected_value,error",
    [
        ("shortName", ["2t"], None),
        ("units", ["K"], None),
        ("level", [0], None),
        ("level:l", [0], None),
        ("level:int", [0], None),
        ("shortName:s", ["2t"], None),
        ("shortName:str", ["2t"], None),
        ("centre", ["ecmf"], None),
        ("centre:l", [98], None),
        (["shortName"], [["2t"]], None),
        (["shortName", "level"], [["2t", 0]], None),
        (("shortName"), ["2t"], None),
        (("shortName", "level"), [("2t", 0)], None),
        ("time.base_datetime", [None], KeyError),  # time component of field
        ("vertical.level", [0], None),  # vertical GRIB namespace! not the vertical component of field
        ("time.dataDate", [20170427], None),  # time GRIB namespace
        ("mars.date", [20170427], None),  # mars GRIB namespace
    ],
)
def test_grib_metadata_core_fl(fl_type, key, expected_value, error):
    ds, _ = load_grib_data("test_single.grib", fl_type, folder="data")

    if error:
        with pytest.raises(error):
            ds.metadata(key)
    else:
        res = ds.metadata(key)
        assert res == expected_value, f"{key=}"


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,expected_value",
    [
        ("metadata.shortName", "2t"),
        ("metadata.units", "K"),
        ("metadata.level", 0),
        ("metadata.level:l", 0),
        ("metadata.level:int", 0),
        ("metadata.shortName:s", "2t"),
        ("metadata.shortName:str", "2t"),
        ("metadata.centre", "ecmf"),
        ("metadata.centre:l", 98),
        (["metadata.shortName"], ["2t"]),
        (["metadata.shortName", "metadata.level"], ["2t", 0]),
        (("metadata.shortName"), "2t"),
        (("metadata.shortName", "metadata.level"), ("2t", 0)),
        ("shortName", None),
    ],
)
def test_grib_metadata_core_via_get(fl_type, key, expected_value):
    ds, _ = load_grib_data("test_single.grib", fl_type, folder="data")

    res = ds[0].get(key)
    assert res == expected_value


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "keys",
    [
        "_badkey_",
        ["_badkey_"],
        ("_badkey_", "_badkey_1_"),
        ["shortName", "_badkey_"],
        ["_badkey_", "shortName"],
    ],
)
def test_grib_metadata_missing_key(fl_type, keys):
    ds, _ = load_grib_data("test.grib", fl_type)

    with pytest.raises(KeyError):
        ds[0].metadata(keys)

    with pytest.raises(KeyError):
        ds.metadata(keys)
