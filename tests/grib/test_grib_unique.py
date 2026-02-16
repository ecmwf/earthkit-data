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

import pytest

from earthkit.data import concat

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_TYPES  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_unique_base(fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)

    ref_full = {
        "metadata.class": ("od",),
        "metadata.stream": ("oper",),
        "metadata.levtype": ("pl",),
        "metadata.type": ("an",),
        "metadata.expver": ("0001",),
        "metadata.date": (20180801,),
        "metadata.time": (1200,),
        "metadata.domain": ("g",),
        "metadata.number": (0,),
        "metadata.levelist": (300, 400, 500, 700, 850, 1000),
        "metadata.param": ("t", "u", "v"),
    }

    keys = list(ref_full.keys())

    r = ds.unique(keys, sort=True)
    assert r == ref_full

    ref = {
        "metadata.levelist": (300, 400, 500, 700, 850, 1000),
        "metadata.param": ("t", "u", "v"),
    }
    r = ds.unique(keys, sort=True, squeeze=True)
    assert r == ref

    ref = ("t", "u", "v")
    r = ds.unique("metadata.param", sort=True)
    assert r["metadata.param"] == ref

    ref = (300, 400, 500, 700, 850, 1000)
    r = ds.unique("metadata.levelist", sort=True)
    assert r["metadata.levelist"] == ref


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_unique_sel(fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)

    ref = {
        "metadata.class": ("od",),
        "metadata.stream": ("oper",),
        "metadata.levtype": ("pl",),
        "metadata.type": ("an",),
        "metadata.expver": ("0001",),
        "metadata.date": (20180801,),
        "metadata.time": (1200,),
        "metadata.domain": ("g",),
        "metadata.number": (0,),
        "metadata.levelist": (300, 400, 500, 700, 850, 1000),
        "metadata.param": ("t",),
    }

    keys = list(ref.keys())

    ds1 = ds.sel({"metadata.param": "t"})
    r = ds1.unique(keys, sort=True, squeeze=False)
    assert r == ref

    ref = {
        "metadata.levelist": (300, 400, 500, 700, 850, 1000),
    }
    r = ds1.unique(keys, sort=True, squeeze=True)
    assert r == ref


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_unique_multi(fl_type):
    f1, _ = load_grib_data("tuv_pl.grib", fl_type)
    f2, _ = load_grib_data("ml_data.grib", fl_type, folder="data")
    ds = concat(f1, f2)

    ref = {
        "metadata.class": ("od",),
        "metadata.stream": ("oper",),
        "metadata.levtype": ("ml", "pl"),
        "metadata.type": ("an", "fc"),
        "metadata.expver": ("0001",),
        "metadata.date": (20180111, 20180801),
        "metadata.time": (1200,),
        "metadata.domain": ("g",),
        "metadata.number": (0,),
        "metadata.levelist": (
            1,
            5,
            9,
            13,
            17,
            21,
            25,
            29,
            33,
            37,
            41,
            45,
            49,
            53,
            57,
            61,
            65,
            69,
            73,
            77,
            81,
            85,
            89,
            93,
            97,
            101,
            105,
            109,
            113,
            117,
            121,
            125,
            129,
            133,
            137,
            300,
            400,
            500,
            700,
            850,
            1000,
        ),
        "metadata.param": ("lnsp", "t", "u", "v"),
    }

    keys = list(ref.keys())

    r = ds.unique(keys, sort=True, squeeze=False)
    assert r == ref


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_unique_multi_sel(fl_type):
    f1, _ = load_grib_data("tuv_pl.grib", fl_type)
    f2, _ = load_grib_data("ml_data.grib", fl_type, folder="data")
    ds = concat(f1, f2)

    ref = {
        "metadata.class": ("od",),
        "metadata.stream": ("oper",),
        "metadata.levtype": ("ml", "pl"),
        "metadata.type": ("an", "fc"),
        "metadata.expver": ("0001",),
        "metadata.date": (20180111, 20180801),
        "metadata.time": (1200,),
        "metadata.domain": ("g",),
        "metadata.number": (0,),
        "metadata.levelist": (93, 500),
        "metadata.param": ("t",),
    }

    keys = list(ref.keys())

    ds1 = ds.sel({"metadata.param": "t", "metadata.levelist": [93, 500]})
    r = ds1.unique(keys, sort=True, squeeze=False)
    assert r == ref


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_unique_order_by(fl_type):
    ds, _ = load_grib_data("tuv_pl.grib", fl_type)

    ref = {
        "metadata.class": ("od",),
        "metadata.stream": ("oper",),
        "metadata.levtype": ("pl",),
        "metadata.type": ("an",),
        "metadata.expver": ("0001",),
        "metadata.date": (20180801,),
        "metadata.time": (1200,),
        "metadata.domain": ("g",),
        "metadata.number": (0,),
        "metadata.levelist": (300, 400, 500, 700, 850, 1000),
        "metadata.param": ("t", "u", "v"),
    }

    keys = list(ref.keys())

    ds1 = ds.order_by({"metadata.levelist": "descending"})
    r = ds1.unique(keys, sort=True, squeeze=False)
    assert r == ref
