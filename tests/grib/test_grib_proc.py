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
from earthkit.data.utils.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)


@pytest.mark.cache
def test_grib_proc_analysis():
    ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/msl_analysis.grib"))

    f = ds[0]
    assert f.time.base_datetime() == datetime.datetime(2016, 9, 25)
    assert f.time.step() == datetime.timedelta(0)
    assert f.time.valid_datetime() == datetime.datetime(2016, 9, 25)

    assert isinstance(f.proc.items, list)
    t = f.proc.time()
    assert t.value == datetime.timedelta(0)
    assert t.method == "instant"


@pytest.mark.cache
def test_grib_proc_step_range_1():
    ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/wgust_step_range.grib1"))

    f = ds[2]
    assert f.time.valid_datetime() == datetime.datetime(2011, 12, 16, 12, 0)
    assert f.time.base_datetime() == datetime.datetime(2011, 12, 15, 12, 0)
    assert f.time.forecast_reference_time() == datetime.datetime(2011, 12, 15, 12, 0)
    assert f.time.step() == datetime.timedelta(hours=24)
    assert f.time.forecast_period() == datetime.timedelta(hours=24)

    t = f.proc.time()
    assert t.value == datetime.timedelta(hours=6)
    assert t.method == "max"

    t = f.proc.items[0]
    assert t.value == datetime.timedelta(hours=6)
    assert t.method == "max"


@pytest.mark.cache
def test_grib_proc_step_range_2():
    ds = from_source("url", earthkit_remote_test_data_file("xr_engine/date/lsp_step_range.grib2"))

    f = ds[0]
    assert f.time.valid_datetime() == datetime.datetime(2025, 5, 30)
    assert f.time.base_datetime() == datetime.datetime(2025, 5, 27)
    assert f.time.step() == datetime.timedelta(hours=72)

    t = f.proc.time()
    assert t.value == datetime.timedelta(hours=1)
    assert t.method == "accum"

    f = ds[1]
    assert f.time.valid_datetime() == datetime.datetime(2025, 5, 30, 1)
    assert f.time.base_datetime() == datetime.datetime(2025, 5, 27)
    assert f.time.step() == datetime.timedelta(hours=73)

    t = f.proc.time()
    assert t.value == datetime.timedelta(hours=1)
    assert t.method == "accum"
