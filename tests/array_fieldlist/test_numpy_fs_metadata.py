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
import os
import sys

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from array_fl_fixtures import load_array_fl  # noqa: E402
from array_fl_fixtures import load_array_fl_file  # noqa: E402

# Note: Almost all grib metadata tests are also run for numpyfs.
# See grib/test_grib_metadata.py


def test_array_fl_field_repr():
    ds, _ = load_array_fl(1)

    t = repr(ds[0])
    assert t
    # assert t == "ArrayField(2t,None,20200513,1200,0,0)"


def test_array_fl_values_metadata_basic():
    ds, _ = load_array_fl(1)

    # values metadata
    # keys = [
    #     "min",
    #     "max",
    #     "avg",
    #     "ds",
    #     "skew",
    #     "kurt",
    #     "isConstant",
    #     "const",
    #     "bitmapPresent",
    #     "numberOfMissing",
    #     "values",
    # ]
    # for k in keys:
    #     assert ds[0].metadata(k, default=None) is None, k
    #     with pytest.raises(KeyError):
    #         ds[0].metadata(k)

    # bits per value must be kept from the original GRIB data
    assert ds[0].get("grib.bitsPerValue") == 16


def test_array_fl_values_metadata_internal():
    ds, _ = load_array_fl(1)

    keys = {
        "param": "2t",
        "grib.shortName": "2t",
    }

    for k, v in keys.items():
        assert ds[0].get(k) == v, k


def test_array_fl_metadata_keys():
    ds, _ = load_array_fl(1)

    # The number/order of metadata keys can vary with the ecCodes version.
    # The same is true for the namespaces.

    md = ds[0].metadata()
    md_num = len(md)
    assert md_num > 100

    keys = md.keys()
    assert len(keys) == md_num

    for k in md.keys():
        assert isinstance(k, str)
        assert k != ""
        break

    items = md.items()
    assert len(list(items)) == md_num

    for k, v in md.items():
        assert isinstance(k, str)
        assert k != ""
        assert v is not None
        break

    assert "max" not in md
    assert "maximum" not in md
    assert "statistics.max" not in md
    assert "validityDate" in md


def test_array_fl_namespace():
    f, _ = load_array_fl_file("tuv_pl.grib")

    r = f[0].namespace("vertical")
    ref = {"vertical": {"level": 1000, "level_type": "pressure"}}
    assert r == ref

    r = f[0].namespace(["vertical", "time"])
    ref = {
        "vertical": {"level": 1000, "level_type": "pressure"},
        "time": {
            "base_datetime": datetime.datetime(2018, 8, 1, 12, 0),
            "step": datetime.timedelta(0),
            "valid_datetime": datetime.datetime(2018, 8, 1, 12, 0),
        },
    }

    assert r == ref

    ref = {
        "geography",
        "vertical",
        "time",
        "parameter",
        "ensemble",
    }

    r = f[0].namespace()
    assert isinstance(r, dict)
    assert set(r.keys()) == ref

    r = f[0].namespace(all)
    assert isinstance(r, dict)
    assert set(r.keys()) == ref

    r = f[0].namespace([all])
    assert isinstance(r, dict)
    assert set(r.keys()) == ref


# @pytest.mark.migrate
def test_array_fl_grib_namespace():
    f, _ = load_array_fl_file("tuv_pl.grib")

    r = f[0].namespace("grib.vertical")
    ref = {"grib.vertical": {"level": 1000, "typeOfLevel": "isobaricInhPa"}}

    assert r == ref

    r = f[0].namespace(["grib.vertical", "grib.time"])
    ref = {
        "grib.vertical": {"typeOfLevel": "isobaricInhPa", "level": 1000},
        "grib.time": {
            "dataDate": 20180801,
            "dataTime": 1200,
            "stepUnits": 1,
            "stepType": "instant",
            "stepRange": "0",
            "startStep": 0,
            "endStep": 0,
            "validityDate": 20180801,
            "validityTime": 1200,
        },
    }
    assert r == ref

    ref = {
        "grib.geography",
        "grib.vertical",
        "grib.time",
        "grib.parameter",
        "grib.mars",
        "grib.ls",
        "grib.statistics",
    }

    r = f[0].namespace("grib")
    assert isinstance(r, dict)
    assert set(r.keys()) == ref


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
