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

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_examples_file, earthkit_test_data_file
from earthkit.data.utils import projections


def check_array(v, shape=None, first=None, last=None, meanv=None, eps=1e-3):
    assert v.shape == shape
    assert np.isclose(v[0], first, eps)
    assert np.isclose(v[-1], last, eps)
    assert np.isclose(v.mean(), meanv, eps)


def repeat_list_items(items, count):
    return sum([[x] * count for x in items], [])


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
def test_grib_metadata_grib(key, expected_value):
    f = from_source("file", earthkit_test_data_file("test_single.grib"))
    sn = f.metadata(key)
    assert sn == [expected_value]
    sn = f[0].metadata(key)
    assert sn == expected_value


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
def test_grib_metadata_astype_1(key, astype, expected_value):
    f = from_source("file", earthkit_test_data_file("test_single.grib"))
    sn = f.metadata(key, astype=astype)
    assert sn == [expected_value]
    sn = f[0].metadata(key, astype=astype)
    assert sn == expected_value


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
def test_grib_metadata_18(key, expected_value):
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))
    sn = f.metadata(key)
    assert sn == expected_value


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
def test_grib_metadata_astype_18(key, astype, expected_value):
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))
    sn = f.metadata(key, astype=astype)
    assert sn == expected_value


@pytest.mark.parametrize(
    "key,expected_value",
    [
        ("max", 307.18560791015625),
        ("max:d", 307.18560791015625),
        ("max:float", 307.18560791015625),
    ],
)
def test_grib_metadata_double_1(key, expected_value):
    f = from_source("file", earthkit_test_data_file("test_single.grib"))
    r = f.metadata(key)
    assert len(r) == 1
    assert np.isclose(r[0], expected_value)


@pytest.mark.parametrize(
    "key",
    [
        ("max"),
        ("max:d"),
        ("max:float"),
    ],
)
def test_grib_metadata_double_18(key):
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))

    ref = [
        320.5641784667969,
        17.713119506835938,
        11.833480834960938,
        304.53916931152344,
        27.10162353515625,
        12.660964965820312,
        287.26531982421875,
        28.145523071289062,
        15.6385498046875,
        271.8430633544922,
        36.74000549316406,
        15.009902954101562,
        264.00323486328125,
        46.213775634765625,
        23.949615478515625,
        250.6531524658203,
        58.45549011230469,
        36.92034912109375,
    ]

    r = f.metadata(key)
    np.testing.assert_allclose(r, ref, 0.001)


@pytest.mark.parametrize(
    "key,astype",
    [
        ("max", None),
        ("max", float),
    ],
)
def test_grib_metadata_double_astype_18(key, astype):
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))

    ref = [
        320.5641784667969,
        17.713119506835938,
        11.833480834960938,
        304.53916931152344,
        27.10162353515625,
        12.660964965820312,
        287.26531982421875,
        28.145523071289062,
        15.6385498046875,
        271.8430633544922,
        36.74000549316406,
        15.009902954101562,
        264.00323486328125,
        46.213775634765625,
        23.949615478515625,
        250.6531524658203,
        58.45549011230469,
        36.92034912109375,
    ]

    r = f.metadata(key, astype=astype)
    np.testing.assert_allclose(r, ref, 0.001)


def test_grib_get_long_array_1():
    f = from_source(
        "file", earthkit_test_data_file("rgg_small_subarea_cellarea_ref.grib")
    )
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


def test_grib_get_double_array_values_1():
    f = from_source("file", earthkit_test_data_file("test_single.grib"))
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


def test_grib_get_double_array_values_18():
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))
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


def test_grib_get_double_array_1():
    f = from_source("file", earthkit_test_data_file("ml_data.grib"))[0]
    # f is now a field!
    v = f.metadata("pv")
    assert isinstance(v, np.ndarray)
    assert len(v) == 276
    assert np.isclose(v[0], 0.0)
    assert np.isclose(v[1], 2.0003650188446045)
    assert np.isclose(v[20], 316.4207458496094)
    assert np.isclose(v[275], 1.0)


def test_grib_get_double_array_18():
    f = from_source("file", earthkit_test_data_file("ml_data.grib"))
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


def test_grib_metadata_generic():
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))[0:4]

    sn = f.metadata("shortName")
    assert sn == ["t", "u", "v", "t"]
    sn = f.metadata(["shortName"])
    assert sn == [["t"], ["u"], ["v"], ["t"]]
    cs = f.metadata("centre:s")
    assert cs == ["ecmf", "ecmf", "ecmf", "ecmf"]
    cl = f.metadata("centre:l")
    assert cl == [98, 98, 98, 98]
    lg = f.metadata(["level:d", "cfVarName"])
    assert lg == [[1000, "t"], [1000, "u"], [1000, "v"], [850, "t"]]
    lg = f.metadata("level", "cfVarName")
    assert lg == [(1000, "t"), (1000, "u"), (1000, "v"), (850, "t")]

    # astype
    cs = f.metadata("centre", astype=None)
    assert cs == ["ecmf", "ecmf", "ecmf", "ecmf"]
    cs = f.metadata("centre", astype=str)
    assert cs == ["ecmf", "ecmf", "ecmf", "ecmf"]
    cl = f.metadata("centre", astype=int)
    assert cl == [98, 98, 98, 98]
    lg = f.metadata(["level", "cfVarName"], astype=(int, None))
    assert lg == [[1000, "t"], [1000, "u"], [1000, "v"], [850, "t"]]
    lg = f.metadata(["level", "cfVarName"], astype=str)
    assert lg == [["1000", "t"], ["1000", "u"], ["1000", "v"], ["850", "t"]]

    # non matching astype
    with pytest.raises(ValueError):
        f.metadata(["level", "cfVarName", "centre"], astype=(int, None))

    # lgk = f.metadata(["level:d", "cfVarName"], "key")
    # assert lgk == [[1000, 1000, 1000, 850], ["t", "u", "v", "t"]]
    # with pytest.raises(ValueError):
    #     lgk = f.metadata(["level:d", "cfVarName"], "invalid")

    # single fieldlist
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))
    f = f.sel(count=[1])
    lg = f.metadata(["level", "cfVarName"])
    assert lg == [[1000, "t"]]

    # single field
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))[0]
    lg = f.metadata(["level", "cfVarName"])
    assert lg == [1000, "t"]


def test_grib_metadata_missing_value():
    f = from_source("file", earthkit_test_data_file("ml_data.grib"))

    with pytest.raises(KeyError):
        f[0].metadata("scaleFactorOfSecondFixedSurface")

    v = f[0].metadata("scaleFactorOfSecondFixedSurface", default=None)
    assert v is None


def test_grib_metadata_missing_key():
    f = from_source("file", earthkit_examples_file("test.grib"))

    with pytest.raises(KeyError):
        f[0].metadata("_badkey_")

    v = f[0].metadata("__badkey__", default=0)
    assert v == 0


def test_grib_metadata_namespace():
    f = from_source("file", earthkit_examples_file("test6.grib"))

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

    r = f[0].metadata()
    assert isinstance(r, dict)
    for ns in ["default", "vertical", "time"]:
        assert ns in r, ns


def test_grib_values_1():
    f = from_source("file", earthkit_test_data_file("test_single.grib"))

    eps = 1e-5

    # whole file
    v = f.values
    assert isinstance(v, np.ndarray)
    assert v.shape == (1, 84)
    v = v[0].flatten()
    check_array(
        v,
        (84,),
        first=260.43560791015625,
        last=227.18560791015625,
        meanv=274.36566743396577,
        eps=eps,
    )

    # field
    v1 = f[0].values
    assert isinstance(v1, np.ndarray)
    assert v1.shape == (84,)
    assert np.allclose(v, v1, eps)


def test_grib_values_18():
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))

    eps = 1e-5

    # whole file
    v = f.values
    assert isinstance(v, np.ndarray)
    assert v.shape == (18, 84)
    vf = v[0].flatten()
    check_array(
        vf,
        (84,),
        first=272.5642,
        last=240.56417846679688,
        meanv=279.70703560965404,
        eps=eps,
    )

    vf = v[15].flatten()
    check_array(
        vf,
        (84,),
        first=226.6531524658203,
        last=206.6531524658203,
        meanv=227.84362865629652,
        eps=eps,
    )


def test_grib_to_numpy_1():
    f = from_source("file", earthkit_test_data_file("test_single.grib"))

    eps = 1e-5
    v = f.to_numpy()
    assert isinstance(v, np.ndarray)
    v = v[0].flatten()
    check_array(
        v,
        (84,),
        first=260.43560791015625,
        last=227.18560791015625,
        meanv=274.36566743396577,
        eps=eps,
    )


@pytest.mark.parametrize(
    "first,options, expected_shape",
    [
        (False, {}, (1, 7, 12)),
        (False, {"flatten": True}, (1, 84)),
        (False, {"flatten": False}, (1, 7, 12)),
        (True, {}, (7, 12)),
        (True, {"flatten": True}, (84,)),
        (True, {"flatten": False}, (7, 12)),
    ],
)
def test_grib_to_numpy_1_shape(first, options, expected_shape):
    f = from_source("file", earthkit_test_data_file("test_single.grib"))

    v_ref = f[0].to_numpy().flatten()
    eps = 1e-5

    data = f[0] if first else f
    v1 = data.to_numpy(**options)
    assert isinstance(v1, np.ndarray)
    assert v1.shape == expected_shape
    v1 = v1.flatten()
    assert np.allclose(v_ref, v1, eps)


def test_grib_to_numpy_18():
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))

    eps = 1e-5

    # whole file
    v = f.to_numpy(flatten=True)
    assert isinstance(v, np.ndarray)
    assert v.shape == (18, 84)
    vf0 = v[0].flatten()
    check_array(
        vf0,
        (84,),
        first=272.5642,
        last=240.56417846679688,
        meanv=279.70703560965404,
        eps=eps,
    )

    vf15 = v[15].flatten()
    check_array(
        vf15,
        (84,),
        first=226.6531524658203,
        last=206.6531524658203,
        meanv=227.84362865629652,
        eps=eps,
    )


@pytest.mark.parametrize(
    "options, expected_shape",
    [
        (
            {},
            (
                18,
                7,
                12,
            ),
        ),
        (
            {"flatten": True},
            (
                18,
                84,
            ),
        ),
        ({"flatten": False}, (18, 7, 12)),
    ],
)
def test_grib_to_numpy_18_shape(options, expected_shape):
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))

    eps = 1e-5

    # whole file
    v = f.to_numpy()
    assert isinstance(v, np.ndarray)
    assert v.shape == (18, 7, 12)
    vf0 = f[0].to_numpy().flatten()
    assert vf0.shape == (84,)
    vf15 = f[15].to_numpy().flatten()
    assert vf15.shape == (84,)

    v1 = f.to_numpy(**options)
    assert isinstance(v1, np.ndarray)
    assert v1.shape == expected_shape
    vr = v1[0].flatten()
    assert np.allclose(vf0, vr, eps)
    vr = v1[15].flatten()
    assert np.allclose(vf15, vr, eps)


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_grib_to_numpy_1_dtype(dtype):
    f = from_source("file", earthkit_test_data_file("test_single.grib"))

    v = f[0].to_numpy(dtype=dtype)
    assert v.dtype == dtype

    v = f.to_numpy(dtype=dtype)
    assert v.dtype == dtype


@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_grib_to_numpy_18_dtype(dtype):
    f = from_source("file", earthkit_examples_file("tuv_pl.grib"))

    v = f[0].to_numpy(dtype=dtype)
    assert v.dtype == dtype

    v = f.to_numpy(dtype=dtype)
    assert v.dtype == dtype


def test_grib_values_with_missing():
    f = from_source("file", earthkit_test_data_file("test_single_with_missing.grib"))

    v = f[0].values
    assert isinstance(v, np.ndarray)
    assert v.shape == (84,)
    eps = 0.001
    assert np.count_nonzero(np.isnan(v)) == 38
    mask = np.array([12, 14, 15, 24, 25, 26] + list(range(28, 60)))
    assert np.isclose(v[0], 260.4356, eps)
    assert np.isclose(v[11], 260.4356, eps)
    assert np.isclose(v[-1], 227.1856, eps)
    m = v[mask]
    assert len(m) == 38
    assert np.count_nonzero(np.isnan(m)) == 38


@pytest.mark.parametrize("index", [0, None])
def test_grib_to_latlon_single(index):
    f = from_source("file", earthkit_test_data_file("test_single.grib"))

    eps = 1e-5
    g = f[index] if index is not None else f
    v = g.to_latlon(flatten=True)
    assert isinstance(v, dict)
    assert isinstance(v["lon"], np.ndarray)
    assert isinstance(v["lat"], np.ndarray)
    check_array(
        v["lon"],
        (84,),
        first=0.0,
        last=330.0,
        meanv=165.0,
        eps=eps,
    )
    check_array(
        v["lat"],
        (84,),
        first=90,
        last=-90,
        meanv=0,
        eps=eps,
    )


@pytest.mark.parametrize("index", [0, None])
def test_grib_to_latlon_single_shape(index):
    f = from_source("file", earthkit_test_data_file("test_single.grib"))

    g = f[index] if index is not None else f
    v = g.to_latlon()
    assert isinstance(v, dict)
    assert isinstance(v["lon"], np.ndarray)
    assert isinstance(v["lat"], np.ndarray)

    # x
    assert v["lon"].shape == (7, 12)
    for x in v["lon"]:
        assert np.allclose(x, np.linspace(0, 330, 12))

    # y
    assert v["lat"].shape == (7, 12)
    for i, y in enumerate(v["lat"]):
        assert np.allclose(y, np.ones(12) * (90 - i * 30))


def test_grib_to_latlon_multi():
    f = from_source("file", earthkit_examples_file("test.grib"))

    v_ref = f[0].to_latlon(flatten=True)
    v = f.to_latlon(flatten=True)
    assert isinstance(v, dict)
    assert v.keys() == v_ref.keys()

    assert isinstance(v, dict)
    assert np.allclose(v["lat"], v_ref["lat"])
    assert np.allclose(v["lon"], v_ref["lon"])


def test_grib_to_latlon_multi_non_shared_grid():
    f1 = from_source("file", earthkit_examples_file("test.grib"))
    f2 = from_source("file", earthkit_examples_file("test4.grib"))
    f = f1 + f2

    with pytest.raises(ValueError):
        f.to_latlon()


@pytest.mark.parametrize("index", [0, None])
def test_grib_to_points_single(index):
    f = from_source("file", earthkit_test_data_file("test_single.grib"))

    eps = 1e-5
    g = f[index] if index is not None else f
    v = g.to_points(flatten=True)
    assert isinstance(v, dict)
    assert isinstance(v["x"], np.ndarray)
    assert isinstance(v["y"], np.ndarray)
    check_array(
        v["x"],
        (84,),
        first=0.0,
        last=330.0,
        meanv=165.0,
        eps=eps,
    )
    check_array(
        v["y"],
        (84,),
        first=90,
        last=-90,
        meanv=0,
        eps=eps,
    )


def test_grib_to_points_unsupported_grid():
    f = from_source("file", earthkit_test_data_file("mercator.grib"))
    with pytest.raises(ValueError):
        f[0].to_points()


def test_grib_to_points_multi():
    f = from_source("file", earthkit_examples_file("test.grib"))

    v_ref = f[0].to_points(flatten=True)
    v = f.to_points(flatten=True)
    assert isinstance(v, dict)
    assert v.keys() == v_ref.keys()

    assert isinstance(v, dict)
    assert np.allclose(v["x"], v_ref["x"])
    assert np.allclose(v["y"], v_ref["y"])


def test_grib_to_points_multi_non_shared_grid():
    f1 = from_source("file", earthkit_examples_file("test.grib"))
    f2 = from_source("file", earthkit_examples_file("test4.grib"))
    f = f1 + f2

    with pytest.raises(ValueError):
        f.to_points()


def test_grib_datetime():
    s = from_source("file", earthkit_examples_file("test.grib"))

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


def test_bbox():
    ds = from_source("file", earthkit_examples_file("test.grib"))
    bb = ds.bounding_box()
    assert len(bb) == 2
    for b in bb:
        assert b.as_tuple() == (73, -27, 33, 45)


@pytest.mark.parametrize("index", [0, None])
def test_grib_projection_ll(index):
    f = from_source("file", earthkit_examples_file("test.grib"))

    if index is not None:
        g = f[index]
    else:
        g = f
    assert isinstance(g.projection(), projections.EquidistantCylindrical)


def test_grib_projection_mercator():
    f = from_source("file", earthkit_test_data_file("mercator.grib"))
    projection = f[0].projection()
    assert isinstance(projection, projections.Mercator)
    assert projection.parameters == {
        "true_scale_latitude": 20,
        "central_latitude": 0,
        "central_longitude": 0,
        "false_easting": 0,
        "false_northing": 0,
    }
    assert projection.globe == dict()


def test_message():
    f = from_source("file", earthkit_examples_file("test.grib"))
    v = f[0].message()
    assert len(v) == 526
    assert v[:4] == b"GRIB"
    v = f[1].message()
    assert len(v) == 526
    assert v[:4] == b"GRIB"


def test_grib_from_memory():
    with open(earthkit_test_data_file("test_single.grib"), "rb") as f:
        data = f.read()
        fs = from_source("memory", data)
        assert len(fs) == 1
        sn = fs.metadata("param")
        assert sn == ["2t"]


def test_grib_from_stream_invalid_args():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(TypeError):
            from_source("stream", stream, order_by="level")

    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(TypeError):
            from_source("stream", stream, group_by=1)

    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(TypeError):
            from_source("stream", stream, group_by=["level", 1])

    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(TypeError):
            from_source("stream", stream, group_by="level", batch_size=1)

    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        with pytest.raises(ValueError):
            from_source("stream", stream, batch_size=-1)


@pytest.mark.parametrize("group_by", ["level", ["level", "gridType"]])
def test_grib_from_stream_group_by(group_by):
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream, group_by=group_by)

        # no methods are available
        with pytest.raises(TypeError):
            len(fs)

        ref = [
            [("t", 1000), ("u", 1000), ("v", 1000)],
            [("t", 850), ("u", 850), ("v", 850)],
        ]
        for i, f in enumerate(fs):
            assert len(f) == 3
            assert f.metadata(("param", "level")) == ref[i]

        # stream consumed, no data is available
        assert sum([1 for _ in fs]) == 0


def test_grib_from_stream_single_batch():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream)

        # no methods are available
        with pytest.raises(TypeError):
            len(fs)

        ref = ["t", "u", "v", "t", "u", "v"]
        val = []
        for f in fs:
            v = f.metadata("param")
            val.append(v)

        assert val == ref

        # stream consumed, no data is available
        assert sum([1 for _ in fs]) == 0


def test_grib_from_stream_multi_batch():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream, batch_size=2)

        # no methods are available
        with pytest.raises(TypeError):
            len(fs)

        ref = [["t", "u"], ["v", "t"], ["u", "v"]]
        for i, f in enumerate(fs):
            assert len(f) == 2
            f.metadata("param") == ref[i]

        # stream consumed, no data is available
        assert sum([1 for _ in fs]) == 0


def test_grib_from_stream_in_memory():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream, batch_size=0)

        assert len(fs) == 6

        ref = ["t", "u", "v", "t", "u", "v"]
        val = []

        # iteration
        for f in fs:
            v = f.metadata("param")
            val.append(v)

        assert val == ref, "iteration"

        # metadata
        val = []
        val = fs.metadata("param")
        assert val == ref, "method"


def test_grib_save_when_loaded_from_file():
    fs = from_source("file", earthkit_examples_file("test6.grib"))
    assert len(fs) == 6
    with temp_file() as tmp:
        fs.save(tmp)
        fs_saved = from_source("file", tmp)
        assert len(fs) == len(fs_saved)


def test_grib_save_when_loaded_from_memory():
    with open(earthkit_test_data_file("test_single.grib"), "rb") as f:
        data = f.read()
        fs = from_source("memory", data)
        with temp_file() as tmp:
            fs.save(tmp)
            fs_saved = from_source("file", tmp)
            assert len(fs) == len(fs_saved)


def test_grib_save_when_loaded_from_stream():
    with open(earthkit_examples_file("test6.grib"), "rb") as stream:
        fs = from_source("stream", stream, batch_size=0)
        assert len(fs) == 6
        with temp_file() as tmp:
            fs.save(tmp)
            fs_saved = from_source("file", tmp)
            assert len(fs) == len(fs_saved)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
