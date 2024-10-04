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

import numpy as np
import pytest

from earthkit.data.utils.dates import date_to_grib
from earthkit.data.utils.dates import datetime_to_grib
from earthkit.data.utils.dates import mars_like_date_list
from earthkit.data.utils.dates import numpy_datetime_to_datetime
from earthkit.data.utils.dates import numpy_timedelta_to_timedelta
from earthkit.data.utils.dates import step_to_grib
from earthkit.data.utils.dates import time_to_grib
from earthkit.data.utils.dates import timedeltas_to_int
from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.dates import to_datetime_list
from earthkit.data.utils.dates import to_time
from earthkit.data.utils.dates import to_timedelta

# Change to utc once aware datetime objects will be used
# tzinfo = datetime.timezone.utc
tzinfo = None


def relative_date(n):
    """Since it is based on calling now() returns both the relative date and day after."""
    if n <= 0:
        d = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=n)
        d = datetime.datetime(d.year, d.month, d.day)
        return (d, d + datetime.timedelta(days=1))
    else:
        raise ValueError(f"{n=} must be negative")


@pytest.mark.parametrize(
    "d,expected_value,error",
    [
        (20020502, datetime.datetime(2002, 5, 2), None),
        (np.int64(20020502), datetime.datetime(2002, 5, 2), None),
        ("20020502", datetime.datetime(2002, 5, 2), None),
        ("2002-05-02", datetime.datetime(2002, 5, 2), None),
        ("2002-05-02T00", datetime.datetime(2002, 5, 2), None),
        ("2002-05-02T00Z", datetime.datetime(2002, 5, 2, tzinfo=datetime.timezone.utc), None),
        ("2002-05-02T06", datetime.datetime(2002, 5, 2, 6), None),
        ("2002-05-02T06:11", datetime.datetime(2002, 5, 2, 6, 11), None),
        ("2002-05-02T06:11:03", datetime.datetime(2002, 5, 2, 6, 11, 3), None),
        (datetime.datetime(2002, 5, 2, 6, 11, 3), datetime.datetime(2002, 5, 2, 6, 11, 3), None),
        (np.datetime64("2002-05-02"), datetime.datetime(2002, 5, 2, tzinfo=tzinfo), None),
        (np.datetime64(0, "Y"), datetime.datetime(1970, 1, 1, tzinfo=tzinfo), None),
        (0, relative_date(0), None),
        (-1, relative_date(-1), None),
        (1, None, ValueError),
        (20020, None, ValueError),
    ],
)
def test_to_datetime(d, expected_value, error):
    if error is None:
        if isinstance(expected_value, tuple):
            assert to_datetime(d) in expected_value
        else:
            assert to_datetime(d) == expected_value
    else:
        with pytest.raises(error):
            to_datetime(d)


@pytest.mark.parametrize(
    "args,expected_value,error",
    [
        (
            (datetime.datetime(2002, 5, 2), datetime.datetime(2002, 5, 4), 1),
            [datetime.datetime(2002, 5, 2), datetime.datetime(2002, 5, 3), datetime.datetime(2002, 5, 4)],
            None,
        ),
        (
            (datetime.datetime(2002, 5, 4), datetime.datetime(2002, 5, 2), 1),
            None,
            AssertionError,
        ),
        (
            (datetime.datetime(2002, 5, 2), datetime.datetime(2002, 5, 4), 0),
            None,
            AssertionError,
        ),
        (
            (datetime.datetime(2002, 5, 2), datetime.datetime(2002, 5, 4), -1),
            None,
            AssertionError,
        ),
    ],
)
def test_mars_like_date_list(args, expected_value, error):
    if error is None:
        assert mars_like_date_list(*args) == expected_value
    else:
        with pytest.raises(error):
            mars_like_date_list(*args)


@pytest.mark.parametrize(
    "d,expected_value,error",
    [
        ([20020502, "to", 20020503], [datetime.datetime(2002, 5, 2), datetime.datetime(2002, 5, 3)], None),
        ((20020502, "to", 20020503), [datetime.datetime(2002, 5, 2), datetime.datetime(2002, 5, 3)], None),
        ([20020502, "TO", 20020503], [datetime.datetime(2002, 5, 2), datetime.datetime(2002, 5, 3)], None),
        (
            ["20020502", "to", "20020503"],
            [datetime.datetime(2002, 5, 2), datetime.datetime(2002, 5, 3)],
            None,
        ),
        (
            ["2002-05-02", "to", "2002-05-03"],
            [datetime.datetime(2002, 5, 2), datetime.datetime(2002, 5, 3)],
            None,
        ),
        (
            ["2002-05-02T06", "to", "2002-05-03T06"],
            [datetime.datetime(2002, 5, 2, 6), datetime.datetime(2002, 5, 3, 6)],
            None,
        ),
        (
            [datetime.datetime(2002, 5, 2), "to", datetime.datetime(2002, 5, 3)],
            [datetime.datetime(2002, 5, 2), datetime.datetime(2002, 5, 3)],
            None,
        ),
        (
            [20020502, "to", 20020504, "by", 2],
            [datetime.datetime(2002, 5, 2), datetime.datetime(2002, 5, 4)],
            None,
        ),
        (
            [datetime.datetime(2002, 5, 2), "to", datetime.datetime(2002, 5, 4), "by", 2],
            [datetime.datetime(2002, 5, 2), datetime.datetime(2002, 5, 4)],
            None,
        ),
        (20020502, [datetime.datetime(2002, 5, 2)], None),
        ("20020502", [datetime.datetime(2002, 5, 2)], None),
        (datetime.datetime(2002, 5, 2), [datetime.datetime(2002, 5, 2)], None),
        (np.datetime64("2002-05-02"), [datetime.datetime(2002, 5, 2, tzinfo=tzinfo)], None),
    ],
)
def test_to_datetime_list(d, expected_value, error):
    if error is None:
        assert to_datetime_list(d) == expected_value
    else:
        with pytest.raises(error):
            to_datetime_list(d)


@pytest.mark.parametrize(
    "d,expected_value,error",
    [
        (20020502, datetime.time(0), None),
        (np.int64(20020502), datetime.time(0), None),
        ("20020502", datetime.time(0), None),
        ("2002-05-02", datetime.time(0), None),
        ("2002-05-02T00", datetime.time(0), None),
        ("2002-05-02T00Z", datetime.time(0), None),
        ("2002-05-02T06", datetime.time(6), None),
        ("2002-05-02T06:11", datetime.time(6, 11), None),
        ("2002-05-02T06:11:03", datetime.time(6, 11, 3), None),
        (datetime.datetime(2002, 5, 2, 6, 11, 3), datetime.time(6, 11, 3), None),
        (np.datetime64("2002-05-02"), datetime.time(0), None),
        (np.datetime64(6, "h"), datetime.time(6), None),
    ],
)
def test_to_time(d, expected_value, error):
    if error is None:
        assert to_time(d) == expected_value
    else:
        with pytest.raises(error):
            to_time(d)


@pytest.mark.parametrize(
    "step,expected_delta,error",
    [
        (12, datetime.timedelta(hours=12), None),
        ("12h", datetime.timedelta(hours=12), None),
        ("12s", datetime.timedelta(seconds=12), None),
        ("12m", datetime.timedelta(minutes=12), None),
        ("1m", datetime.timedelta(minutes=1), None),
        ("", None, (ValueError, TypeError)),
        ("m", None, (ValueError, TypeError, AttributeError)),
        ("1Z", None, (ValueError, TypeError)),
        ("m1", None, (ValueError, TypeError)),
        ("-1", None, (ValueError, TypeError)),
        ("-1s", None, (ValueError, TypeError)),
        ("1.1s", None, (ValueError, TypeError)),
    ],
)
def test_to_timedelta(step, expected_delta, error):
    if error is None:
        assert to_timedelta(step) == expected_delta
    else:
        with pytest.raises(error):
            to_timedelta(step)


@pytest.mark.parametrize(
    "td,expected_delta,error",
    [
        (np.timedelta64(61, "s"), datetime.timedelta(minutes=1, seconds=1), None),
        (
            np.timedelta64((2 * 3600 + 61) * 1000, "ms"),
            datetime.timedelta(hours=2, minutes=1, seconds=1),
            None,
        ),
        (
            np.timedelta64((2 * 3600 + 61) * 1000 * 1000 * 1000, "ns"),
            datetime.timedelta(hours=2, minutes=1, seconds=1),
            None,
        ),
    ],
)
def test_numpy_timedelta_to_timedelta(td, expected_delta, error):
    if error is None:
        assert numpy_timedelta_to_timedelta(td) == expected_delta
    else:
        with pytest.raises(error):
            numpy_timedelta_to_timedelta(td)


@pytest.mark.parametrize(
    "td,expected_delta,error",
    [
        (np.datetime64("2002-05-02"), datetime.datetime(2002, 5, 2, tzinfo=tzinfo), None),
        (
            np.datetime64("2002-05-02T06"),
            datetime.datetime(2002, 5, 2, 6, tzinfo=tzinfo),
            None,
        ),
        (
            np.datetime64("2002-05-02T06:23"),
            datetime.datetime(2002, 5, 2, 6, 23, tzinfo=tzinfo),
            None,
        ),
        (np.datetime64(0, "s"), datetime.datetime(1970, 1, 1, tzinfo=tzinfo), None),
        (np.datetime64(30, "s"), datetime.datetime(1970, 1, 1, 0, 0, 30, tzinfo=tzinfo), None),
        (np.datetime64(30, "m"), datetime.datetime(1970, 1, 1, 0, 30, tzinfo=tzinfo), None),
        (np.datetime64(30, "h"), datetime.datetime(1970, 1, 2, 6, tzinfo=tzinfo), None),
    ],
)
def test_numpy_datetime_to_datetime(td, expected_delta, error):
    if error is None:
        assert numpy_datetime_to_datetime(td) == expected_delta
    else:
        with pytest.raises(error):
            numpy_datetime_to_datetime(td)


@pytest.mark.parametrize(
    "td,expected_value,error",
    [
        (
            [datetime.timedelta(hours=12), datetime.timedelta(hours=18)],
            ([12, 18], datetime.timedelta(hours=1)),
            None,
        ),
        (
            [datetime.timedelta(hours=12), datetime.timedelta(hours=18, minutes=30)],
            ([12 * 60, 18 * 60 + 30], datetime.timedelta(minutes=1)),
            None,
        ),
        (
            [datetime.timedelta(hours=12), datetime.timedelta(hours=18, seconds=30)],
            ([12 * 3600, 18 * 3600 + 30], datetime.timedelta(seconds=1)),
            None,
        ),
        (
            datetime.timedelta(hours=12),
            ([12], datetime.timedelta(hours=1)),
            None,
        ),
    ],
)
def test_timedeltas_to_int(td, expected_value, error):
    if error is None:
        assert timedeltas_to_int(td) == expected_value
    else:
        with pytest.raises(error):
            timedeltas_to_int(td)


@pytest.mark.parametrize(
    "d,expected_value,error",
    [
        (20020502, 20020502, None),
        (np.int64(20020502), 20020502, None),
        ("20020502", 20020502, None),
        ("2002-05-02", 20020502, None),
        ("2002-05-02T00", 20020502, None),
        ("2002-05-02T00Z", 20020502, None),
        ("2002-05-02T06", 20020502, None),
        ("2002-05-02T06:11", 20020502, None),
        ("2002-05-02T06:11:03", 20020502, None),
        (datetime.datetime(2002, 5, 2, 6, 11, 3), 20020502, None),
        (np.datetime64("2002-05-02"), 20020502, None),
        (np.datetime64(0, "Y"), 19700101, None),
    ],
)
def test_date_to_grib(d, expected_value, error):
    if error is None:
        assert date_to_grib(d) == expected_value
    else:
        with pytest.raises(error):
            date_to_grib(d)


@pytest.mark.parametrize(
    "d,expected_value,error",
    [
        (0, 0, None),
        (6, 6, None),
        (12, 12, None),
        (600, 600, None),
        (1200, 1200, None),
        (1230, 1230, None),
        (np.int64(0), 0, None),
        (np.int64(6), 6, None),
        (np.int64(12), 12, None),
        (np.int64(600), 600, None),
        (np.int64(1200), 1200, None),
        (np.int64(1230), 1230, None),
        ("0", 0, None),
        ("6", 6, None),
        ("12", 12, None),
        ("600", 600, None),
        ("1200", 1200, None),
        ("1230", 1230, None),
        (datetime.timedelta(minutes=0), 0, None),
        (datetime.timedelta(minutes=6), 6, None),
        (datetime.timedelta(hours=0), 0, None),
        (datetime.timedelta(hours=6), 600, None),
        (datetime.timedelta(hours=12), 1200, None),
        (datetime.timedelta(hours=12, minutes=6), 1206, None),
        (datetime.timedelta(hours=120, seconds=2), None, ValueError),
        (np.timedelta64(0, "m"), 0, None),
        (np.timedelta64(6, "m"), 6, None),
        (np.timedelta64(0, "h"), 0, None),
        (np.timedelta64(6, "h"), 600, None),
        (np.timedelta64(12, "h"), 1200, None),
        (np.timedelta64(12 * 60 + 30, "m"), 1230, None),
    ],
)
def test_time_to_grib(d, expected_value, error):
    if error is None:
        assert time_to_grib(d) == expected_value
    else:
        with pytest.raises(error):
            time_to_grib(d)


@pytest.mark.parametrize(
    "step,expected_value,error",
    [
        (0, 0, None),
        (6, 6, None),
        (12, 12, None),
        (120, 120, None),
        ("0h", "0h", None),
        ("6h", "6h", None),
        ("12h", "12h", None),
        ("120h", "120h", None),
        ("6m", "6m", None),
        ("6s", "6s", None),
        (np.timedelta64(6, "h"), 6, None),
        (np.timedelta64(6 * 3600 * 1000, "ms"), 6, None),
        (np.timedelta64(6 * 3600 * 1000 * 1000 * 1000, "ns"), 6, None),
        (np.timedelta64(61, "s"), "61s", None),
        (np.timedelta64((2 * 3600 + 61) * 1000, "ms"), "7261s", None),
        (
            np.timedelta64((2 * 3600 + 61) * 1000 * 1000 * 1000, "ns"),
            "7261s",
            None,
        ),
    ],
)
def test_step_to_grib(step, expected_value, error):
    if error is None:
        assert step_to_grib(step) == expected_value
    else:
        with pytest.raises(error):
            step_to_grib(step)


@pytest.mark.parametrize(
    "d,expected_value,error",
    [
        (datetime.datetime(2002, 5, 2), (20020502, 0), None),
        (datetime.datetime(2002, 5, 2, 6), (20020502, 600), None),
        (datetime.datetime(2002, 5, 2, 12), (20020502, 1200), None),
        (np.int64(20020502), (20020502, 0), None),
        ("20020502", (20020502, 0), None),
        ("2002-05-02", (20020502, 0), None),
        ("2002-05-02T00", (20020502, 0), None),
        ("2002-05-02T00Z", (20020502, 0), None),
        ("2002-05-02T06", (20020502, 600), None),
        ("2002-05-02T06:11", (20020502, 611), None),
        ("2002-05-02T06:11:03", (20020502, 611), None),
        (datetime.datetime(2002, 5, 2, 6, 11, 3), (20020502, 611), None),
        (np.datetime64("2002-05-02"), (20020502, 0), None),
        (np.datetime64("2002-05-02T06"), (20020502, 600), None),
        (np.datetime64(0, "Y"), (19700101, 0), None),
    ],
)
def test_datetime_to_grib(d, expected_value, error):
    if error is None:
        assert datetime_to_grib(d) == expected_value
    else:
        with pytest.raises(error):
            datetime_to_grib(d)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
