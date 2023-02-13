#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np

from emohawk import load_from
from emohawk.testing import emohawk_file


# @pytest.mark.skipif(("GITHUB_WORKFLOW" in os.environ) or True, reason="Not yet ready")
def test_sel_single_message():
    s = load_from("file", emohawk_file("tests/data/test_single.grib"))

    r = s.sel(shortName="2t")
    assert len(r) == 1
    assert r[0].metadata("shortName") == "2t"


def test_grib_sel_single_file():
    f = load_from("file", emohawk_file("docs/examples/tuv_pl.grib"))

    # ------------------------
    # single resulting field
    # ------------------------
    g = f.sel(shortName="u", level=700)
    assert len(g) == 1
    assert g.metadata(["shortName", "level"]) == [["u", 700]]

    g1 = f[7]
    d = g.to_numpy() - g1.to_numpy()
    assert np.allclose(d, np.zeros(len(d)))

    # ------------------------------------
    # single resulting field - paramId
    # ------------------------------------
    g = f.sel(paramId=131, level=700)
    assert len(g) == 1
    assert g.metadata(["paramId", "level"]) == [[131, 700]]

    # g = f.sel(param=131, level=700)
    # assert len(g) == 1
    # assert g.metadata(["param", "level"]) == [[131, 700]]

    # -------------------------
    # multiple resulting fields
    # -------------------------
    f = load_from("file", emohawk_file("docs/examples/tuv_pl.grib"))

    g = f.sel(shortName=["t", "u"], level=[700, 500])
    assert len(g) == 4
    assert g.metadata(["shortName", "level:l"]) == [
        ["t", 700],
        ["u", 700],
        ["t", 500],
        ["u", 500],
    ]

    # -------------------------
    # empty result
    # -------------------------
    f = load_from("file", emohawk_file("docs/examples/tuv_pl.grib"))
    g = f.sel(shortName="w")
    assert len(g) == 0

    # -------------------------
    # invalid key
    # -------------------------
    f = load_from("file", emohawk_file("docs/examples/tuv_pl.grib"))
    g = f.sel(INVALIDKEY="w")
    assert len(g) == 0

    # -------------------------
    # str or int values
    # -------------------------
    f = load_from("file", emohawk_file("docs/examples/tuv_pl.grib"))

    g = f.sel(shortName=["t"], level=[500, 700], marsType="an")
    # g = f.sel(shortName=["t"], level=["500", 700], marsType="an")
    assert len(g) == 2
    assert g.metadata(["shortName", "level:l", "marsType"]) == [
        ["t", 700, "an"],
        ["t", 500, "an"],
    ]

    f = load_from("file", emohawk_file("tests/data/t_time_series.grib"))

    g = f.sel(shortName=["t"], step=[3, 6])
    assert len(g) == 2
    assert g.metadata(["shortName", "level:l", "step:l"]) == [
        ["t", 1000, 3],
        ["t", 1000, 6],
    ]

    # repeated use
    g = f.sel(shortName=["t"], step=[3, 6])
    # g = f.sel(shortName=["t"], step=["3", "06"])
    assert len(g) == 2
    assert g.metadata(["shortName", "level:l", "step:l"]) == [
        ["t", 1000, 3],
        ["t", 1000, 6],
    ]

    # -------------------------
    # mars keys
    # -------------------------
    f = load_from("file", emohawk_file("docs/examples/tuv_pl.grib"))

    g = f.sel(shortName=["t"], level=[500, 700], marsType="an")
    assert len(g) == 2
    assert g.metadata(["shortName", "level:l", "marsType"]) == [
        ["t", 700, "an"],
        ["t", 500, "an"],
    ]

    g = f.sel({"shortName": "t", "level": [500, 700], "mars.type": "an"})
    assert len(g) == 2
    assert g.metadata(["shortName", "level:l", "mars.type"]) == [
        ["t", 700, "an"],
        ["t", 500, "an"],
    ]


def test_grib_sel_slice_single_file():
    f = load_from("file", emohawk_file("docs/examples/tuv_pl.grib"))

    # ------------------------------------
    # single resulting field
    # ------------------------------------
    g = f.sel(paramId=131, level=slice(600, 700))
    assert len(g) == 1
    assert g.metadata(["paramId", "level"]) == [[131, 700]]

    g = f.sel(paramId=131, level=slice(650, 750))
    assert len(g) == 1
    assert g.metadata(["paramId", "level"]) == [[131, 700]]

    g = f.sel(paramId=131, level=slice(1000, None))
    assert len(g) == 1
    assert g.metadata(["paramId", "level"]) == [[131, 1000]]

    g = f.sel(paramId=131, level=slice(None, 300))
    assert len(g) == 1
    assert g.metadata(["paramId", "level"]) == [[131, 300]]

    # ------------------------------------
    # multiple resulting fields
    # ------------------------------------
    g = f.sel(paramId=131, level=slice(500, 700))
    assert len(g) == 2
    assert g.metadata(["paramId", "level"]) == [[131, 700], [131, 500]]

    # -------------------------
    # empty result
    # -------------------------
    g = f.sel(paramId=131, level=slice(510, 520))
    assert len(g) == 0


def test_grib_sel_multi_file():
    f1 = load_from("file", emohawk_file("docs/examples/tuv_pl.grib"))
    f2 = load_from("file", emohawk_file("tests/data/ml_data.grib"))
    f = load_from("multi", [f1, f2])

    # single resulting field
    g = f.sel(shortName="t", level=61)
    assert len(g) == 1
    assert g.metadata(["shortName", "level:l", "typeOfLevel"]) == [["t", 61, "hybrid"]]

    g1 = f[34]
    d = g.to_numpy() - g1.to_numpy()
    assert np.allclose(d, np.zeros(len(d)))


def test_grib_sel_slice_multi_file():
    f1 = load_from("file", emohawk_file("docs/examples/tuv_pl.grib"))
    f2 = load_from("file", emohawk_file("tests/data/ml_data.grib"))
    f = load_from("multi", [f1, f2])

    g = f.sel(shortName="t", level=slice(56, 62))
    assert len(g) == 2
    assert g.metadata(["shortName", "level:l", "typeOfLevel"]) == [
        ["t", 57, "hybrid"],
        ["t", 61, "hybrid"],
    ]


def test_grib_sel_date():
    # date and time
    f = load_from("file", emohawk_file("tests/data/t_time_series.grib"))

    g = f.sel(date=20201221, time=1200, step=9)
    # g = f.sel(date="20201221", time="12", step="9")
    assert len(g) == 2

    ref_keys = ["shortName", "date", "time", "step"]
    ref = [
        ["t", 20201221, 1200, 9],
        ["z", 20201221, 1200, 9],
    ]

    assert g.metadata(ref_keys) == ref


if __name__ == "__main__":
    from emohawk.testing import main

    main()
