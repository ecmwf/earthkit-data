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
from earthkit.data.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)


@pytest.mark.cache
def test_grib_proc_analysis():
    ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/msl_analysis.grib"))

    f = ds[0]
    assert f.base_datetime == datetime.datetime(2016, 9, 25)
    assert f.step == datetime.timedelta(0)
    assert f.valid_datetime == datetime.datetime(2016, 9, 25)

    assert isinstance(f.proc.items, list)
    t = f.proc.time
    assert t.value == datetime.timedelta(0)
    # assert t.method == TimeMethods.ACCUMULATED
    # assert t.method == "instant"


# @pytest.mark.cache
# def test_grib_proc_step_range_1():
#     ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/wgust_step_range.grib1"))

#     f = ds[2]
#     assert f.valid_datetime == datetime.datetime(2011, 12, 16, 12, 0)
#     assert f.base_datetime == datetime.datetime(2011, 12, 15, 12, 0)
#     assert f.forecast_reference_time == datetime.datetime(2011, 12, 15, 12, 0)
#     assert f.step == datetime.timedelta(hours=24)
#     assert f.forecast_period == datetime.timedelta(hours=24)
#     # assert f.time_span == TimeSpan(6, TimeSpanMethod.MAX)
#     # assert f.time_span_value == datetime.timedelta(hours=6)
#     # assert f.time_span_method == TimeSpanMethod.MAX


# @pytest.mark.cache
# def test_grib_proc_step_range_2():
#     ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/lsp_step_range.grib2"))

#     f = ds[0]
#     assert f.valid_datetime == datetime.datetime(2025, 5, 30)
#     assert f.base_datetime == datetime.datetime(2025, 5, 27)
#     assert f.step == datetime.timedelta(hours=72)
#     # assert f.time_span == TimeSpan(1, TimeSpanMethod.ACCUMULATED)
#     # assert f.time_span_value == datetime.timedelta(hours=1)
#     # assert f.time_span_method == TimeSpanMethod.ACCUMULATED

#     f = ds[1]
#     assert f.valid_datetime == datetime.datetime(2025, 5, 30, 1)
#     assert f.base_datetime == datetime.datetime(2025, 5, 27)
#     assert f.step == datetime.timedelta(hours=73)
#     # assert f.time_span == TimeSpan(1, TimeSpanMethod.ACCUMULATED)
#     # assert f.time_span_value == datetime.timedelta(hours=1)
#     # assert f.time_span_method == TimeSpanMethod.ACCUMULATED


# @pytest.mark.cache
# def test_grib_proc_seasonal():
#     ds = from_source(
#         "url",
#         earthkit_remote_test_data_file("xr_engine/date/jma_seasonal_fc_ref_time_per_member.grib"),
#     )

#     f = ds[0]
#     assert f.base_datetime == datetime.datetime(2014, 8, 29)
#     assert f.step == datetime.timedelta(days=33)
#     assert f.valid_datetime == datetime.datetime(2014, 10, 1)
#     # assert f.indexing_datetime == datetime.datetime(2014, 9, 1)


# # @pytest.mark.cache
# # def test_grib_proc_monthly():
# #     ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/seasonal_monthly.grib"))

# #     f = ds[0]
# #     assert f.base_datetime == datetime.datetime(1993, 10, 1)
# #     assert f.step == datetime.timedelta(days=31)
# #     assert f.valid_datetime == datetime.datetime(1993, 11, 1)


# # @pytest.mark.cache
# # def test_grib_time_step_in_minutes():
# #     ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/step_60m.grib"))

# #     f = ds[0]
# #     assert f.base_datetime == datetime.datetime(2024, 1, 15)
# #     assert f.step == datetime.timedelta(0)
# #     assert f.valid_datetime == datetime.datetime(2024, 1, 15)


# @pytest.mark.cache
# def test_legacy_grib_step_in_seconds():
#     ds = from_source("url", earthkit_remote_test_data_file("t_30s.grib"))
#     f = ds[0]

#     # ref = {
#     #     "base_time": [datetime.datetime(2023, 8, 20, 12)],
#     #     "valid_time": [datetime.datetime(2023, 8, 20, 12, 0, 30)],
#     # }
#     # assert ds.datetime() == ref

#     assert f.base_datetime == datetime.datetime(2023, 8, 20, 12, 0, 0)
#     assert f.valid_datetime == datetime.datetime(2023, 8, 20, 12, 0, 30)
#     assert f.step == datetime.timedelta(seconds=30)
#     assert f.get("grib.step") == "30s"
