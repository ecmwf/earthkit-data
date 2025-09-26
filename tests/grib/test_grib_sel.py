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
from earthkit.data.specs.time_span import TimeSpan
from earthkit.data.specs.time_span import TimeSpanMethod
from earthkit.data.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_TYPES  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402

# @pytest.mark.skipif(("GITHUB_WORKFLOW" in os.environ) or True, reason="Not yet ready")


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("key", ["name", "param", "shortName"])
def test_grib_sel_single_message(fl_type, key):
    s, _ = load_grib_data("test_single.grib", fl_type, folder="data")

    r = s.sel(**{key: "2t"})
    assert len(r) == 1
    assert r[0].get(key) == "2t"


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "params,expected_meta,metadata_keys",
    [
        (dict(shortName="u", level=700), [["u", 700]], []),
        (dict(paramId=131, level=700), [[131, 700]], []),
        (
            dict(shortName=["t", "u"], level=[700, 500]),
            [
                ["t", 700],
                ["u", 700],
                ["t", 500],
                ["u", 500],
            ],
            ["shortName", "level:l"],
        ),
        (dict(shortName="w"), [], []),
        (dict(INVALIDKEY="w"), [], []),
        (
            dict(shortName=["t"], level=[500, 700], marsType="an"),
            [
                ["t", 700, "an"],
                ["t", 500, "an"],
            ],
            ["shortName", "level:l", "marsType"],
        ),
    ],
)
def test_grib_sel_single_file_1(fl_type, params, expected_meta, metadata_keys):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    g = f.sel(**params)
    assert len(g) == len(expected_meta)
    if len(expected_meta) > 0:
        keys = list(params.keys())
        if metadata_keys:
            keys = metadata_keys

        assert g.get(keys) == expected_meta
    return


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_sel_single_file_2(fl_type):
    f, _ = load_grib_data("t_time_series.grib", fl_type, folder="data")

    g = f.sel(shortName=["t"], endStep=[3, 6])

    assert len(g) == 2
    assert g.get(["shortName", "level:l", "step:l"]) == [
        ["t", 1000, 3],
        ["t", 1000, 6],
    ]

    # repeated use
    g = f.sel(shortName=["t"], endStep=[3, 6])
    # g = f.sel(shortName=["t"], step=["3", "06"])
    assert len(g) == 2
    assert g.get(["shortName", "level:l", "endStep:l"]) == [
        ["t", 1000, 3],
        ["t", 1000, 6],
    ]


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_sel_single_file_as_dict(fl_type):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    g = f.sel({"shortName": "t", "level": [500, 700], "mars.type": "an"})
    assert len(g) == 2
    assert g.get(["shortName", "level:l", "mars.type"]) == [
        ["t", 700, "an"],
        ["t", 500, "an"],
    ]


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "param_id,level,expected_meta",
    [
        (131, (slice(600, 700)), [[131, 700]]),
        (131, (slice(650, 750)), [[131, 700]]),
        (131, (slice(1000, None)), [[131, 1000]]),
        (131, (slice(None, 300)), [[131, 300]]),
        (131, (slice(500, 700)), [[131, 700], [131, 500]]),
        (131, (slice(510, 520)), []),
    ],
)
def test_grib_sel_slice_single_file(fl_type, param_id, level, expected_meta):
    f, _ = load_grib_data("tuv_pl.grib", fl_type)

    g = f.sel(paramId=param_id, level=level)
    assert len(g) == len(expected_meta)
    if expected_meta:
        assert g.get(["paramId", "level"]) == expected_meta


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_sel_multi_file(fl_type):
    f1, _ = load_grib_data(
        "tuv_pl.grib",
        fl_type,
    )
    f2, _ = load_grib_data("ml_data.grib", fl_type, folder="data")
    f = from_source("multi", [f1, f2])

    # single resulting field
    g = f.sel(shortName="t", level=61)
    print(f"{g=}")
    assert len(g) == 1
    assert g.get(["shortName", "level:l", "typeOfLevel"]) == [["t", 61, "hybrid"]]

    g1 = f[34]
    d = g.to_numpy() - g1.to_numpy()
    assert np.allclose(d, np.zeros(len(d)))


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_sel_slice_multi_file(fl_type):
    f1, _ = load_grib_data("tuv_pl.grib", fl_type)
    f2, _ = load_grib_data("ml_data.grib", fl_type, folder="data")

    f = from_source("multi", [f1, f2])

    g = f.sel(shortName="t", level=slice(56, 62))
    assert len(g) == 2
    assert g.get(["shortName", "level:l", "typeOfLevel"]) == [
        ["t", 57, "hybrid"],
        ["t", 61, "hybrid"],
    ]


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_sel_date_time_step_1(fl_type):
    f, _ = load_grib_data("t_time_series.grib", fl_type, folder="data")

    g = f.sel(date=20201221, time=1200, endStep=9)
    assert len(g) == 2

    ref_keys = ["shortName", "date", "time", "endStep"]
    ref = [
        ["t", 20201221, 1200, 9],
        ["z", 20201221, 1200, 9],
    ]

    assert g.get(ref_keys) == ref


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_sel_date_time_step_2(fl_type):
    f, _ = load_grib_data("t_time_series.grib", fl_type, folder="data")

    g = f.sel(date=20201221, time=1200, step=9)
    assert len(g) == 2

    ref_keys = ["shortName", "date", "time", "step"]
    ref = [
        ["t", 20201221, 1200, datetime.timedelta(hours=9)],
        ["z", 20201221, 1200, datetime.timedelta(hours=9)],
    ]

    assert g.get(ref_keys) == ref


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_sel_date_time_step_3(fl_type):
    f, _ = load_grib_data("t_time_series.grib", fl_type, folder="data")

    g = f.sel(date=20201221, time=1200, step=datetime.timedelta(hours=9))
    assert len(g) == 2

    ref_keys = ["shortName", "date", "time", "step"]
    ref = [
        ["t", 20201221, 1200, datetime.timedelta(hours=9)],
        ["z", 20201221, 1200, datetime.timedelta(hours=9)],
    ]

    assert g.get(ref_keys) == ref


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("dval", ["2020-12-21T21:00:00", datetime.datetime(2020, 12, 21, 21, 0, 0)])
def test_grib_sel_valid_datetime(fl_type, dval):
    f, _ = load_grib_data("t_time_series.grib", fl_type, folder="data")

    g = f.sel(valid_datetime=dval)
    assert len(g) == 2

    ref_keys = ["shortName", "date", "time", "endStep"]
    ref = [
        ["t", 20201221, 1200, 9],
        ["z", 20201221, 1200, 9],
    ]

    assert g.metadata(ref_keys) == ref


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "_kwargs",
    [
        {"base_datetime": "2020-12-21T12:00:00"},
        {"base_datetime": datetime.datetime(2020, 12, 21, 12, 0, 0)},
        {"forecast_reference_time": "2020-12-21T12:00:00"},
        {"forecast_reference_time": datetime.datetime(2020, 12, 21, 12, 0, 0)},
    ],
)
def test_grib_sel_base_datetime(fl_type, _kwargs):
    f, _ = load_grib_data("t_time_series.grib", fl_type, folder="data")

    g = f.sel(**_kwargs)
    assert len(g) == 10

    ref_keys = ["shortName", "date", "time", "endStep"]
    ref = [
        ["t", 20201221, 1200, 0],
        ["z", 20201221, 1200, 0],
        ["t", 20201221, 1200, 3],
        ["z", 20201221, 1200, 3],
        ["t", 20201221, 1200, 6],
        ["z", 20201221, 1200, 6],
        ["t", 20201221, 1200, 9],
        ["z", 20201221, 1200, 9],
        ["t", 20201221, 1200, 48],
        ["z", 20201221, 1200, 48],
    ]

    assert g.get(ref_keys) == ref


@pytest.mark.cache
@pytest.mark.parametrize(
    "_kwargs,ref_len,ref",
    [
        (
            {"step": 24, "time_span_value": datetime.timedelta(hours=6)},
            1,
            {"step": datetime.timedelta(hours=24), "time_span": TimeSpan(6, TimeSpanMethod.MAX)},
        ),
        (
            {"step": 24, "time_span_method": TimeSpanMethod.MAX},
            1,
            {"step": datetime.timedelta(hours=24), "time_span": TimeSpan(6, TimeSpanMethod.MAX)},
        ),
        (
            {"time_span_method": TimeSpanMethod.AVERAGE},
            0,
            {},
        ),
        (
            {"step": 24, "time_span": TimeSpan(6, TimeSpanMethod.MAX)},
            1,
            {"step": datetime.timedelta(hours=24), "time_span": TimeSpan(6, TimeSpanMethod.MAX)},
        ),
    ],
)
def test_grib_sel_time_span(_kwargs, ref_len, ref):
    ds1 = from_source("url", earthkit_remote_test_data_file("xr_engine/date/wgust_step_range.grib1"))

    g = ds1.sel(**_kwargs)
    assert len(g) == ref_len
    for k, v in ref.items():
        assert g[0].get(k) == v


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_sel_remapping_1(fl_type):
    ds, _ = load_grib_data("test6.grib", fl_type)
    ref = [("t", 850)]
    r = ds.sel(param_level="t850", remapping={"param_level": "{param}{levelist}"})
    assert r.get("param", "level") == ref


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_sel_remapping_2(fl_type):
    ds, _ = load_grib_data("test6.grib", fl_type)
    ref = [("u", 1000), ("t", 850)]
    r = ds.sel(param_level=["t850", "u1000"], remapping={"param_level": "{param}{levelist}"})
    assert r.get("param", "level") == ref


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
