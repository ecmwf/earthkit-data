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

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.utils.unique import UniqueValuesCollector


@pytest.mark.parametrize("cache", [True, False])
@pytest.mark.parametrize(
    "keys,_kwargs,expected_result",
    [
        ("parameter.variable", {}, {"parameter.variable": ("t", "u", "v")}),
        (["parameter.variable"], {}, {"parameter.variable": ("t", "u", "v")}),
        (
            ["parameter.variable", "time.step", "vertical.level"],
            {},
            {
                "parameter.variable": ("t", "u", "v"),
                "time.step": (datetime.timedelta(hours=0),),
                "vertical.level": (1000, 850, 700, 500, 400, 300),
            },
        ),
        (
            ["parameter.variable", "time.step", "vertical.level"],
            {"sort": True},
            {
                "parameter.variable": ("t", "u", "v"),
                "time.step": (datetime.timedelta(hours=0),),
                "vertical.level": (300, 400, 500, 700, 850, 1000),
            },
        ),
        (
            ("parameter.variable", "_invalid"),
            {"drop_none": False},
            {"parameter.variable": ("t", "u", "v"), "_invalid": (None,)},
        ),
        (
            ("parameter.variable", "_invalid"),
            {"drop_none": True},
            {"parameter.variable": ("t", "u", "v"), "_invalid": tuple()},
        ),
        (
            ["parameter.variable", "_invalid", "vertical.level"],
            {"sort": True, "drop_none": True},
            {
                "parameter.variable": ("t", "u", "v"),
                "_invalid": tuple(),
                "vertical.level": (300, 400, 500, 700, 850, 1000),
            },
        ),
    ],
)
def test_unique_1(keys, _kwargs, expected_result, cache):
    ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))

    c = UniqueValuesCollector(cache=cache)

    res = c.collect(ds, keys, **_kwargs)
    assert res == expected_result

    if cache:
        # repeated use
        res = c.collect(ds, keys, **_kwargs)
        assert res == expected_result


def test_unique_cache():
    ds = from_source("file", earthkit_examples_file("tuv_pl.grib"))

    c = UniqueValuesCollector(cache=True)

    keys = ("parameter.variable", "_invalid", "time.step", "vertical.level")
    v_ref = {
        "parameter.variable": ("t", "u", "v"),
        "_invalid": tuple(),
        "time.step": (datetime.timedelta(hours=0),),
        "vertical.level": (300, 400, 500, 700, 850, 1000),
    }
    res = c.collect(ds, keys, sort=True, drop_none=True)
    assert res == v_ref

    # repeated use
    res = c.collect(ds, keys, sort=True, drop_none=True)
    assert res == v_ref

    # different order of keys
    keys = ("parameter.variable", "vertical.level", "_invalid", "time.step")
    v_ref = {
        "parameter.variable": ("t", "u", "v"),
        "vertical.level": (300, 400, 500, 700, 850, 1000),
        "_invalid": tuple(),
        "time.step": (datetime.timedelta(hours=0),),
    }
    res = c.collect(ds, keys, sort=True, drop_none=True)
    assert res == v_ref

    # additional key
    keys = ("parameter.variable", "time.base_datetime", "vertical.level")
    v_ref = {
        "parameter.variable": ("t", "u", "v"),
        "time.base_datetime": (datetime.datetime(2018, 8, 1, 12, 0),),
        "vertical.level": (300, 400, 500, 700, 850, 1000),
    }
    res = c.collect(ds, keys, sort=True, drop_none=True)
    assert res == v_ref

    # no sorting, no dropping of None
    keys = ("parameter.variable", "_invalid", "time.step", "vertical.level")
    v_ref = {
        "parameter.variable": ("t", "u", "v"),
        "_invalid": (None,),
        "time.step": (datetime.timedelta(hours=0),),
        "vertical.level": (1000, 850, 700, 500, 400, 300),
    }
    res = c.collect(ds, keys, sort=False, drop_none=False)
    assert res == v_ref
