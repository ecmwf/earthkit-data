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
        ("parameter.variable", "2t"),
        ("parameter.units", "K"),
        ("vertical.level", 0),
        ("grib.shortName", "2t"),
        ("grib.shortName:s", "2t"),
        ("grib.shortName:str", "2t"),
        ("grib.centre", "ecmf"),
        ("grib.centre:l", 98),
        ("grib.level", 0),
        ("grib.level:l", 0),
        ("grib.level:int", 0),
        (["grib.shortName"], ["2t"]),
        (["grib.shortName", "vertical.level"], ["2t", 0]),
        (("grib.shortName"), "2t"),
        (("grib.shortName", "vertical.level"), ("2t", 0)),
    ],
)
def test_grib_get_core(fl_type, key, expected_value):
    f, _ = load_grib_data("test_single.grib", fl_type, folder="data")
    sn = f.get(key)
    assert sn == [expected_value]
    sn = f[0].get(key)
    assert sn == expected_value


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,astype,expected_value",
    [
        ("grib.shortName", str, "2t"),
        ("grib.shortName", None, "2t"),
        ("grib.centre", None, "ecmf"),
        ("grib.centre", str, "ecmf"),
        ("grib.centre", int, 98),
        ("grib.level", None, 0),
        ("grib.level", str, "0"),
        ("grib.level", int, 0),
        ("vertical.level", None, 0),
        ("vertical.level", str, "0"),
        ("vertical.level", int, 0),
    ],
)
def test_grib_get_astype_01(fl_type, key, astype, expected_value):
    f, _ = load_grib_data("test_single.grib", fl_type, folder="data")
    sn = f.get(key, astype=astype)
    assert sn == [expected_value]
    sn = f[0].get(key, astype=astype)
    assert sn == expected_value


@pytest.mark.parametrize("fs_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,expected_value",
    [
        ("grib.shortName", ["t", "u", "v"] * 6),
        ("grib.shortName:s", ["t", "u", "v"] * 6),
        ("grib.shortName:str", ["t", "u", "v"] * 6),
        ("grib.level", repeat_list_items([1000, 850, 700, 500, 400, 300], 3)),
        ("grib.level:l", repeat_list_items([1000, 850, 700, 500, 400, 300], 3)),
        ("grib.level:int", repeat_list_items([1000, 850, 700, 500, 400, 300], 3)),
        ("vertical.level", repeat_list_items([1000, 850, 700, 500, 400, 300], 3)),
    ],
)
def test_grib_get_18(fs_type, key, expected_value):
    ds, _ = load_grib_data("tuv_pl.grib", fs_type)
    sn = ds.get(key)
    assert sn == expected_value


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,astype,expected_value",
    [
        ("grib.shortName", str, ["t", "u", "v"] * 6),
        ("grib.shortName", None, ["t", "u", "v"] * 6),
        ("parameter.variable", str, ["t", "u", "v"] * 6),
        ("parameter.variable", None, ["t", "u", "v"] * 6),
        (
            "grib.level",
            int,
            repeat_list_items([1000, 850, 700, 500, 400, 300], 3),
        ),
        (
            "grib.level",
            None,
            repeat_list_items([1000, 850, 700, 500, 400, 300], 3),
        ),
        (
            "vertical.level",
            int,
            repeat_list_items([1000, 850, 700, 500, 400, 300], 3),
        ),
        (
            "vertical.level",
            None,
            repeat_list_items([1000, 850, 700, 500, 400, 300], 3),
        ),
    ],
)
def test_grib_get_astype_18(fl_type, key, astype, expected_value):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)
    sn = f.get(key, astype=astype)
    assert sn == expected_value


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,expected_value",
    [
        ("grib.latitudeOfFirstGridPointInDegrees", 90.0),
        ("grib.latitudeOfFirstGridPointInDegrees:d", 90.0),
        ("grib.latitudeOfFirstGridPointInDegrees:float", 90.0),
    ],
)
def test_grib_get_double_01(fl_type, key, expected_value):
    f, _ = load_grib_data("test_single.grib", fl_type, folder="data")
    r = f.get(key)
    assert len(r) == 1
    assert np.isclose(r[0], expected_value)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key",
    [
        ("grib.latitudeOfFirstGridPointInDegrees"),
        ("grib.latitudeOfFirstGridPointInDegrees:d"),
        ("grib.latitudeOfFirstGridPointInDegrees:float"),
    ],
)
def test_grib_get_double_18(fl_type, key):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    ref = [90.0] * 18
    r = f.get(key)
    np.testing.assert_allclose(r, ref, 0.001)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,astype",
    [
        ("grib.latitudeOfFirstGridPointInDegrees", None),
        ("grib.latitudeOfFirstGridPointInDegrees", float),
    ],
)
def test_grib_get_double_astype_18(fl_type, key, astype):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    ref = [90.0] * 18

    r = f.get(key, astype=astype)
    np.testing.assert_allclose(r, ref, 0.001)


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_get_long_array_01(fl_type):
    f, _ = load_grib_data("rgg_small_subarea_cellarea_ref.grib", fl_type, folder="data")

    assert len(f) == 1
    pl = f.get("grib.pl")
    assert len(pl) == 1
    pl = pl[0]
    assert isinstance(pl, np.ndarray)
    assert len(pl) == 73
    assert pl[0] == 24
    assert pl[1] == 28
    assert pl[20] == 104
    assert pl[72] == 312


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_get_double_array_values_01(fl_type):
    f, _ = load_grib_data("test_single.grib", fl_type, folder="data")

    v = f.get("values")
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
    v = f.get("values")
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
def test_grib_get_double_array_01(fl_type):
    f_in, _ = load_grib_data("ml_data.grib", fl_type, folder="data")

    f = f_in[0]
    # f is now a field!
    v = f.get("grib.pv")
    assert isinstance(v, np.ndarray)
    assert len(v) == 276
    assert np.isclose(v[0], 0.0)
    assert np.isclose(v[1], 2.0003650188446045)
    assert np.isclose(v[20], 316.4207458496094)
    assert np.isclose(v[275], 1.0)


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_get_double_array_18(fl_type):
    f, _ = load_grib_data("ml_data.grib", fl_type, folder="data")
    v = f.get("grib.pv")
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
def test_grib_get_type_qualifier(fl_type):
    f_in, _ = load_grib_data("tuv_pl.grib", fl_type)
    f = f_in[0:4]

    # to str
    r = f.get("grib.centre:s")
    assert r == ["ecmf", "ecmf", "ecmf", "ecmf"]
    r = f.get("grib.centre:str")
    assert r == ["ecmf", "ecmf", "ecmf", "ecmf"]
    r = f.get("grib.level:s")
    assert r == ["1000", "1000", "1000", "850"]
    r = f.get("grib.level:str")
    assert r == ["1000", "1000", "1000", "850"]

    # to int
    r = f.get("grib.centre:l")
    assert r == [98, 98, 98, 98]
    r = f.get("grib.centre:int")
    assert r == [98, 98, 98, 98]
    r = f.get("grib.level:d")
    assert r == [1000, 1000, 1000, 850]
    r = f.get("grib.level:int")
    assert r == [1000, 1000, 1000, 850]

    # to float
    r = f.get("grib.centre:d")
    assert np.allclose(np.array(r), np.array([98.0, 98.0, 98.0, 98.0]))
    assert all(isinstance(x, float) for x in r)
    r = f.get("grib.centre:float")
    assert np.allclose(np.array(r), np.array([98.0, 98.0, 98.0, 98.0]))
    assert all(isinstance(x, float) for x in r)
    r = f.get("grib.level:d")
    assert np.allclose(np.array(r), np.array([1000.0, 1000.0, 1000.0, 850.0]))
    assert all(isinstance(x, float) for x in r)
    r = f.get("grib.level:float")
    assert np.allclose(np.array(r), np.array([1000.0, 1000.0, 1000.0, 850.0]))
    assert all(isinstance(x, float) for x in r)


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_get_astype_core(fl_type):
    f_in, _ = load_grib_data("tuv_pl.grib", fl_type)
    f = f_in[0:4]

    # to str
    r = f.get("grib.centre", astype=None)
    assert r == ["ecmf", "ecmf", "ecmf", "ecmf"]
    r = f.get("grib.centre", astype=str)
    assert r == ["ecmf", "ecmf", "ecmf", "ecmf"]
    r = f.get("vertical.level", astype=str)
    assert r == ["1000", "1000", "1000", "850"]

    # to int
    r = f.get("grib.centre", astype=int)
    assert r == [98, 98, 98, 98]
    r = f.get("vertical.level", astype=int)
    assert r == [1000, 1000, 1000, 850]

    # to float
    r = f.get("vertical.level", astype=float)
    assert np.allclose(np.array(r), np.array([1000.0, 1000.0, 1000.0, 850.0]))
    assert all(isinstance(x, float) for x in r)

    # multi
    r = f.get(["vertical.level", "grib.cfVarName"], astype=(int, None))
    assert r == [[1000, "t"], [1000, "u"], [1000, "v"], [850, "t"]]
    r = f.get(["vertical.level", "grib.cfVarName"], astype=str)
    assert r == [["1000", "t"], ["1000", "u"], ["1000", "v"], ["850", "t"]]

    # non matching astype
    with pytest.raises(ValueError):
        f.get(["vertical.level", "grib.cfVarName", "grib.centre"], astype=(int, None))


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_get_generic(fl_type):
    f_full, _ = load_grib_data("tuv_pl.grib", fl_type)

    f = f_full[0:4]

    sn = f.get("grib.shortName")
    assert sn == ["t", "u", "v", "t"]
    sn = f.get(["grib.shortName"])
    assert sn == [["t"], ["u"], ["v"], ["t"]]
    sn = f.get("parameter.variable")
    assert sn == ["t", "u", "v", "t"]
    sn = f.get(["parameter.variable"])
    assert sn == [["t"], ["u"], ["v"], ["t"]]

    lg = f.get(("vertical.level", "grib.cfVarName"))
    assert lg == [(1000, "t"), (1000, "u"), (1000, "v"), (850, "t")]
    lg = f.get(["vertical.level", "grib.cfVarName"])
    assert lg == [[1000, "t"], [1000, "u"], [1000, "v"], [850, "t"]]

    # single fieldlist
    f = f_full
    f = f.sel({"parameter.variable": "t", "vertical.level": 1000})
    lg = f.get(["vertical.level", "grib.cfVarName"])
    assert lg == [[1000, "t"]]

    # single field
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))[0]
    lg = f.get(["vertical.level", "grib.cfVarName"])
    assert lg == [1000, "t"]


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_get_missing_value(fl_type):
    f, _ = load_grib_data("ml_data.grib", fl_type, folder="data")

    with pytest.raises(KeyError):
        f[0].get("grib.scaleFactorOfSecondFixedSurface", raise_on_missing=True)

    v = f[0].get("grib.scaleFactorOfSecondFixedSurface", default=None)
    assert v is None


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,_kwargs,expected_value, error",
    [
        ("_badkey_", {"raise_on_missing": True}, None, KeyError),
        ("__badkey__", {"default": 0, "raise_on_missing": False}, 0, None),
        ("__badkey__", {"default": 0}, 0, None),
        (["_badkey_", "_badkey_1_"], {"default": 1, "raise_on_missing": False}, [1, 1], None),
        (["_badkey_", "_badkey_1_"], {"default": [1, 0], "raise_on_missing": False}, [1, 0], None),
    ],
)
def test_grib_get_missing_key_field(fl_type, key, _kwargs, expected_value, error):
    f, _ = load_grib_data("test.grib", fl_type)

    if error:
        with pytest.raises(error):
            f[0].get(key, **_kwargs)
    else:
        v = f[0].get(key, **_kwargs)
        assert v == expected_value


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "key,_kwargs,expected_value, error",
    [
        ("_badkey_", {"raise_on_missing": True}, None, KeyError),
        ("__badkey__", {"default": 0, "raise_on_missing": False}, [0, 0], None),
        ("__badkey__", {"default": 0}, [0, 0], None),
        (["_badkey_", "_badkey_1_"], {"default": 1, "raise_on_missing": False}, [[1, 1], [1, 1]], None),
        (["_badkey_", "_badkey_1_"], {"default": [1, 0], "raise_on_missing": False}, [[1, 0], [1, 0]], None),
    ],
)
def test_grib_get_missing_key_fl(fl_type, key, _kwargs, expected_value, error):
    f, _ = load_grib_data("test.grib", fl_type)

    if error:
        with pytest.raises(error):
            f.get(key, **_kwargs)
    else:
        v = f.get(key, **_kwargs)
        assert v == expected_value

    # with pytest.raises(KeyError):
    #     f[0].get("_badkey_", raise_on_missing=True)

    # v = f[0].get("__badkey__", default=0, raise_on_missing=False)
    # assert v == 0

    # v = f[0].get("__badkey__", default=0)
    # assert v == 0


@pytest.mark.migrate
@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_metadata_namespace(fl_type):
    f, _ = load_grib_data("test6.grib", fl_type)

    r = f[0].metadata(namespace="vertical")
    ref = {"vertical.level": 1000, "vertical.typeOfLevel": "isobaricInhPa"}
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


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_get_message(fl_type):
    f, _ = load_grib_data("test.grib", fl_type)
    v = f[0].get("grib.message")
    assert len(v) == 526
    assert v[:4] == b"GRIB"
    v = f[1].get("grib.message")
    assert len(v) == 526
    assert v[:4] == b"GRIB"


@pytest.mark.parametrize("fl_type", FL_FILE)
def test_grib_get_tilde_shortname(fl_type):
    # the shortName is ~ in the grib file
    # but the parameter is 106
    f, _ = load_grib_data("tilde_shortname.grib", fl_type, folder="data")

    # parameter object keys
    assert f[0].get("parameter.variable") == "106"
    assert f[0].get("parameter.variable") == "106"

    # raw GRIB keys
    assert f[0].get("grib.shortName") == "106"
    assert f[0].get("grib.shortName", astype=int) == 0
    assert f[0].get("grib.paramId") == 106
    assert f[0].get("grib.paramId", astype=int) == 106
    assert f[0].get("grib.param") == "106.128"
    assert f[0].get("grib.mars.param") == "106.128"
    assert f[0].get("grib.mars.param") == "106.128"

    # TODO: decide on the expected behaviour here
    assert f[0].get("grib.parameter.shortName") == "~"
    # the old metadata() returned the parameter id
    # assert f[0].get("grib.parameter.shortName"] == "106"


def test_grib_get_gridspec_key():
    ds = from_source("file", earthkit_examples_file("test.grib"))

    ds[0].get("gridSpec", default=None)  # Should not raise an error


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "_kwargs,key,expected_value",
    [
        (
            {"output": "item_per_field"},
            "parameter.variable",
            ["2t", "msl"],
        ),
        (
            {"output": "item_per_field"},
            ["parameter.variable", "vertical.level"],
            [["2t", 0], ["msl", 0]],
        ),
        (
            {"output": "item_per_field"},
            ("parameter.variable", "vertical.level"),
            [("2t", 0), ("msl", 0)],
        ),
        (
            {"output": "item_per_key"},
            "parameter.variable",
            ["2t", "msl"],
        ),
        (
            {"output": "item_per_key"},
            ["parameter.variable", "vertical.level"],
            [["2t", "msl"], [0, 0]],
        ),
        (
            {"output": "item_per_key"},
            ("parameter.variable", "vertical.level"),
            [["2t", "msl"], [0, 0]],
        ),
        (
            {"output": "dict_per_field"},
            "parameter.variable",
            [{"parameter.variable": "2t"}, {"parameter.variable": "msl"}],
        ),
        (
            {"output": "dict_per_field"},
            ["parameter.variable", "vertical.level"],
            [
                {"parameter.variable": "2t", "vertical.level": 0},
                {"parameter.variable": "msl", "vertical.level": 0},
            ],
        ),
        (
            {"output": "dict_per_field"},
            ("parameter.variable", "vertical.level"),
            [
                {"parameter.variable": "2t", "vertical.level": 0},
                {"parameter.variable": "msl", "vertical.level": 0},
            ],
        ),
        (
            {"output": "dict_per_key"},
            "parameter.variable",
            {"parameter.variable": ["2t", "msl"]},
        ),
        (
            {"output": "dict_per_key"},
            ["parameter.variable", "vertical.level"],
            {"parameter.variable": ["2t", "msl"], "vertical.level": [0, 0]},
        ),
        (
            {"output": "dict_per_key"},
            ("parameter.variable", "vertical.level"),
            {"parameter.variable": ["2t", "msl"], "vertical.level": [0, 0]},
        ),
    ],
)
def test_grib_get_core_fl(fl_type, _kwargs, key, expected_value):
    ds, _ = load_grib_data("test.grib", fl_type)
    res = ds.get(key, **_kwargs)
    assert res == expected_value, f"fl_type={fl_type}, _kwargs={_kwargs}, key={key}"


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
