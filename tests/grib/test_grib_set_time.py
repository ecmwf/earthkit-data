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

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_grib_data  # noqa: E402


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.parametrize("write_method", ["target"])
@pytest.mark.parametrize(
    "_kwargs,ref_set,ref_saved,edition_saved",
    [
        # (
        #     {"base_datetime": "2025-08-24T12:00:00", "step": 6},
        #     {
        #         "base_datetime": datetime.datetime(2025, 8, 24, 12),
        #         "valid_datetime": datetime.datetime(2025, 8, 24, 18),
        #         "step": datetime.timedelta(hours=6),
        #         "time_span": datetime.timedelta(hours=0),
        #     },
        #     {
        #         "grib.dataDate": 20250824,
        #         "grib.dataTime": 1200,
        #         "grib.validityDate": 20250824,
        #         "grib.validityTime": 1800,
        #         "grib.step": 6,
        #         "grib.stepRange": "6",
        #         "grib.startStep": 6,
        #         "grib.endStep": 6,
        #     },
        # ),
        # (
        #     {"base_datetime": datetime.datetime(2025, 8, 24, 12), "step": datetime.timedelta(hours=6)},
        #     {
        #         "base_datetime": datetime.datetime(2025, 8, 24, 12),
        #         "valid_datetime": datetime.datetime(2025, 8, 24, 18),
        #         "step": datetime.timedelta(hours=6),
        #         "time_span": datetime.timedelta(hours=0),
        #     },
        #     {
        #         "grib.dataDate": 20250824,
        #         "grib.dataTime": 1200,
        #         "grib.validityDate": 20250824,
        #         "grib.validityTime": 1800,
        #         "grib.step": 6,
        #         "grib.stepRange": "6",
        #         "grib.startStep": 6,
        #         "grib.endStep": 6,
        #     },
        # ),
        # (
        #     {"valid_datetime": "2025-08-24T18:00:00", "step": datetime.timedelta(hours=6)},
        #     {
        #         "base_datetime": datetime.datetime(2025, 8, 24, 12),
        #         "valid_datetime": datetime.datetime(2025, 8, 24, 18),
        #         "step": datetime.timedelta(hours=6),
        #         "time_span": datetime.timedelta(hours=0),
        #     },
        #     {
        #         "grib.dataDate": 20250824,
        #         "grib.dataTime": 1200,
        #         "grib.validityDate": 20250824,
        #         "grib.validityTime": 1800,
        #         "grib.step": 6,
        #         "grib.stepRange": "6",
        #         "grib.startStep": 6,
        #         "grib.endStep": 6,
        #     },
        # ),
        # (
        #     {"valid_datetime": datetime.datetime(2025, 8, 24, 18), "step": datetime.timedelta(hours=6)},
        #     {
        #         "base_datetime": datetime.datetime(2025, 8, 24, 12),
        #         "valid_datetime": datetime.datetime(2025, 8, 24, 18),
        #         "step": datetime.timedelta(hours=6),
        #         "time_span": datetime.timedelta(hours=0),
        #     },
        #     {
        #         "grib.dataDate": 20250824,
        #         "grib.dataTime": 1200,
        #         "grib.validityDate": 20250824,
        #         "grib.validityTime": 1800,
        #         "grib.step": 6,
        #         "grib.stepRange": "6",
        #         "grib.startStep": 6,
        #         "grib.endStep": 6,
        #     },
        # ),
        # (
        #     {"base_datetime": "2025-08-24T12:00:00"},
        #     {
        #         "base_datetime": datetime.datetime(2025, 8, 24, 12),
        #         "valid_datetime": datetime.datetime(2025, 8, 24, 12),
        #         "step": datetime.timedelta(hours=0),
        #         "time_span": datetime.timedelta(hours=0),
        #     },
        #     {
        #         "grib.dataDate": 20250824,
        #         "grib.dataTime": 1200,
        #         "grib.validityDate": 20250824,
        #         "grib.validityTime": 1200,
        #         "grib.step": 0,
        #         "grib.stepRange": "0",
        #         "grib.startStep": 0,
        #         "grib.endStep": 0,
        #     },
        # ),
        # (
        #     {"base_datetime": datetime.datetime(2025, 8, 24, 12)},
        #     {
        #         "base_datetime": datetime.datetime(2025, 8, 24, 12),
        #         "valid_datetime": datetime.datetime(2025, 8, 24, 12),
        #         "step": datetime.timedelta(hours=0),
        #         "time_span": datetime.timedelta(hours=0),
        #     },
        #     {
        #         "grib.dataDate": 20250824,
        #         "grib.dataTime": 1200,
        #         "grib.validityDate": 20250824,
        #         "grib.validityTime": 1200,
        #         "grib.step": 0,
        #         "grib.stepRange": "0",
        #         "grib.startStep": 0,
        #         "grib.endStep": 0,
        #     },
        # ),
        # (
        #     {"valid_datetime": "2025-08-24T12:00:00", "step": 0},
        #     {
        #         "base_datetime": datetime.datetime(2025, 8, 24, 12),
        #         "valid_datetime": datetime.datetime(2025, 8, 24, 12),
        #         "step": datetime.timedelta(hours=0),
        #         "time_span": datetime.timedelta(hours=0),
        #     },
        #     {
        #         "grib.dataDate": 20250824,
        #         "grib.dataTime": 1200,
        #         "grib.validityDate": 20250824,
        #         "grib.validityTime": 1200,
        #         "grib.step": 0,
        #         "grib.stepRange": "0",
        #         "grib.startStep": 0,
        #         "grib.endStep": 0,
        #     },
        # ),
        # (
        #     {"valid_datetime": datetime.datetime(2025, 8, 24, 12), "step": datetime.timedelta(hours=0)},
        #     {
        #         "base_datetime": datetime.datetime(2025, 8, 24, 12),
        #         "valid_datetime": datetime.datetime(2025, 8, 24, 12),
        #         "step": datetime.timedelta(hours=0),
        #         "time_span": datetime.timedelta(hours=0),
        #     },
        #     {
        #         "grib.dataDate": 20250824,
        #         "grib.dataTime": 1200,
        #         "grib.validityDate": 20250824,
        #         "grib.validityTime": 1200,
        #         "grib.step": 0,
        #         "grib.stepRange": "0",
        #         "grib.startStep": 0,
        #         "grib.endStep": 0,
        #     },
        # ),
        # (
        #     {"valid_datetime": "2007-01-03T18:00:00"},
        #     {
        #         "base_datetime": datetime.datetime(2007, 1, 1, 12),
        #         "valid_datetime": datetime.datetime(2007, 1, 3, 18),
        #         "step": datetime.timedelta(hours=54),
        #         "time_span": datetime.timedelta(hours=0),
        #     },
        #     {
        #         "grib.dataDate": 20070101,
        #         "grib.dataTime": 1200,
        #         "grib.validityDate": 20070103,
        #         "grib.validityTime": 1800,
        #         "grib.step": 54,
        #         "grib.stepRange": "54",
        #         "grib.startStep": 54,
        #         "grib.endStep": 54,
        #     },
        # ),
        # (
        #     {"valid_datetime": datetime.datetime(2007, 1, 3, 18)},
        #     {
        #         "base_datetime": datetime.datetime(2007, 1, 1, 12),
        #         "valid_datetime": datetime.datetime(2007, 1, 3, 18),
        #         "step": datetime.timedelta(hours=54),
        #         "time_span": datetime.timedelta(hours=0),
        #     },
        #     {
        #         "grib.dataDate": 20070101,
        #         "grib.dataTime": 1200,
        #         "grib.validityDate": 20070103,
        #         "grib.validityTime": 1800,
        #         "grib.step": 54,
        #         "grib.stepRange": "54",
        #         "grib.startStep": 54,
        #         "grib.endStep": 54,
        #     },
        # ),
        # (
        #     {"valid_datetime": datetime.datetime(2007, 1, 3, 18), "time_span": 1},
        #     {
        #         "base_datetime": datetime.datetime(2007, 1, 1, 12),
        #         "valid_datetime": datetime.datetime(2007, 1, 3, 18),
        #         "step": datetime.timedelta(hours=54),
        #         "time_span": datetime.timedelta(hours=1),
        #     },
        #     None,
        # ),
        # (
        #     {"step": datetime.timedelta(hours=6)},
        #     {
        #         "base_datetime": datetime.datetime(2007, 1, 1, 12),
        #         "valid_datetime": datetime.datetime(2007, 1, 1, 18),
        #         "step": datetime.timedelta(hours=6),
        #         "time_span": datetime.timedelta(hours=0),
        #     },
        #     {
        #         "grib.dataDate": 20070101,
        #         "grib.dataTime": 1200,
        #         "grib.validityDate": 20070101,
        #         "grib.validityTime": 1800,
        #         "grib.step": 6,
        #         "grib.stepRange": "6",
        #         "grib.startStep": 6,
        #         "grib.endStep": 6,
        #     },
        # ),
        # (
        #     {"step": datetime.timedelta(hours=6, minutes=30)},
        #     {
        #         "base_datetime": datetime.datetime(2007, 1, 1, 12),
        #         "valid_datetime": datetime.datetime(2007, 1, 1, 18, 30),
        #         "step": datetime.timedelta(hours=6, minutes=30),
        #         "time_span": datetime.timedelta(hours=0),
        #     },
        #     {
        #         "grib.dataDate": 20070101,
        #         "grib.dataTime": 1200,
        #         "grib.validityDate": 20070101,
        #         "grib.validityTime": 1830,
        #         "grib.step": "390m",
        #         "grib.stepRange": "390m",
        #         "grib.startStep": "390m",
        #         "grib.endStep": "390m",
        #     },
        #     2,
        # ),
        (
            {"step": datetime.timedelta(hours=36), "time_span": (datetime.timedelta(days=1), "avg")},
            {
                "base_datetime": datetime.datetime(2007, 1, 1, 12),
                "valid_datetime": datetime.datetime(2007, 1, 3, 0),
                "step": datetime.timedelta(hours=36),
                "time_span": (datetime.timedelta(days=1), "avg"),
            },
            {
                "grib.dataDate": 20070101,
                "grib.dataTime": 1200,
                "grib.validityDate": 20070103,
                "grib.validityTime": 0,
                "grib.step": 36,
                "grib.stepRange": "12-36",
                "grib.startStep": 12,
                "grib.endStep": 36,
            },
            None,
        ),
        # (
        #     {"time_span": datetime.timedelta(hours=6, minutes=30)},
        #     {
        #         "base_datetime": datetime.datetime(2007, 1, 1, 12),
        #         "valid_datetime": datetime.datetime(2007, 1, 1, 12),
        #         "step": datetime.timedelta(hours=0),
        #         "time_span": datetime.timedelta(hours=6, minutes=30),
        #     },
        #     None,
        # ),
    ],
)
def test_grib_set_time_1(fl_type, write_method, _kwargs, ref_set, ref_saved, edition_saved):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set(**_kwargs)

    print("Metadata of f:", f._time.to_dict())

    for k, v in ref_set.items():
        assert f.get(k) == v, f"key {k} expected {v} got {f.get(k)}"

    # original message is unchanged
    assert ds_ori[0].get("base_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("valid_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("step") == datetime.timedelta(hours=0)
    assert ds_ori[0].get("time_span") == datetime.timedelta(hours=0)

    if ref_saved is None:
        return

    with temp_file() as tmp:
        _encoder_kwargs = {}
        if edition_saved is not None:
            _encoder_kwargs = {"edition": edition_saved}

        f.to_target("file", tmp, **_encoder_kwargs)
        f_saved = from_source("file", tmp)
        assert len(f_saved) == 1

        print("Metadata after setting to handle:", f_saved[0]._time.to_dict())

        for k, v in ref_set.items():
            assert f_saved[0].get(k) == v, f"key {k} expected {v} got {f_saved[0].get(k)}"

        for k, v in ref_saved.items():
            assert f_saved[0].get(k) == v, f"key {k} expected {v} got {f_saved[0].get(k)}"
