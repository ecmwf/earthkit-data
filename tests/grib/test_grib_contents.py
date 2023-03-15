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

from emohawk import load_from
from emohawk.core.temporary import temp_file
from emohawk.testing import emohawk_examples_file, emohawk_test_data_file


def check_array(v, shape=None, first=None, last=None, meanv=None, eps=1e-3):
    assert v.shape == shape
    assert np.isclose(v[0], first, eps)
    assert np.isclose(v[-1], last, eps)
    assert np.isclose(v.mean(), meanv, eps)


def test_grib_get_string_1():
    f = load_from("file", emohawk_test_data_file("test_single.grib"))
    for name in ("shortName", "shortName:s", "shortName:str"):
        sn = f.metadata(name)
        assert sn == ["2t"]
        sn = f[0][name]
        assert sn == "2t"


def test_grib_get_string_18():
    f = load_from("file", emohawk_examples_file("tuv_pl.grib"))
    for name in ("shortName", "shortName:s", "shortName:str"):
        sn = f.metadata(name)
        assert sn == ["t", "u", "v"] * 6
        # sn = f[name]
        # assert sn == ["t", "u", "v"] * 6


def test_grib_get_long_1():
    f = load_from("file", emohawk_test_data_file("test_single.grib"))
    for name in ("level", "level:l", "level:int"):
        r = f.metadata(name)
        assert r == [0]
        r = f[0][name]
        assert r == 0


def test_grib_get_long_18():
    f = load_from("file", emohawk_examples_file("tuv_pl.grib"))
    ref = (
        ([1000] * 3)
        + ([850] * 3)
        + ([700] * 3)
        + ([500] * 3)
        + ([400] * 3)
        + ([300] * 3)
    )

    for name in ("level", "level:l", "level:int"):
        r = f.metadata(name)
        assert r == ref
        # r = f[name]
        # assert r == ref


def test_grib_get_double_1():
    f = load_from("file", emohawk_test_data_file("test_single.grib"))
    for name in ("max", "max:d", "max:float"):
        r = f.metadata(name)
        assert len(r) == 1
        r = r[0]
        assert np.isclose(r, 307.18560791015625)
        # r = f[name]
        # assert np.isclose(r, 316.061)


def test_grib_get_double_18():
    f = load_from("file", emohawk_examples_file("tuv_pl.grib"))

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

    for name in ("max", "max:d", "max:float"):
        r = f.metadata(name)
        np.testing.assert_allclose(r, ref, 0.001)
        # r = f[name]
        # np.testing.assert_allclose(r, ref, 0.001)


def test_grib_get_long_array_1():
    f = load_from("file", emohawk_test_data_file("rgg_small_subarea_cellarea_ref.grib"))
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
    f = load_from("file", emohawk_test_data_file("test_single.grib"))
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
    f = load_from("file", emohawk_examples_file("tuv_pl.grib"))
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
    f = load_from("file", emohawk_test_data_file("ml_data.grib"))[0]
    # f is now a field!
    v = f.metadata("pv")
    assert isinstance(v, np.ndarray)
    assert len(v) == 276
    assert np.isclose(v[0], 0.0)
    assert np.isclose(v[1], 2.0003650188446045)
    assert np.isclose(v[20], 316.4207458496094)
    assert np.isclose(v[275], 1.0)


def test_grib_get_double_array_18():
    f = load_from("file", emohawk_test_data_file("ml_data.grib"))
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


def test_grib_get_generic():
    f = load_from("file", emohawk_examples_file("tuv_pl.grib"))
    f = f.sel(count=[1, 2, 3, 4])

    sn = f.metadata(["shortName"])
    assert sn == [["t"], ["u"], ["v"], ["t"]]
    cs = f.metadata(["centre:s"])
    assert cs == [["ecmf"], ["ecmf"], ["ecmf"], ["ecmf"]]
    cl = f.metadata(["centre:l"])
    assert cl == [[98], [98], [98], [98]]
    lg = f.metadata(["level:d", "cfVarName"])
    assert lg == [[1000, "t"], [1000, "u"], [1000, "v"], [850, "t"]]
    # lgk = f.metadata(["level:d", "cfVarName"], "key")
    # assert lgk == [[1000, 1000, 1000, 850], ["t", "u", "v", "t"]]
    # with pytest.raises(ValueError):
    #     lgk = f.metadata(["level:d", "cfVarName"], "invalid")

    # single fieldlist
    f = load_from("file", emohawk_examples_file("tuv_pl.grib"))
    f = f.sel(count=[1])
    lg = f.metadata(["level", "cfVarName"])
    assert lg == [[1000, "t"]]

    # single field
    f = load_from("file", emohawk_examples_file("tuv_pl.grib"))[0]
    lg = f.metadata(["level", "cfVarName"])
    assert lg == [1000, "t"]


def test_grib_metadata_namespace():
    f = load_from("file", emohawk_examples_file("test6.grib"))

    r = f[0].metadata(namespace="vertical")
    ref = {"level": 1000, "typeOfLevel": "isobaricInhPa"}
    assert r == ref

    with pytest.raises(ValueError):
        f[0].metadata("param", namespace="vertical")


def test_grib_values_1():
    f = load_from("file", emohawk_test_data_file("test_single.grib"))

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
    f = load_from("file", emohawk_examples_file("tuv_pl.grib"))

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
    f = load_from("file", emohawk_test_data_file("test_single.grib"))

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
        (False, {}, (1, 84)),
        (False, {"flatten": True}, (1, 84)),
        (False, {"flatten": False}, (1, 7, 12)),
        (True, {}, (84,)),
        (True, {"flatten": True}, (84,)),
        (True, {"flatten": False}, (7, 12)),
    ],
)
def test_grib_to_numpy_1_shape(first, options, expected_shape):
    f = load_from("file", emohawk_test_data_file("test_single.grib"))

    v_ref = f[0].to_numpy().flatten()
    eps = 1e-5

    data = f[0] if first else f
    v1 = data.to_numpy(**options)
    assert isinstance(v1, np.ndarray)
    assert v1.shape == expected_shape
    v1 = v1.flatten()
    assert np.allclose(v_ref, v1, eps)


def test_grib_to_numpy_18():
    f = load_from("file", emohawk_examples_file("tuv_pl.grib"))

    eps = 1e-5

    # whole file
    v = f.to_numpy()
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
                84,
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
    f = load_from("file", emohawk_examples_file("tuv_pl.grib"))

    eps = 1e-5

    # whole file
    v = f.to_numpy()
    assert isinstance(v, np.ndarray)
    assert v.shape == (18, 84)
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


def test_grib_values_with_missing():
    f = load_from("file", emohawk_test_data_file("test_single_with_missing.grib"))

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


def test_grib_to_points_1():
    f = load_from("file", emohawk_test_data_file("test_single.grib"))

    eps = 1e-5
    v = f[0].to_points()
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


def test_grib_to_points_1_shape():
    f = load_from("file", emohawk_test_data_file("test_single.grib"))

    v = f[0].to_points(flatten=False)
    assert isinstance(v, dict)
    assert isinstance(v["x"], np.ndarray)
    assert isinstance(v["y"], np.ndarray)

    # x
    assert v["x"].shape == (7, 12)
    for x in v["x"]:
        assert np.allclose(x, np.linspace(0, 330, 12))

    # y
    assert v["y"].shape == (7, 12)
    for i, y in enumerate(v["y"]):
        assert np.allclose(y, np.ones(12) * (90 - i * 30))


def test_grib_datetime():

    s = load_from("file", emohawk_examples_file("test.grib"))

    assert s.to_datetime() == datetime.datetime(2020, 5, 13, 12), s.to_datetime()

    assert s.to_datetime_list() == [
        datetime.datetime(2020, 5, 13, 12)
    ], s.to_datetime_list()

    s = load_from(
        "dummy-source",
        kind="grib",
        paramId=[129, 130],
        date=[19900101, 19900102],
        level=[1000, 500],
    )
    assert s.to_datetime_list() == [
        datetime.datetime(1990, 1, 1, 12, 0),
        datetime.datetime(1990, 1, 2, 12, 0),
    ], s.to_datetime_list()


def test_bbox():
    s = load_from("file", emohawk_examples_file("test.grib"))
    assert s.to_bounding_box().as_tuple() == (73, -27, 33, 45), s.to_bounding_box()


def test_grib_proj_string_ll():
    f = load_from("file", emohawk_examples_file("test.grib"))
    r = f[0].to_proj()
    assert len(r) == 2
    assert r[0] is None
    assert r[1] is None


def test_grib_proj_string_mercator():
    f = load_from("file", emohawk_test_data_file("mercator.grib"))
    assert f[0].to_proj() == (
        "EPSG:4326",
        "+proj=merc +lat_ts=20.000000 +lat_0=0 +lon_0=0 +x_0=0 +y_0=0 +R=6371200.000000",
    )


def test_message():
    f = load_from("file", emohawk_examples_file("test.grib"))
    v = f[0].message()
    assert len(v) == 526
    assert v[:4] == b"GRIB"
    v = f[1].message()
    assert len(v) == 526
    assert v[:4] == b"GRIB"


def test_grib_from_memory():
    with open(emohawk_test_data_file("test_single.grib"), "rb") as f:
        data = f.read()
        fs = load_from("memory", data)
        assert len(fs) == 1
        sn = fs.metadata("param")
        assert sn == ["2t"]


def test_grib_from_stream_single_iter():
    with open(emohawk_examples_file("test6.grib"), "rb") as stream:
        fs = load_from("stream", stream)

        # no methods are available
        with pytest.raises(TypeError):
            len(fs)

        ref = ["t", "u", "v", "t", "u", "v"]
        val = []
        for f in fs:
            v = f.metadata("param")
            val.append(v)

        assert val == ref

        # no data is available
        i = 0
        for f in fs:
            i += 1
        assert i == 0


def test_grib_from_stream_in_memory():
    with open(emohawk_examples_file("test6.grib"), "rb") as stream:
        fs = load_from("stream", stream, single_iter=False)

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
    fs = load_from("file", emohawk_examples_file("test6.grib"))
    assert len(fs) == 6
    with temp_file() as tmp:
        fs.save(tmp)
        fs_saved = load_from("file", tmp)
        assert len(fs) == len(fs_saved)


def test_grib_save_when_loaded_from_memory():
    with open(emohawk_test_data_file("test_single.grib"), "rb") as f:
        data = f.read()
        fs = load_from("memory", data)
        with temp_file() as tmp:
            fs.save(tmp)
            fs_saved = load_from("file", tmp)
            assert len(fs) == len(fs_saved)


def test_grib_save_when_loaded_from_stream():
    with open(emohawk_examples_file("test6.grib"), "rb") as stream:
        fs = load_from("stream", stream, single_iter=False)
        assert len(fs) == 6
        with temp_file() as tmp:
            fs.save(tmp)
            fs_saved = load_from("file", tmp)
            assert len(fs) == len(fs_saved)


if __name__ == "__main__":
    from emohawk.testing import main

    main()
