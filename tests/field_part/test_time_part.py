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

from earthkit.data.field.part.time import ForecastTime
from earthkit.data.field.part.time import create_time


@pytest.mark.parametrize(
    "input_d,ref",
    [
        (
            [
                {"valid_datetime": "2016-09-25"},
                {"valid_datetime": "20160925"},
                {"valid_datetime": datetime.datetime(2016, 9, 25)},
            ],
            (
                datetime.datetime(2016, 9, 25),
                datetime.timedelta(0),
                datetime.datetime(2016, 9, 25),
            ),
        ),
        (
            [
                {"valid_datetime": "2016-09-25T12", "step": 0},
                {"valid_datetime": "20160925T12", "step": datetime.timedelta(0)},
            ],
            (
                datetime.datetime(2016, 9, 25, 12),
                datetime.timedelta(0),
                datetime.datetime(2016, 9, 25, 12),
            ),
        ),
        (
            [
                {"valid_datetime": "2016-09-25T12", "step": 6},
                {"valid_datetime": "20160925T12", "step": datetime.timedelta(hours=6)},
            ],
            (
                datetime.datetime(2016, 9, 25, 6),
                datetime.timedelta(hours=6),
                datetime.datetime(2016, 9, 25, 12),
            ),
        ),
        (
            [
                {"base_datetime": "2016-09-25T12", "step": 6},
                {"base_datetime": "20160925T12", "step": datetime.timedelta(hours=6)},
                {"forecast_reference_time": "2016-09-25T12", "forecast_period": 6},
            ],
            (
                datetime.datetime(2016, 9, 25, 12),
                datetime.timedelta(hours=6),
                datetime.datetime(2016, 9, 25, 18),
            ),
        ),
        (
            [
                {"base_datetime": "2016-09-25T12", "step": "30m"},
                {"base_datetime": "20160925T12", "step": datetime.timedelta(minutes=30)},
            ],
            (
                datetime.datetime(2016, 9, 25, 12),
                datetime.timedelta(hours=0, minutes=30),
                datetime.datetime(2016, 9, 25, 12, 30),
            ),
        ),
        (
            [
                {"base_datetime": "2016-09-25T12", "step": "90m"},
                {"base_datetime": "20160925T12", "step": datetime.timedelta(minutes=90)},
            ],
            (
                datetime.datetime(2016, 9, 25, 12),
                datetime.timedelta(hours=1, minutes=30),
                datetime.datetime(2016, 9, 25, 13, 30),
            ),
        ),
        (
            [
                {"base_datetime": "2020-09-25T12", "step": 30},
                {"base_datetime": "2020-09-25T12", "step": datetime.timedelta(hours=30)},
            ],
            (
                datetime.datetime(2020, 9, 25, 12),
                datetime.timedelta(hours=30),
                datetime.datetime(2020, 9, 26, 18),
            ),
        ),
        (
            {"base_datetime": "2020-09-25T12", "valid_datetime": "2020-09-26T18"},
            (
                datetime.datetime(2020, 9, 25, 12),
                datetime.timedelta(hours=30),
                datetime.datetime(2020, 9, 26, 18),
            ),
        ),
        (
            [
                {"date": "2020-09-25", "time": "1200"},
                {"date": "20200925", "time": "1200"},
                {"date": datetime.date(2020, 9, 25), "time": datetime.time(12)},
                # {"date": datetime.datetime(2020, 9, 25), "time": datetime.time(12)},
                # {"date": datetime.datetime(2020, 9, 25, 12), "time": datetime.time(12)},
            ],
            (
                datetime.datetime(2020, 9, 25, 12),
                datetime.timedelta(0),
                datetime.datetime(2020, 9, 25, 12),
            ),
        ),
        (
            [
                {"date": "2020-09-25", "time": "120"},
                {"date": "20200925", "time": "120"},
                # {"date": datetime.date(2020, 9, 25), "time": datetime.time(1, 20)},
                # {"date": datetime.datetime(2020, 9, 25), "time": datetime.time(1, 20)},
            ],
            (
                datetime.datetime(2020, 9, 25, 1, 20),
                datetime.timedelta(0),
                datetime.datetime(2020, 9, 25, 1, 20),
            ),
        ),
        (
            [
                {"date": "2020-09-25", "time": "1200", "step": 6},
                {"date": "2020-09-25", "time": "1200", "step": datetime.timedelta(hours=6)},
            ],
            (
                datetime.datetime(2020, 9, 25, 12),
                datetime.timedelta(hours=6),
                datetime.datetime(2020, 9, 25, 18),
            ),
        ),
    ],
)
def test_time_spec_from_dict_ok(input_d, ref):

    if not isinstance(input_d, list):
        input_d = [input_d]

    if isinstance(input_d, list):
        for d in input_d:
            t = create_time(d)

            assert t.base_datetime == ref[0]
            assert t.forecast_reference_time == ref[0]
            assert t.step == ref[1]
            assert t.forecast_period == ref[1]
            assert t.valid_datetime == ref[2]


@pytest.mark.parametrize(
    "input_d,error",
    [
        (
            [
                {"date": "2020-09-25T12", "time": "600"},
                {"date": datetime.datetime(2020, 9, 25, 12), "time": "600"},
            ],
            ValueError,
        ),
    ],
)
def test_time_spec_from_dict_error(input_d, error):
    if not isinstance(input_d, list):
        input_d = [input_d]

    if isinstance(input_d, list):
        for d in input_d:
            with pytest.raises(error):
                create_time(d)


def test_time_spec_alias_1():
    t = ForecastTime(base_datetime=datetime.datetime(2007, 1, 1, 12), step=datetime.timedelta(hours=6))
    assert t.base_datetime == datetime.datetime(2007, 1, 1, 12)
    assert t.step == datetime.timedelta(hours=6)
    assert t.valid_datetime == datetime.datetime(2007, 1, 1, 18)
    assert t.forecast_reference_time == datetime.datetime(2007, 1, 1, 12)
    assert t.forecast_period == datetime.timedelta(hours=6)


def test_time_spec_alias_2():
    t = create_time(
        dict(
            forecast_reference_time=datetime.datetime(2007, 1, 1, 12),
            forecast_period=datetime.timedelta(hours=6),
        )
    )
    assert t.base_datetime == datetime.datetime(2007, 1, 1, 12)
    assert t.step == datetime.timedelta(hours=6)
    assert t.valid_datetime == datetime.datetime(2007, 1, 1, 18)
    assert t.forecast_reference_time == datetime.datetime(2007, 1, 1, 12)
    assert t.forecast_period == datetime.timedelta(hours=6)


@pytest.mark.parametrize(
    "input_d,ref",
    [
        (
            [
                {"base_datetime": "2025-08-24T12:00:00", "step": 6},
                {"base_datetime": datetime.datetime(2025, 8, 24, 12), "step": datetime.timedelta(hours=6)},
                {
                    "forecast_reference_time": datetime.datetime(2025, 8, 24, 12),
                    "forecast_period": datetime.timedelta(hours=6),
                },
            ],
            {
                "base_datetime": datetime.datetime(2025, 8, 24, 12),
                "valid_datetime": datetime.datetime(2025, 8, 24, 18),
                "step": datetime.timedelta(hours=6),
            },
        ),
        (
            [
                {"valid_datetime": "2025-08-24T18:00:00", "step": datetime.timedelta(hours=6)},
                {"valid_datetime": datetime.datetime(2025, 8, 24, 18), "step": datetime.timedelta(hours=6)},
            ],
            {
                "base_datetime": datetime.datetime(2025, 8, 24, 12),
                "valid_datetime": datetime.datetime(2025, 8, 24, 18),
                "step": datetime.timedelta(hours=6),
            },
        ),
        (
            [
                {"base_datetime": "2025-08-24T12:00:00"},
                {"base_datetime": datetime.datetime(2025, 8, 24, 12)},
                {"forecast_reference_time": datetime.datetime(2025, 8, 24, 12)},
            ],
            {
                "base_datetime": datetime.datetime(2025, 8, 24, 12),
                "valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "step": datetime.timedelta(hours=0),
            },
        ),
        (
            [
                {"valid_datetime": "2025-08-24T12:00:00", "step": 0},
                {"valid_datetime": datetime.datetime(2025, 8, 24, 12), "step": datetime.timedelta(hours=0)},
            ],
            {
                "base_datetime": datetime.datetime(2025, 8, 24, 12),
                "valid_datetime": datetime.datetime(2025, 8, 24, 12),
                "step": datetime.timedelta(hours=0),
            },
        ),
        (
            [
                {"valid_datetime": "2007-01-03T18:00:00"},
                {"valid_datetime": datetime.datetime(2007, 1, 3, 18)},
            ],
            {
                "base_datetime": datetime.datetime(2007, 1, 1, 12),
                "valid_datetime": datetime.datetime(2007, 1, 3, 18),
                "step": datetime.timedelta(hours=54),
            },
        ),
        (
            {"step": datetime.timedelta(hours=6)},
            {
                "base_datetime": datetime.datetime(2007, 1, 1, 12),
                "valid_datetime": datetime.datetime(2007, 1, 1, 18),
                "step": datetime.timedelta(hours=6),
            },
        ),
        (
            {"step": datetime.timedelta(hours=6, minutes=30)},
            {
                "base_datetime": datetime.datetime(2007, 1, 1, 12),
                "valid_datetime": datetime.datetime(2007, 1, 1, 18, 30),
                "step": datetime.timedelta(hours=6, minutes=30),
            },
        ),
        (
            {
                "step": datetime.timedelta(hours=36),
            },
            {
                "base_datetime": datetime.datetime(2007, 1, 1, 12),
                "valid_datetime": datetime.datetime(2007, 1, 3, 0),
                "step": datetime.timedelta(hours=36),
            },
        ),
    ],
)
def test_time_spec_set(input_d, ref):

    t = ForecastTime(base_datetime=datetime.datetime(2007, 1, 1, 12), step=datetime.timedelta(0))

    if not isinstance(input_d, list):
        input_d = [input_d]

    for d in input_d:
        t1 = t.set(**d)

        for k, v in ref.items():
            assert getattr(t1, k) == v, f"key {k} expected {v} got {getattr(t, k)}"

        # the original object is unchanged
        assert t.base_datetime == datetime.datetime(2007, 1, 1, 12)
        assert t.valid_datetime == datetime.datetime(2007, 1, 1, 12)
        assert t.step == datetime.timedelta(hours=0)


@pytest.mark.parametrize(
    "input_d,error",
    [
        ({"date": "2020-09-25T12"}, ValueError),
        ({"date": "2020-09-25T12", "time": "600"}, ValueError),
        ({"time": "600"}, ValueError),
        ({"step_timedelta": datetime.timedelta(hours=6)}, ValueError),
    ],
)
def test_time_spec_set_error(input_d, error):

    t = ForecastTime(base_datetime=datetime.datetime(2007, 1, 1, 12), step=datetime.timedelta(0))

    with pytest.raises(error):
        t.set(**input_d)
