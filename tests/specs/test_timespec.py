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

import pytest

from earthkit.data.specs.time import SimpleTime
from earthkit.data.specs.time_span import TimeSpan
from earthkit.data.specs.time_span import TimeSpanMethod


@pytest.mark.parametrize(
    "input_d,ref",
    [
        (
            {"valid_datetime": "2016-09-25"},
            (
                datetime.datetime(2016, 9, 25),
                datetime.timedelta(0),
                datetime.datetime(2016, 9, 25),
                TimeSpan(),
            ),
        ),
        (
            {"valid_datetime": "2016-09-25T12", "step": 0},
            (
                datetime.datetime(2016, 9, 25, 12),
                datetime.timedelta(0),
                datetime.datetime(2016, 9, 25, 12),
                TimeSpan(),
            ),
        ),
        (
            {"valid_datetime": "2016-09-25T12", "step": 6},
            (
                datetime.datetime(2016, 9, 25, 6),
                datetime.timedelta(hours=6),
                datetime.datetime(2016, 9, 25, 12),
                TimeSpan(),
            ),
        ),
        (
            {"base_datetime": "2016-09-25T12", "step": 6},
            (
                datetime.datetime(2016, 9, 25, 12),
                datetime.timedelta(hours=6),
                datetime.datetime(2016, 9, 25, 18),
                TimeSpan(),
            ),
        ),
        (
            {"base_datetime": "2016-09-25T12", "step": "30m"},
            (
                datetime.datetime(2016, 9, 25, 12),
                datetime.timedelta(hours=0, minutes=30),
                datetime.datetime(2016, 9, 25, 12, 30),
                TimeSpan(),
            ),
        ),
        (
            {"base_datetime": "2016-09-25T12", "step": "90m"},
            (
                datetime.datetime(2016, 9, 25, 12),
                datetime.timedelta(hours=1, minutes=30),
                datetime.datetime(2016, 9, 25, 13, 30),
                TimeSpan(),
            ),
        ),
        (
            {"base_datetime": "2020-09-25T12", "step": 30, "time_span": TimeSpan(6, TimeSpanMethod.AVERAGE)},
            (
                datetime.datetime(2020, 9, 25, 12),
                datetime.timedelta(hours=30),
                datetime.datetime(2020, 9, 26, 18),
                TimeSpan(6, TimeSpanMethod.AVERAGE),
            ),
        ),
        (
            {"base_datetime": "2020-09-25T12", "valid_datetime": "2020-09-26T18"},
            (
                datetime.datetime(2020, 9, 25, 12),
                datetime.timedelta(hours=30),
                datetime.datetime(2020, 9, 26, 18),
                TimeSpan(),
            ),
        ),
    ],
)
def test_timespec_from_dict(input_d, ref):
    t = SimpleTime.from_dict(input_d)

    assert t.base_datetime == ref[0]
    assert t.forecast_reference_time == ref[0]
    assert t.step == ref[1]
    assert t.forecast_period == ref[1]
    assert t.valid_datetime == ref[2]
    assert t.time_span == ref[3]
    assert t.time_span_value == ref[3].value
    assert t.time_span_method == ref[3].method


# @pytest.mark.parametrize("fl_type", FL_TYPES)
# def test_grib_time_forecast(fl_type):
#     ds, _ = load_grib_data("t_time_series.grib", fl_type, folder="data")
#     f = ds[4]

#     assert f.valid_datetime == datetime.datetime(2020, 12, 21, 18, 0)
#     assert f.base_datetime == datetime.datetime(2020, 12, 21, 12, 0)
#     assert f.forecast_reference_time == datetime.datetime(2020, 12, 21, 12, 0)
#     assert f.step == datetime.timedelta(hours=6)
#     assert f.forecast_period == datetime.timedelta(hours=6)
#     assert f.time_span == datetime.timedelta(0)


# @pytest.mark.cache
# def test_grib_time_step_range_1():
#     ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/wgust_step_range.grib1"))

#     f = ds[2]
#     assert f.valid_datetime == datetime.datetime(2011, 12, 16, 12, 0)
#     assert f.base_datetime == datetime.datetime(2011, 12, 15, 12, 0)
#     assert f.forecast_reference_time == datetime.datetime(2011, 12, 15, 12, 0)
#     assert f.step == datetime.timedelta(hours=24)
#     assert f.forecast_period == datetime.timedelta(hours=24)
#     assert f.time_span == datetime.timedelta(hours=6)


# @pytest.mark.cache
# def test_grib_time_step_range_2():
#     ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/lsp_step_range.grib2"))

#     f = ds[0]
#     assert f.valid_datetime == datetime.datetime(2025, 5, 30)
#     assert f.base_datetime == datetime.datetime(2025, 5, 27)
#     assert f.step == datetime.timedelta(hours=72)
#     assert f.time_span == datetime.timedelta(hours=1)

#     f = ds[1]
#     assert f.valid_datetime == datetime.datetime(2025, 5, 30, 1)
#     assert f.base_datetime == datetime.datetime(2025, 5, 27)
#     assert f.step == datetime.timedelta(hours=73)
#     assert f.time_span == datetime.timedelta(hours=1)


# @pytest.mark.cache
# def test_grib_time_seasonal():
#     ds = from_source(
#         "url",
#         earthkit_remote_test_data_file("xr_engine/date/jma_seasonal_fc_ref_time_per_member.grib"),
#     )

#     f = ds[0]
#     assert f.base_datetime == datetime.datetime(2014, 8, 29)
#     assert f.step == datetime.timedelta(days=33)
#     assert f.valid_datetime == datetime.datetime(2014, 10, 1)
#     assert f.time_span == datetime.timedelta(0)
#     assert f.indexing_datetime == datetime.datetime(2014, 9, 1)


# @pytest.mark.cache
# def test_grib_time_monthly():
#     ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/seasonal_monthly.grib"))

#     f = ds[0]
#     assert f.base_datetime == datetime.datetime(1993, 10, 1)
#     assert f.step == datetime.timedelta(days=31)
#     assert f.valid_datetime == datetime.datetime(1993, 11, 1)
#     assert f.time_span == datetime.timedelta(0)
#     assert f.indexing_datetime is None


# @pytest.mark.cache
# def test_grib_time_step_in_minutes():
#     ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/step_60m.grib"))

#     f = ds[0]
#     assert f.base_datetime == datetime.datetime(2024, 1, 15)
#     assert f.step == datetime.timedelta(0)
#     assert f.valid_datetime == datetime.datetime(2024, 1, 15)
#     assert f.time_span == datetime.timedelta(0)
