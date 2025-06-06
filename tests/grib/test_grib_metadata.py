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

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_FILE  # noqa: E402
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
        ("shortName:s", "2t"),
        ("shortName:str", "2t"),
        ("centre", "ecmf"),
        ("centre:l", 98),
        ("level", 0),
        ("level:l", 0),
        ("level:int", 0),
        (["shortName"], ["2t"]),
        (["shortName", "level"], ["2t", 0]),
        (("shortName"), "2t"),
        (("shortName", "level"), ("2t", 0)),
    ],
)
def test_grib_metadata_grib(fl_type, key, expected_value):
    f, _ = load_grib_data("test_single.grib", fl_type, folder="data")
    sn = f.metadata(key)
    assert sn == [expected_value]
    sn = f[0].metadata(key)
    assert sn == expected_value


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,astype,expected_value",
    [
        ("shortName", str, "2t"),
        ("shortName", None, "2t"),
        ("centre", None, "ecmf"),
        ("centre", str, "ecmf"),
        ("centre", int, 98),
        ("level", None, 0),
        ("level", str, "0"),
        ("level", int, 0),
    ],
)
def test_grib_metadata_astype_1(fl_type, key, astype, expected_value):
    f, _ = load_grib_data("test_single.grib", fl_type, folder="data")
    sn = f.metadata(key, astype=astype)
    assert sn == [expected_value]
    sn = f[0].metadata(key, astype=astype)
    assert sn == expected_value


@pytest.mark.parametrize("fs_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,expected_value",
    [
        ("shortName", ["t", "u", "v"] * 6),
        ("shortName:s", ["t", "u", "v"] * 6),
        ("shortName:str", ["t", "u", "v"] * 6),
        ("level", repeat_list_items([1000, 850, 700, 500, 400, 300], 3)),
        ("level:l", repeat_list_items([1000, 850, 700, 500, 400, 300], 3)),
        ("level:int", repeat_list_items([1000, 850, 700, 500, 400, 300], 3)),
    ],
)
def test_grib_metadata_18(fs_type, key, expected_value):
    # f = load_grib_data("tuv_pl.grib", mode)
    ds, _ = load_grib_data("tuv_pl.grib", fs_type)
    sn = ds.metadata(key)
    assert sn == expected_value


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,astype,expected_value",
    [
        ("shortName", str, ["t", "u", "v"] * 6),
        ("shortName", None, ["t", "u", "v"] * 6),
        (
            "level",
            int,
            repeat_list_items([1000, 850, 700, 500, 400, 300], 3),
        ),
        (
            "level",
            None,
            repeat_list_items([1000, 850, 700, 500, 400, 300], 3),
        ),
    ],
)
def test_grib_metadata_astype_18(fl_type, key, astype, expected_value):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)
    sn = f.metadata(key, astype=astype)
    assert sn == expected_value


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,expected_value",
    [
        ("latitudeOfFirstGridPointInDegrees", 90.0),
        ("latitudeOfFirstGridPointInDegrees:d", 90.0),
        ("latitudeOfFirstGridPointInDegrees:float", 90.0),
    ],
)
def test_grib_metadata_double_1(fl_type, key, expected_value):
    f, _ = load_grib_data("test_single.grib", fl_type, folder="data")
    r = f.metadata(key)
    assert len(r) == 1
    assert np.isclose(r[0], expected_value)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key",
    [
        ("latitudeOfFirstGridPointInDegrees"),
        ("latitudeOfFirstGridPointInDegrees:d"),
        ("latitudeOfFirstGridPointInDegrees:float"),
    ],
)
def test_grib_metadata_double_18(fl_type, key):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    ref = [90.0] * 18
    r = f.metadata(key)
    np.testing.assert_allclose(r, ref, 0.001)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,astype",
    [
        ("latitudeOfFirstGridPointInDegrees", None),
        ("latitudeOfFirstGridPointInDegrees", float),
    ],
)
def test_grib_metadata_double_astype_18(fl_type, key, astype):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    ref = [90.0] * 18

    r = f.metadata(key, astype=astype)
    np.testing.assert_allclose(r, ref, 0.001)


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_get_long_array_1(fl_type):
    f, _ = load_grib_data("rgg_small_subarea_cellarea_ref.grib", fl_type, folder="data")

    assert len(f) == 1
    pl = f.metadata("pl")
    assert len(pl) == 1
    pl = pl[0]
    assert isinstance(pl, np.ndarray)
    assert len(pl) == 73
    assert pl[0] == 24
    assert pl[1] == 28
    assert pl[20] == 104
    assert pl[72] == 312


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_get_double_array_values_1(fl_type):
    f, _ = load_grib_data("test_single.grib", fl_type, folder="data")

    v = f.metadata("values")
    assert len(v) == 1
    v = v[0]
    assert isinstance(v, np.ndarray)
    eps = 1e-5
    check_array(
        v,
        (84,),
        first=260.43560791015625,
        last=227.18560791015625,
        meanv=274.36566743396577,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_get_double_array_values_18(fl_type):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)
    v = f.metadata("values")
    assert isinstance(v, list)
    assert len(v) == 18
    for d in v:
        assert isinstance(d, np.ndarray)
        assert d.shape == (84,)

    eps = 1e-5
    check_array(
        v[0],
        (84,),
        first=272.5642,
        last=240.56417846679688,
        meanv=279.70703560965404,
        eps=eps,
    )

    check_array(
        v[15],
        (84,),
        first=226.6531524658203,
        last=206.6531524658203,
        meanv=227.84362865629652,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_get_double_array_1(fl_type):
    f_in, _ = load_grib_data("ml_data.grib", fl_type, folder="data")

    f = f_in[0]
    # f is now a field!
    v = f.metadata("pv")
    assert isinstance(v, np.ndarray)
    assert len(v) == 276
    assert np.isclose(v[0], 0.0)
    assert np.isclose(v[1], 2.0003650188446045)
    assert np.isclose(v[20], 316.4207458496094)
    assert np.isclose(v[275], 1.0)


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_get_double_array_18(fl_type):
    f, _ = load_grib_data("ml_data.grib", fl_type, folder="data")
    v = f.metadata("pv")
    assert isinstance(v, list)
    assert len(v) == 36
    for row in v:
        assert isinstance(row, np.ndarray)
        assert len(row) == 276

    eps = 0.001
    assert np.isclose(v[0][1], 2.0003650188446045, eps)
    assert np.isclose(v[0][20], 316.4207458496094, eps)
    assert np.isclose(v[17][1], 2.0003650188446045, eps)
    assert np.isclose(v[17][20], 316.4207458496094, eps)


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_metadata_type_qualifier(fl_type):
    f_in, _ = load_grib_data("tuv_pl.grib", fl_type)
    f = f_in[0:4]

    # to str
    r = f.metadata("centre:s")
    assert r == ["ecmf", "ecmf", "ecmf", "ecmf"]
    r = f.metadata("centre:str")
    assert r == ["ecmf", "ecmf", "ecmf", "ecmf"]
    r = f.metadata("level:s")
    assert r == ["1000", "1000", "1000", "850"]
    r = f.metadata("level:str")
    assert r == ["1000", "1000", "1000", "850"]

    # to int
    r = f.metadata("centre:l")
    assert r == [98, 98, 98, 98]
    r = f.metadata("centre:int")
    assert r == [98, 98, 98, 98]
    r = f.metadata("level:d")
    assert r == [1000, 1000, 1000, 850]
    r = f.metadata("level:int")
    assert r == [1000, 1000, 1000, 850]

    # to float
    r = f.metadata("centre:d")
    assert np.allclose(np.array(r), np.array([98.0, 98.0, 98.0, 98.0]))
    assert all(isinstance(x, float) for x in r)
    r = f.metadata("centre:float")
    assert np.allclose(np.array(r), np.array([98.0, 98.0, 98.0, 98.0]))
    assert all(isinstance(x, float) for x in r)
    r = f.metadata("level:d")
    assert np.allclose(np.array(r), np.array([1000.0, 1000.0, 1000.0, 850.0]))
    assert all(isinstance(x, float) for x in r)
    r = f.metadata("level:float")
    assert np.allclose(np.array(r), np.array([1000.0, 1000.0, 1000.0, 850.0]))
    assert all(isinstance(x, float) for x in r)


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_metadata_astype_core(fl_type):
    f_in, _ = load_grib_data("tuv_pl.grib", fl_type)
    f = f_in[0:4]

    # to str
    r = f.metadata("centre", astype=None)
    assert r == ["ecmf", "ecmf", "ecmf", "ecmf"]
    r = f.metadata("centre", astype=str)
    assert r == ["ecmf", "ecmf", "ecmf", "ecmf"]
    r = f.metadata("level", astype=str)
    assert r == ["1000", "1000", "1000", "850"]

    # to int
    r = f.metadata("centre", astype=int)
    assert r == [98, 98, 98, 98]
    r = f.metadata("level", astype=int)
    assert r == [1000, 1000, 1000, 850]

    # to float
    r = f.metadata("level", astype=float)
    assert np.allclose(np.array(r), np.array([1000.0, 1000.0, 1000.0, 850.0]))
    assert all(isinstance(x, float) for x in r)

    # multi
    r = f.metadata(["level", "cfVarName"], astype=(int, None))
    assert r == [[1000, "t"], [1000, "u"], [1000, "v"], [850, "t"]]
    r = f.metadata(["level", "cfVarName"], astype=str)
    assert r == [["1000", "t"], ["1000", "u"], ["1000", "v"], ["850", "t"]]

    # non matching astype
    with pytest.raises(ValueError):
        f.metadata(["level", "cfVarName", "centre"], astype=(int, None))


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_metadata_generic(fl_type):
    f_full, _ = load_grib_data("tuv_pl.grib", fl_type)

    f = f_full[0:4]

    sn = f.metadata("shortName")
    assert sn == ["t", "u", "v", "t"]
    sn = f.metadata(["shortName"])
    assert sn == [["t"], ["u"], ["v"], ["t"]]
    lg = f.metadata("level", "cfVarName")
    assert lg == [(1000, "t"), (1000, "u"), (1000, "v"), (850, "t")]
    lg = f.metadata(["level", "cfVarName"])
    assert lg == [[1000, "t"], [1000, "u"], [1000, "v"], [850, "t"]]
    lg = f.metadata("level", "cfVarName")
    assert lg == [(1000, "t"), (1000, "u"), (1000, "v"), (850, "t")]

    # single fieldlist
    f = f_full
    f = f.sel(param="t", level=1000)
    lg = f.metadata(["level", "cfVarName"])
    assert lg == [[1000, "t"]]

    # single field
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))[0]
    lg = f.metadata(["level", "cfVarName"])
    assert lg == [1000, "t"]


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_metadata_missing_value(fl_type):
    f, _ = load_grib_data("ml_data.grib", fl_type, folder="data")

    with pytest.raises(KeyError):
        f[0].metadata("scaleFactorOfSecondFixedSurface")

    v = f[0].metadata("scaleFactorOfSecondFixedSurface", default=None)
    assert v is None


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_metadata_missing_key(fl_type):
    f, _ = load_grib_data("test.grib", fl_type)

    with pytest.raises(KeyError):
        f[0].metadata("_badkey_")

    v = f[0].metadata("__badkey__", default=0)
    assert v == 0


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_metadata_namespace(fl_type):
    f, _ = load_grib_data("test6.grib", fl_type)

    r = f[0].metadata(namespace="vertical")
    ref = {"level": 1000, "typeOfLevel": "isobaricInhPa"}
    assert r == ref

    r = f[0].metadata(namespace=["vertical", "time"])
    ref = {
        "vertical": {"typeOfLevel": "isobaricInhPa", "level": 1000},
        "time": {
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

    # The number/order of metadata keys can vary with the ecCodes version.
    # The same is true for the namespaces.

    r = f[0].metadata(namespace=None)
    assert isinstance(r, dict)
    md_num = len(r)
    assert md_num > 100
    assert r["level"] == 1000
    assert r["stepType"] == "instant"

    r = f[0].metadata(namespace=[None])
    assert isinstance(r, dict)
    assert len(r) == md_num
    assert r["level"] == 1000
    assert r["stepType"] == "instant"

    r = f[0].metadata(namespace="")
    assert isinstance(r, dict)
    assert len(r) == md_num
    assert r["level"] == 1000
    assert r["stepType"] == "instant"

    r = f[0].metadata(namespace=[""])
    assert isinstance(r, dict)
    assert len(r) == md_num
    assert r["level"] == 1000
    assert r["stepType"] == "instant"

    ref = {
        "geography",
        "statistics",
        "vertical",
        "time",
        "parameter",
        "mars",
        "ls",
        "default",
    }
    r = f[0].metadata(namespace=all)
    assert isinstance(r, dict)
    assert set(r.keys()) == ref

    r = f[0].metadata(namespace=[all])
    assert isinstance(r, dict)
    assert set(r.keys()) == ref

    with pytest.raises(ValueError) as excinfo:
        r = f[0].metadata("level", namespace=["vertical", "time"])
    assert "must be a str when key specified" in str(excinfo.value)

    with pytest.raises(ValueError) as excinfo:
        r = f[0].metadata("level", namespace=["vertical", "time"])
    assert "must be a str when key specified" in str(excinfo.value)


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_datetime(fl_type):
    s, _ = load_grib_data("test.grib", fl_type)

    ref = {
        "base_time": [datetime.datetime(2020, 5, 13, 12)],
        "valid_time": [datetime.datetime(2020, 5, 13, 12)],
    }
    assert s.datetime() == ref

    s = from_source(
        "dummy-source",
        kind="grib",
        paramId=[129, 130],
        date=[19900101, 19900102],
        level=[1000, 500],
    )
    ref = {
        "base_time": [
            datetime.datetime(1990, 1, 1, 12, 0),
            datetime.datetime(1990, 1, 2, 12, 0),
        ],
        "valid_time": [
            datetime.datetime(1990, 1, 1, 12, 0),
            datetime.datetime(1990, 1, 2, 12, 0),
        ],
    }
    assert s.datetime() == ref


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_valid_datetime(fl_type):
    ds, _ = load_grib_data("t_time_series.grib", fl_type, folder="data")
    f = ds[4]

    assert f.metadata("valid_datetime") == "2020-12-21T18:00:00"


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_message(fl_type):
    f, _ = load_grib_data("test.grib", fl_type)
    v = f[0].message()
    assert len(v) == 526
    assert v[:4] == b"GRIB"
    v = f[1].message()
    assert len(v) == 526
    assert v[:4] == b"GRIB"


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_tilde_shortname(fl_type):
    f, _ = load_grib_data("tilde_shortname.grib", fl_type, folder="data")

    assert f[0].metadata("shortName") == "106"
    assert f[0].metadata("shortName", astype=int) == 0
    assert f[0].metadata("paramId") == 106
    assert f[0].metadata("paramId", astype=int) == 106
    assert f[0].metadata("param") == "106"

    assert f[0].metadata(namespace="mars")["param"] == "106"
    assert f[0].metadata(namespace="parameter")["shortName"] == "106"


def test_grib_gridspec_key():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    ds[0].metadata("gridSpec", default=None)  # Should not raise an error
    ds.metadata("gridSpec", default=None)  # Should not raise an error


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
