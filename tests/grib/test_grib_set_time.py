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

import pytest

# from earthkit.data.specs.time_span import TimeSpan
# from earthkit.data.specs.time_span import TimeSpanMethod

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_grib_data  # noqa: E402


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
@pytest.mark.parametrize("write_method", ["target"])
@pytest.mark.parametrize(
    "_kwargs,ref_set,ref_saved,edition_saved",
    [
        (
            {"time.base_datetime": "2025-08-24T12:00:00", "time.step": 6},
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 18),
                "time.step": datetime.timedelta(hours=6),
                # "time_span": TimeSpan(),
            },
            {
                "metadata.dataDate": 20250824,
                "metadata.dataTime": 1200,
                "metadata.validityDate": 20250824,
                "metadata.validityTime": 1800,
                "metadata.step": 6,
                "metadata.stepRange": "6",
                "metadata.startStep": 6,
                "metadata.endStep": 6,
                "metadata.stepType": "instant",
            },
            None,
        ),
        (
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.step": datetime.timedelta(hours=6),
            },
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 18),
                "time.step": datetime.timedelta(hours=6),
                # "time_span": TimeSpan(),
            },
            {
                "metadata.dataDate": 20250824,
                "metadata.dataTime": 1200,
                "metadata.validityDate": 20250824,
                "metadata.validityTime": 1800,
                "metadata.step": 6,
                "metadata.stepRange": "6",
                "metadata.startStep": 6,
                "metadata.endStep": 6,
                "metadata.stepType": "instant",
            },
            None,
        ),
        (
            {"time.valid_datetime": "2025-08-24T18:00:00", "time.step": datetime.timedelta(hours=6)},
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 18),
                "time.step": datetime.timedelta(hours=6),
                # "time_span": TimeSpan(),
            },
            {
                "metadata.dataDate": 20250824,
                "metadata.dataTime": 1200,
                "metadata.validityDate": 20250824,
                "metadata.validityTime": 1800,
                "metadata.step": 6,
                "metadata.stepRange": "6",
                "metadata.startStep": 6,
                "metadata.endStep": 6,
                "metadata.stepType": "instant",
            },
            None,
        ),
        (
            {
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 18),
                "time.step": datetime.timedelta(hours=6),
            },
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 18),
                "time.step": datetime.timedelta(hours=6),
                # "time_span": TimeSpan(),
            },
            {
                "metadata.dataDate": 20250824,
                "metadata.dataTime": 1200,
                "metadata.validityDate": 20250824,
                "metadata.validityTime": 1800,
                "metadata.step": 6,
                "metadata.stepRange": "6",
                "metadata.startStep": 6,
                "metadata.endStep": 6,
                "metadata.stepType": "instant",
            },
            None,
        ),
        (
            {"time.base_datetime": "2025-08-24T12:00:00"},
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.step": datetime.timedelta(hours=0),
                # "time_span": TimeSpan(),
            },
            {
                "metadata.dataDate": 20250824,
                "metadata.dataTime": 1200,
                "metadata.validityDate": 20250824,
                "metadata.validityTime": 1200,
                "metadata.step": 0,
                "metadata.stepRange": "0",
                "metadata.startStep": 0,
                "metadata.endStep": 0,
                "metadata.stepType": "instant",
            },
            None,
        ),
        (
            {"time.base_datetime": datetime.datetime(2025, 8, 24, 12)},
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.step": datetime.timedelta(hours=0),
                # "time_span": TimeSpan(),
            },
            {
                "metadata.dataDate": 20250824,
                "metadata.dataTime": 1200,
                "metadata.validityDate": 20250824,
                "metadata.validityTime": 1200,
                "metadata.step": 0,
                "metadata.stepRange": "0",
                "metadata.startStep": 0,
                "metadata.endStep": 0,
                "metadata.stepType": "instant",
            },
            None,
        ),
        (
            {"time.valid_datetime": "2025-08-24T12:00:00", "time.step": 0},
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.step": datetime.timedelta(hours=0),
                # "time_span": TimeSpan(),
            },
            {
                "metadata.dataDate": 20250824,
                "metadata.dataTime": 1200,
                "metadata.validityDate": 20250824,
                "metadata.validityTime": 1200,
                "metadata.step": 0,
                "metadata.stepRange": "0",
                "metadata.startStep": 0,
                "metadata.endStep": 0,
                "metadata.stepType": "instant",
            },
            None,
        ),
        (
            {
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.step": datetime.timedelta(hours=0),
            },
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.step": datetime.timedelta(hours=0),
                # "time_span": TimeSpan(),
            },
            {
                "metadata.dataDate": 20250824,
                "metadata.dataTime": 1200,
                "metadata.validityDate": 20250824,
                "metadata.validityTime": 1200,
                "metadata.step": 0,
                "metadata.stepRange": "0",
                "metadata.startStep": 0,
                "metadata.endStep": 0,
                "metadata.stepType": "instant",
            },
            None,
        ),
        (
            {"time.valid_datetime": "2007-01-03T18:00:00"},
            {
                "time.base_datetime": datetime.datetime(2007, 1, 1, 12),
                "time.valid_datetime": datetime.datetime(2007, 1, 3, 18),
                "time.step": datetime.timedelta(hours=54),
                # "time_span": TimeSpan(),
            },
            {
                "metadata.dataDate": 20070101,
                "metadata.dataTime": 1200,
                "metadata.validityDate": 20070103,
                "metadata.validityTime": 1800,
                "metadata.step": 54,
                "metadata.stepRange": "54",
                "metadata.startStep": 54,
                "metadata.endStep": 54,
                "metadata.stepType": "instant",
            },
            None,
        ),
        (
            {"time.valid_datetime": datetime.datetime(2007, 1, 3, 18)},
            {
                "time.base_datetime": datetime.datetime(2007, 1, 1, 12),
                "time.valid_datetime": datetime.datetime(2007, 1, 3, 18),
                "time.step": datetime.timedelta(hours=54),
                # "time_span": TimeSpan(),
            },
            {
                "metadata.dataDate": 20070101,
                "metadata.dataTime": 1200,
                "metadata.validityDate": 20070103,
                "metadata.validityTime": 1800,
                "metadata.step": 54,
                "metadata.stepRange": "54",
                "metadata.startStep": 54,
                "metadata.endStep": 54,
                "metadata.stepType": "instant",
            },
            None,
        ),
        (
            {
                "time.valid_datetime": datetime.datetime(2007, 1, 3, 18),
                # "time_span": TimeSpan(1, TimeSpanMethod.AVERAGE),
            },
            {
                "time.base_datetime": datetime.datetime(2007, 1, 1, 12),
                "time.valid_datetime": datetime.datetime(2007, 1, 3, 18),
                "time.step": datetime.timedelta(hours=54),
                # "time_span": TimeSpan(datetime.timedelta(hours=1), TimeSpanMethod.AVERAGE),
            },
            None,
            None,
        ),
        (
            {"time.step": datetime.timedelta(hours=6)},
            {
                "time.base_datetime": datetime.datetime(2007, 1, 1, 12),
                "time.valid_datetime": datetime.datetime(2007, 1, 1, 18),
                "time.step": datetime.timedelta(hours=6),
                # "time_span": TimeSpan(),
            },
            {
                "metadata.dataDate": 20070101,
                "metadata.dataTime": 1200,
                "metadata.validityDate": 20070101,
                "metadata.validityTime": 1800,
                "metadata.step": 6,
                "metadata.stepRange": "6",
                "metadata.startStep": 6,
                "metadata.endStep": 6,
                "metadata.stepType": "instant",
            },
            None,
        ),
        (
            {"time.step": datetime.timedelta(hours=6, minutes=30)},
            {
                "time.base_datetime": datetime.datetime(2007, 1, 1, 12),
                "time.valid_datetime": datetime.datetime(2007, 1, 1, 18, 30),
                "time.step": datetime.timedelta(hours=6, minutes=30),
                # "time_span": TimeSpan(),
            },
            {
                "metadata.dataDate": 20070101,
                "metadata.dataTime": 1200,
                "metadata.validityDate": 20070101,
                "metadata.validityTime": 1830,
                "metadata.step": "390m",
                "metadata.stepRange": "390m",
                "metadata.startStep": "390m",
                "metadata.endStep": "390m",
                "metadata.stepType": "instant",
            },
            2,
        ),
        (
            {
                "time.step": datetime.timedelta(hours=36),
                # "time_span": TimeSpan(datetime.timedelta(days=1), TimeSpanMethod.AVERAGE),
            },
            {
                "time.base_datetime": datetime.datetime(2007, 1, 1, 12),
                "time.valid_datetime": datetime.datetime(2007, 1, 3, 0),
                "time.step": datetime.timedelta(hours=36),
                # "time_span": TimeSpan(datetime.timedelta(days=1), TimeSpanMethod.AVERAGE),
            },
            {
                "metadata.dataDate": 20070101,
                "metadata.dataTime": 1200,
                "metadata.validityDate": 20070103,
                "metadata.validityTime": 0,
                "metadata.step": 36,
                "metadata.stepRange": "36",
                "metadata.startStep": 36,
                "metadata.endStep": 36,
                "metadata.stepType": "instant",
            },
            None,
        ),
        # (
        #     {"time_span": TimeSpan(datetime.timedelta(hours=6, minutes=30), TimeSpanMethod.AVERAGE)},
        #     {
        #         "base_datetime": datetime.datetime(2007, 1, 1, 12),
        #         "valid_datetime": datetime.datetime(2007, 1, 1, 12),
        #         "step": datetime.timedelta(hours=0),
        #         "time_span": TimeSpan(datetime.timedelta(hours=6, minutes=30), TimeSpanMethod.AVERAGE),
        #     },
        #     None,
        #     None,
        # ),
    ],
)
def test_grib_set_time_1(fl_type, write_method, _kwargs, ref_set, ref_saved, edition_saved):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set(**_kwargs)

    for k, v in ref_set.items():
        assert f.get(k) == v, f"key {k} expected {v} got {f.get(k)}"

    # original message is unchanged
    assert ds_ori[0].get("time.base_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("time.valid_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("time.step") == datetime.timedelta(hours=0)
    # assert ds_ori[0].get("time_span") == datetime.timedelta(hours=0)

    if ref_saved is None:
        return

    # TODO:
    # with temp_file() as tmp:
    #     _encoder_kwargs = {}
    #     if edition_saved is not None:
    #         _encoder_kwargs = {"edition": edition_saved}

    #     f.to_target("file", tmp, **_encoder_kwargs)
    #     f_saved = from_source("file", tmp)
    #     assert len(f_saved) == 1

    #     # print("Metadata after setting to handle:", f_saved[0]._time.to_dict())

    #     for k, v in ref_set.items():
    #         assert f_saved[0].get(k) == v, f"key {k} expected {v} got {f_saved[0].get(k)}"

    #     for k, v in ref_saved.items():
    #         assert f_saved[0].get(k) == v, f"key {k} expected {v} got {f_saved[0].get(k)}"
