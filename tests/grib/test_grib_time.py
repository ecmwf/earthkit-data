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
from earthkit.data.specs.time_span import TimeSpan
from earthkit.data.specs.time_span import TimeSpanMethod
from earthkit.data.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_TYPES  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_datetime_1(fl_type):
    ds, _ = load_grib_data("test.grib", fl_type)

    ref = {
        "base_time": [datetime.datetime(2020, 5, 13, 12)],
        "valid_time": [datetime.datetime(2020, 5, 13, 12)],
    }

    assert ds.datetime() == ref

    ref = {
        "base_time": datetime.datetime(2020, 5, 13, 12),
        "valid_time": datetime.datetime(2020, 5, 13, 12),
    }

    assert ds[0].datetime() == ref


def test_grib_fieldlist_datetime_2():
    ds = from_source(
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
    assert ds.datetime() == ref


@pytest.mark.cache
def test_grib_time_analysis():
    ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/msl_analysis.grib"))

    f = ds[0]
    assert f.base_datetime == datetime.datetime(2016, 9, 25)
    assert f.step == datetime.timedelta(0)
    assert f.valid_datetime == datetime.datetime(2016, 9, 25)
    assert f.time_span == TimeSpan()


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_time_forecast(fl_type):
    ds, _ = load_grib_data("t_time_series.grib", fl_type, folder="data")
    f = ds[4]

    assert f.valid_datetime == datetime.datetime(2020, 12, 21, 18, 0)
    assert f.base_datetime == datetime.datetime(2020, 12, 21, 12, 0)
    assert f.forecast_reference_time == datetime.datetime(2020, 12, 21, 12, 0)
    assert f.step == datetime.timedelta(hours=6)
    assert f.forecast_period == datetime.timedelta(hours=6)
    assert f.time_span == TimeSpan()


@pytest.mark.cache
def test_grib_time_step_range_1():
    ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/wgust_step_range.grib1"))

    f = ds[2]
    assert f.valid_datetime == datetime.datetime(2011, 12, 16, 12, 0)
    assert f.base_datetime == datetime.datetime(2011, 12, 15, 12, 0)
    assert f.forecast_reference_time == datetime.datetime(2011, 12, 15, 12, 0)
    assert f.step == datetime.timedelta(hours=24)
    assert f.forecast_period == datetime.timedelta(hours=24)
    assert f.time_span == TimeSpan(6, TimeSpanMethod.MAX)
    assert f.time_span_value == datetime.timedelta(hours=6)
    assert f.time_span_method == TimeSpanMethod.MAX


@pytest.mark.cache
def test_grib_time_step_range_2():
    ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/lsp_step_range.grib2"))

    f = ds[0]
    assert f.valid_datetime == datetime.datetime(2025, 5, 30)
    assert f.base_datetime == datetime.datetime(2025, 5, 27)
    assert f.step == datetime.timedelta(hours=72)
    assert f.time_span == TimeSpan(1, TimeSpanMethod.ACCUMULATED)
    assert f.time_span_value == datetime.timedelta(hours=1)
    assert f.time_span_method == TimeSpanMethod.ACCUMULATED

    f = ds[1]
    assert f.valid_datetime == datetime.datetime(2025, 5, 30, 1)
    assert f.base_datetime == datetime.datetime(2025, 5, 27)
    assert f.step == datetime.timedelta(hours=73)
    assert f.time_span == TimeSpan(1, TimeSpanMethod.ACCUMULATED)
    assert f.time_span_value == datetime.timedelta(hours=1)
    assert f.time_span_method == TimeSpanMethod.ACCUMULATED


@pytest.mark.cache
def test_grib_time_seasonal():
    ds = from_source(
        "url",
        earthkit_remote_test_data_file("xr_engine/date/jma_seasonal_fc_ref_time_per_member.grib"),
    )

    f = ds[0]
    assert f.base_datetime == datetime.datetime(2014, 8, 29)
    assert f.step == datetime.timedelta(days=33)
    assert f.valid_datetime == datetime.datetime(2014, 10, 1)
    assert f.time_span == TimeSpan()
    assert f.indexing_datetime == datetime.datetime(2014, 9, 1)


@pytest.mark.cache
def test_grib_time_monthly():
    ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/seasonal_monthly.grib"))

    f = ds[0]
    assert f.base_datetime == datetime.datetime(1993, 10, 1)
    assert f.step == datetime.timedelta(days=31)
    assert f.valid_datetime == datetime.datetime(1993, 11, 1)
    assert f.time_span == TimeSpan()
    assert f.indexing_datetime is None


@pytest.mark.cache
def test_grib_time_step_in_minutes():
    ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/step_60m.grib"))

    f = ds[0]
    assert f.base_datetime == datetime.datetime(2024, 1, 15)
    assert f.step == datetime.timedelta(0)
    assert f.valid_datetime == datetime.datetime(2024, 1, 15)
    assert f.time_span == TimeSpan()
