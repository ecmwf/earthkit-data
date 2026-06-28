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

from earthkit.data.utils.testing import earthkit_test_data_file, load_nc_or_xr_source


@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize(
    "_kwargs,ref_set",
    [
        (
            {"time.base_datetime": "2025-08-24T12:00:00", "time.step": 6},
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 18),
                "time.step": datetime.timedelta(hours=6),
                # "time_span": TimeSpan(),
            },
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
        ),
        (
            {"time.valid_datetime": "2025-08-24T18:00:00", "time.step": datetime.timedelta(hours=6)},
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 18),
                "time.step": datetime.timedelta(hours=6),
                # "time_span": TimeSpan(),
            },
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
        ),
        (
            {"time.base_datetime": "2025-08-24T12:00:00"},
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.step": datetime.timedelta(hours=0),
                # "time_span": TimeSpan(),
            },
        ),
        (
            {"time.base_datetime": datetime.datetime(2025, 8, 24, 12)},
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.step": datetime.timedelta(hours=0),
                # "time_span": TimeSpan(),
            },
        ),
        (
            {"time.valid_datetime": "2025-08-24T12:00:00", "time.step": 0},
            {
                "time.base_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "time.step": datetime.timedelta(hours=0),
                # "time_span": TimeSpan(),
            },
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
        ),
        (
            {"time.valid_datetime": "2007-01-03T18:00:00"},
            {
                "time.base_datetime": datetime.datetime(2007, 1, 1, 12),
                "time.valid_datetime": datetime.datetime(2007, 1, 3, 18),
                "time.step": datetime.timedelta(hours=54),
                # "time_span": TimeSpan(),
            },
        ),
        (
            {"time.valid_datetime": datetime.datetime(2007, 1, 3, 18)},
            {
                "time.base_datetime": datetime.datetime(2007, 1, 1, 12),
                "time.valid_datetime": datetime.datetime(2007, 1, 3, 18),
                "time.step": datetime.timedelta(hours=54),
                # "time_span": TimeSpan(),
            },
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
        ),
        (
            {"time.step": datetime.timedelta(hours=6)},
            {
                "time.base_datetime": datetime.datetime(2007, 1, 1, 12),
                "time.valid_datetime": datetime.datetime(2007, 1, 1, 18),
                "time.step": datetime.timedelta(hours=6),
                # "time_span": TimeSpan(),
            },
        ),
        (
            {"time.step": datetime.timedelta(hours=6, minutes=30)},
            {
                "time.base_datetime": datetime.datetime(2007, 1, 1, 12),
                "time.valid_datetime": datetime.datetime(2007, 1, 1, 18, 30),
                "time.step": datetime.timedelta(hours=6, minutes=30),
                # "time_span": TimeSpan(),
            },
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
        ),
    ],
)
def test_netcdf_set_time_1(mode, _kwargs, ref_set):
    ds_ori = load_nc_or_xr_source(earthkit_test_data_file("test4.nc"), mode)

    f = ds_ori[0].set(**_kwargs)

    for k, v in ref_set.items():
        assert f.get(k) == v, f"key {k} expected {v} got {f.get(k)}"

    # original message is unchanged
    assert ds_ori[0].get("time.base_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("time.valid_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("time.step") == datetime.timedelta(hours=0)
    # assert ds_ori[0].get("time_span") == datetime.timedelta(hours=0)
