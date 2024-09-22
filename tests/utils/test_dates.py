#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from datetime import datetime
from datetime import timedelta
from datetime import timezone

import numpy as np
import pytest

from earthkit.data.utils.dates import date_to_grib
from earthkit.data.utils.dates import datetime_to_grib
from earthkit.data.utils.dates import mars_like_date_list
from earthkit.data.utils.dates import numpy_datetime_to_datetime
from earthkit.data.utils.dates import numpy_timedelta_to_timedelta
from earthkit.data.utils.dates import step_to_delta
from earthkit.data.utils.dates import step_to_grib
from earthkit.data.utils.dates import time_to_grib
from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.dates import to_datetime_list


@pytest.mark.parametrize(
    "d,expected_value,error",
    [
        (20020502, datetime(2002, 5, 2), None),
        (np.int64(20020502), datetime(2002, 5, 2), None),
        ("20020502", datetime(2002, 5, 2), None),
        ("2002-05-02", datetime(2002, 5, 2), None),
        ("2002-05-02", datetime(2002, 5, 2), None),
        ("2002-05-02T00", datetime(2002, 5, 2), None),
        ("2002-05-02T00Z", datetime(2002, 5, 2, tzinfo=timezone.utc), None),
        ("2002-05-02T06", datetime(2002, 5, 2, 6), None),
        ("2002-05-02T06:11", datetime(2002, 5, 2, 6, 11), None),
        ("2002-05-02T06:11:03", datetime(2002, 5, 2, 6, 11, 3), None),
        (datetime(2002, 5, 2, 6, 11, 3), datetime(2002, 5, 2, 6, 11, 3), None),
        (np.datetime64("2002-05-02"), datetime(2002, 5, 2, tzinfo=timezone.utc), None),
        (np.datetime64(0, "Y"), datetime(1970, 1, 1, tzinfo=timezone.utc), None),
    ],
)
def test_to_datetime(d, expected_value, error):
    if error is None:
        assert to_datetime(d) == expected_value
    else:
        with pytest.raises(error):
            to_datetime(d)


@pytest.mark.parametrize(
    "args,expected_value,error",
    [
        (
            (datetime(2002, 5, 2), datetime(2002, 5, 4), 1),
            [datetime(2002, 5, 2), datetime(2002, 5, 3), datetime(2002, 5, 4)],
            None,
        ),
        (
            (datetime(2002, 5, 4), datetime(2002, 5, 2), 1),
            None,
            AssertionError,
        ),
        (
            (datetime(2002, 5, 2), datetime(2002, 5, 4), 0),
            None,
            AssertionError,
        ),
        (
            (datetime(2002, 5, 2), datetime(2002, 5, 4), -1),
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
        ([20020502, "to", 20020503], [datetime(2002, 5, 2), datetime(2002, 5, 3)], None),
        ((20020502, "to", 20020503), [datetime(2002, 5, 2), datetime(2002, 5, 3)], None),
        ([20020502, "TO", 20020503], [datetime(2002, 5, 2), datetime(2002, 5, 3)], None),
        (["20020502", "to", "20020503"], [datetime(2002, 5, 2), datetime(2002, 5, 3)], None),
        (["2002-05-02", "to", "2002-05-03"], [datetime(2002, 5, 2), datetime(2002, 5, 3)], None),
        (["2002-05-02T06", "to", "2002-05-03T06"], [datetime(2002, 5, 2, 6), datetime(2002, 5, 3, 6)], None),
        (
            [datetime(2002, 5, 2), "to", datetime(2002, 5, 3)],
            [datetime(2002, 5, 2), datetime(2002, 5, 3)],
            None,
        ),
        ([20020502, "to", 20020504, "by", 2], [datetime(2002, 5, 2), datetime(2002, 5, 4)], None),
        (
            [datetime(2002, 5, 2), "to", datetime(2002, 5, 4), "by", 2],
            [datetime(2002, 5, 2), datetime(2002, 5, 4)],
            None,
        ),
        (20020502, [datetime(2002, 5, 2)], None),
        ("20020502", [datetime(2002, 5, 2)], None),
        (datetime(2002, 5, 2), [datetime(2002, 5, 2)], None),
        (np.datetime64("2002-05-02"), [datetime(2002, 5, 2, tzinfo=timezone.utc)], None),
    ],
)
def test_to_datetime_list(d, expected_value, error):
    if error is None:
        assert to_datetime_list(d) == expected_value
    else:
        with pytest.raises(error):
            to_datetime_list(d)


@pytest.mark.parametrize(
    "step,expected_delta,error",
    [
        (12, timedelta(hours=12), None),
        ("12h", timedelta(hours=12), None),
        ("12s", timedelta(seconds=12), None),
        ("12m", timedelta(minutes=12), None),
        ("1m", timedelta(minutes=1), None),
        ("", None, ValueError),
        ("m", None, ValueError),
        ("1Z", None, ValueError),
        ("m1", None, ValueError),
        ("-1", None, ValueError),
        ("-1s", None, ValueError),
        ("1.1s", None, ValueError),
    ],
)
def test_step_to_delta(step, expected_delta, error):
    if error is None:
        assert step_to_delta(step) == expected_delta
    else:
        with pytest.raises(error):
            step_to_delta(step)


@pytest.mark.parametrize(
    "td,expected_delta,error",
    [
        (np.timedelta64(61, "s"), timedelta(minutes=1, seconds=1), None),
        (np.timedelta64((2 * 3600 + 61) * 1000, "ms"), timedelta(hours=2, minutes=1, seconds=1), None),
        (
            np.timedelta64((2 * 3600 + 61) * 1000 * 1000 * 1000, "ns"),
            timedelta(hours=2, minutes=1, seconds=1),
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
        (np.datetime64("2002-05-02"), datetime(2002, 5, 2, tzinfo=timezone.utc), None),
        (np.datetime64("2002-05-02T06"), datetime(2002, 5, 2, 6, tzinfo=timezone.utc), None),
        (np.datetime64("2002-05-02T06:23"), datetime(2002, 5, 2, 6, 23, tzinfo=timezone.utc), None),
        (np.datetime64(0, "s"), datetime(1970, 1, 1, tzinfo=timezone.utc), None),
        (np.datetime64(30, "s"), datetime(1970, 1, 1, 0, 0, 30, tzinfo=timezone.utc), None),
        (np.datetime64(30, "m"), datetime(1970, 1, 1, 0, 30, tzinfo=timezone.utc), None),
        (np.datetime64(30, "h"), datetime(1970, 1, 2, 6, tzinfo=timezone.utc), None),
    ],
)
def test_numpy_datetime_to_datetime(td, expected_delta, error):
    if error is None:
        assert numpy_datetime_to_datetime(td) == expected_delta
    else:
        with pytest.raises(error):
            numpy_datetime_to_datetime(td)


@pytest.mark.parametrize(
    "d,expected_value,error",
    [
        (20020502, 20020502, None),
        (np.int64(20020502), 20020502, None),
        ("20020502", 20020502, None),
        ("2002-05-02", 20020502, None),
        ("2002-05-02", 20020502, None),
        ("2002-05-02T00", 20020502, None),
        ("2002-05-02T00Z", 20020502, None),
        ("2002-05-02T06", 20020502, None),
        ("2002-05-02T06:11", 20020502, None),
        ("2002-05-02T06:11:03", 20020502, None),
        (datetime(2002, 5, 2, 6, 11, 3), 20020502, None),
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
        (6, 600, None),
        (12, 1200, None),
        (600, 600, None),
        (1200, 1200, None),
        (np.int64(0), 0, None),
        (np.int64(6), 600, None),
        (np.int64(12), 1200, None),
        (np.int64(600), 600, None),
        (np.int64(1200), 1200, None),
        ("0", 0, None),
        ("6", 600, None),
        ("12", 1200, None),
        ("600", 600, None),
        ("1200", 1200, None),
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
        (datetime(2002, 5, 2), (20020502, 0), None),
        (datetime(2002, 5, 2, 6), (20020502, 600), None),
        (datetime(2002, 5, 2, 12), (20020502, 1200), None),
        (np.int64(20020502), (20020502, 0), None),
        ("20020502", (20020502, 0), None),
        ("2002-05-02", (20020502, 0), None),
        ("2002-05-02", (20020502, 0), None),
        ("2002-05-02T00", (20020502, 0), None),
        ("2002-05-02T00Z", (20020502, 0), None),
        ("2002-05-02T06", (20020502, 600), None),
        ("2002-05-02T06:11", (20020502, 611), None),
        ("2002-05-02T06:11:03", (20020502, 611), None),
        (datetime(2002, 5, 2, 6, 11, 3), (20020502, 611), None),
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
