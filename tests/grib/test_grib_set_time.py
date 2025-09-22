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

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_grib_data  # noqa: E402


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
# @pytest.mark.parametrize("fl_type", ["file"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.parametrize("write_method", ["target"])
@pytest.mark.parametrize(
    "_kwargs,ref",
    [
        (
            {"base_datetime": "2025-08-24T12:00:00", "step": 6},
            {
                "base_datetime": datetime.datetime(2025, 8, 24, 12),
                "valid_datetime": datetime.datetime(2025, 8, 24, 18),
                "step": datetime.timedelta(hours=6),
                "time_span": datetime.timedelta(hours=0),
            },
        ),
        (
            {"base_datetime": datetime.datetime(2025, 8, 24, 12), "step": datetime.timedelta(hours=6)},
            {
                "base_datetime": datetime.datetime(2025, 8, 24, 12),
                "valid_datetime": datetime.datetime(2025, 8, 24, 18),
                "step": datetime.timedelta(hours=6),
                "time_span": datetime.timedelta(hours=0),
            },
        ),
        (
            {"valid_datetime": "2025-08-24T18:00:00", "step": datetime.timedelta(hours=6)},
            {
                "base_datetime": datetime.datetime(2025, 8, 24, 12),
                "valid_datetime": datetime.datetime(2025, 8, 24, 18),
                "step": datetime.timedelta(hours=6),
                "time_span": datetime.timedelta(hours=0),
            },
        ),
        (
            {"valid_datetime": datetime.datetime(2025, 8, 24, 18), "step": datetime.timedelta(hours=6)},
            {
                "base_datetime": datetime.datetime(2025, 8, 24, 12),
                "valid_datetime": datetime.datetime(2025, 8, 24, 18),
                "step": datetime.timedelta(hours=6),
                "time_span": datetime.timedelta(hours=0),
            },
        ),
        (
            {"base_datetime": "2025-08-24T12:00:00"},
            {
                "base_datetime": datetime.datetime(2025, 8, 24, 12),
                "valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "step": datetime.timedelta(hours=0),
                "time_span": datetime.timedelta(hours=0),
            },
        ),
        (
            {"base_datetime": datetime.datetime(2025, 8, 24, 12)},
            {
                "base_datetime": datetime.datetime(2025, 8, 24, 12),
                "valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "step": datetime.timedelta(hours=0),
                "time_span": datetime.timedelta(hours=0),
            },
        ),
        (
            {"valid_datetime": "2025-08-24T12:00:00", "step": 0},
            {
                "base_datetime": datetime.datetime(2025, 8, 24, 12),
                "valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "step": datetime.timedelta(hours=0),
                "time_span": datetime.timedelta(hours=0),
            },
        ),
        (
            {"valid_datetime": datetime.datetime(2025, 8, 24, 12), "step": datetime.timedelta(hours=0)},
            {
                "base_datetime": datetime.datetime(2025, 8, 24, 12),
                "valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "step": datetime.timedelta(hours=0),
                "time_span": datetime.timedelta(hours=0),
            },
        ),
        (
            {"valid_datetime": "2007-01-03T18:00:00"},
            {
                "base_datetime": datetime.datetime(2007, 1, 1, 12),
                "valid_datetime": datetime.datetime(2007, 1, 3, 18),
                "step": datetime.timedelta(hours=54),
                "time_span": datetime.timedelta(hours=0),
            },
        ),
        (
            {"valid_datetime": datetime.datetime(2007, 1, 3, 18)},
            {
                "base_datetime": datetime.datetime(2007, 1, 1, 12),
                "valid_datetime": datetime.datetime(2007, 1, 3, 18),
                "step": datetime.timedelta(hours=54),
                "time_span": datetime.timedelta(hours=0),
            },
        ),
        (
            {"valid_datetime": datetime.datetime(2007, 1, 3, 18), "time_span": 1},
            {
                "base_datetime": datetime.datetime(2007, 1, 1, 12),
                "valid_datetime": datetime.datetime(2007, 1, 3, 18),
                "step": datetime.timedelta(hours=54),
                "time_span": datetime.timedelta(hours=1),
            },
        ),
        (
            {"step": datetime.timedelta(hours=6)},
            {
                "base_datetime": datetime.datetime(2007, 1, 1, 12),
                "valid_datetime": datetime.datetime(2007, 1, 1, 18),
                "step": datetime.timedelta(hours=6),
                "time_span": datetime.timedelta(hours=0),
            },
        ),
        (
            {"step": datetime.timedelta(hours=6, minutes=30)},
            {
                "base_datetime": datetime.datetime(2007, 1, 1, 12),
                "valid_datetime": datetime.datetime(2007, 1, 1, 18, 30),
                "step": datetime.timedelta(hours=6, minutes=30),
                "time_span": datetime.timedelta(hours=0),
            },
        ),
        (
            {"step": datetime.timedelta(hours=6), "time_span": datetime.timedelta(days=1)},
            {
                "base_datetime": datetime.datetime(2007, 1, 1, 12),
                "valid_datetime": datetime.datetime(2007, 1, 1, 18),
                "step": datetime.timedelta(hours=6),
                "time_span": datetime.timedelta(days=1),
            },
        ),
        (
            {"time_span": datetime.timedelta(hours=6, minutes=30)},
            {
                "base_datetime": datetime.datetime(2007, 1, 1, 12),
                "valid_datetime": datetime.datetime(2007, 1, 1, 12),
                "step": datetime.timedelta(hours=0),
                "time_span": datetime.timedelta(hours=6, minutes=30),
            },
        ),
    ],
)
def test_grib_set_time_1(fl_type, write_method, _kwargs, ref):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set(**_kwargs)
    assert f.get("base_datetime") == ref["base_datetime"]
    assert f.get("valid_datetime") == ref["valid_datetime"]
    assert f.get("step") == ref["step"]
    assert f.get("time_span") == ref["time_span"]

    assert ds_ori[0].get("base_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("valid_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("step") == datetime.timedelta(hours=0)
    assert ds_ori[0].get("time_span") == datetime.timedelta(hours=0)
