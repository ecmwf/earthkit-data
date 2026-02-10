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

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_remote_test_data_file


def test_netcdf_datetime_1():
    ds = from_source("file", earthkit_examples_file("test.nc"))

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


def test_netcdf_datetime_2():
    ds = from_source("file", earthkit_examples_file("test.nc"))

    ref = {
        "base_time": [datetime.datetime(2020, 5, 13, 12)],
        "valid_time": [datetime.datetime(2020, 5, 13, 12)],
    }
    assert ds.datetime() == ref

    ds = from_source(
        "dummy-source",
        kind="netcdf",
        dims=["lat", "lon", "time"],
        variables=["a", "b"],
        coord_values=dict(
            time=[
                datetime.datetime(1990, 1, 1, 12, 0),
                datetime.datetime(1990, 1, 2, 12, 0),
            ]
        ),
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


def test_netcdf_time_analysis():
    ds = from_source("url", earthkit_examples_file("test.nc"))

    f = ds[0]
    assert f.time.base_datetime() == datetime.datetime(2020, 5, 13, 12, 0, 0)
    assert f.time.forecast_reference_time() == datetime.datetime(2020, 5, 13, 12, 0, 0)
    assert f.time.step() == datetime.timedelta(0)
    assert f.time.valid_datetime() == datetime.datetime(2020, 5, 13, 12, 0, 0)


def test_netcdf_valid_time_and_lead_time():
    ds = from_source("url", earthkit_remote_test_data_file("fa_ta850.nc"))

    assert ds[0].time.base_datetime() == datetime.datetime(2020, 1, 23, 0, 0, 0)
    assert ds[0].time.forecast_reference_time() == datetime.datetime(2020, 1, 23, 0, 0, 0)
    assert ds[0].time.valid_datetime() == datetime.datetime(2020, 1, 23, 0, 0, 0)
    assert ds[0].time.step() == datetime.timedelta(0)

    assert ds[0].time.base_datetime() == datetime.datetime(2020, 1, 23, 0, 0, 0)
    assert ds[0].time.forecast_reference_time() == datetime.datetime(2020, 1, 23, 0, 0, 0)
    assert ds[5].time.valid_datetime() == datetime.datetime(2020, 1, 23, 5, 0, 0)
    assert ds[5].time.step() == datetime.timedelta(hours=5)
