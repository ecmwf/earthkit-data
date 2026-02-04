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
    "key,expected_value",
    [
        ("shortName", "2t"),
        ("units", "K"),
        ("level", 0),
        ("level:l", 0),
        ("level:int", 0),
        ("shortName:s", "2t"),
        ("shortName:str", "2t"),
        ("centre", "ecmf"),
        ("centre:l", 98),
        (["shortName"], ["2t"]),
        (["shortName", "level"], ["2t", 0]),
        (("shortName"), "2t"),
        (("shortName", "level"), ("2t", 0)),
        ("time.base_datetime", None),  # time part of field
        ("vertical.level", 0),  # vertical GRIB namespace! not the vertical part of field
        ("time.dataDate", 20170427),  # time GRIB namespace
        ("mars.date", 20170427),  # mars GRIB namespace
    ],
)
def test_grib_metadata_core_field(fl_type, key, expected_value):
    ds, _ = load_grib_data("test_single.grib", fl_type, folder="data")

    res = ds[0].metadata(key)
    assert res == expected_value, f"{key=}"


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,expected_value",
    [
        ("shortName", ["2t"]),
        ("units", ["K"]),
        ("level", [0]),
        ("level:l", [0]),
        ("level:int", [0]),
        ("shortName:s", ["2t"]),
        ("shortName:str", ["2t"]),
        ("centre", ["ecmf"]),
        ("centre:l", [98]),
        (["shortName"], [["2t"]]),
        (["shortName", "level"], [["2t", 0]]),
        (("shortName"), ["2t"]),
        (("shortName", "level"), [("2t", 0)]),
        ("time.base_datetime", [None]),  # time part of field
        ("vertical.level", [0]),  # vertical GRIB namespace! not the vertical part of field
        ("time.dataDate", [20170427]),  # time GRIB namespace
        ("mars.date", [20170427]),  # mars GRIB namespace
    ],
)
def test_grib_metadata_core_fl(fl_type, key, expected_value):
    ds, _ = load_grib_data("test_single.grib", fl_type, folder="data")

    res = ds.get(key)
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
    "key,_kwargs,expected_value, error",
    [
        ("time.reference_date", {"raise_on_missing": True}, None, KeyError),
        ("time.reference_date", {"default": 0, "raise_on_missing": False}, 0, None),
        ("_badkey_", {"raise_on_missing": True}, None, KeyError),
        ("__badkey__", {"default": 0, "raise_on_missing": False}, 0, None),
        ("__badkey__", {"default": 0}, 0, None),
        (["_badkey_", "_badkey_1_"], {"default": 1, "raise_on_missing": False}, [1, 1], None),
        (["_badkey_", "_badkey_1_"], {"default": [1, 0], "raise_on_missing": False}, [1, 0], None),
    ],
)
def test_grib_metadata_missing_key_field(fl_type, key, _kwargs, expected_value, error):
    f, _ = load_grib_data("test.grib", fl_type)

    if error:
        with pytest.raises(error):
            f[0].metadata(key, **_kwargs)
    else:
        v = f[0].metadata(key, **_kwargs)
        assert v == expected_value
