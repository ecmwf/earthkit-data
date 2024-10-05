# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import re

import numpy as np

from earthkit.data.wrappers import get_wrapper

ECC_SECONDS_FACTORS = {"s": 1, "m": 60, "h": 3600}
NUM_STEP_PATTERN = re.compile(r"\d+")
SUFFIX_STEP_PATTERN = re.compile(r"\d+[a-zA-Z]{1}")


def to_datetime(dt):
    if isinstance(dt, datetime.datetime):
        return dt

    if isinstance(dt, datetime.date):
        return datetime.datetime(dt.year, dt.month, dt.day)

    if hasattr(dt, "dtype") and np.issubdtype(dt.dtype, np.datetime64):
        return numpy_datetime_to_datetime(dt)

    if isinstance(dt, np.int64):
        dt = int(dt)

    dt = get_wrapper(dt)

    return to_datetime(dt.to_datetime())


def mars_like_date_list(start, end, by):
    """Return a list of datetime objects from start to end.

    Parameters
    ----------
    start : datetime.datetime
        Start datetime object
    end : datetime.datetime
        End datetime object
    by : int
        Hours between each datetime object

    Returns
    -------
    list of datetime.datetime
    """
    assert by > 0, by
    assert end >= start
    result = []
    while start <= end:
        result.append(start)
        start = start + datetime.timedelta(days=by)
    return result


def to_datetime_list(datetimes):  # noqa C901
    if isinstance(datetimes, (datetime.datetime, np.datetime64)):
        return to_datetime_list([datetimes])

    if isinstance(datetimes, (list, tuple)):
        if len(datetimes) == 3 and isinstance(datetimes[1], str) and datetimes[1].lower() == "to":
            return mars_like_date_list(to_datetime(datetimes[0]), to_datetime(datetimes[2]), 1)

        if (
            len(datetimes) == 5
            and isinstance(datetimes[1], str)
            and isinstance(datetimes[3], str)
            and datetimes[1].lower() == "to"
            and datetimes[3].lower() == "by"
        ):
            return mars_like_date_list(
                to_datetime(datetimes[0]), to_datetime(datetimes[2]), int(datetimes[4])
            )

        return [to_datetime(x) for x in datetimes]

    datetimes = get_wrapper(datetimes)

    return to_datetime_list(datetimes.to_datetime_list())


def to_date_list(obj):
    return sorted(set(to_datetime_list(obj)))


def to_time(dt):
    if isinstance(dt, float):
        dt = int(dt)

    if isinstance(dt, str):
        if len(dt) <= 4:
            dt = int(dt)
        else:
            return to_datetime(dt).time()

    if isinstance(dt, np.int64):
        dt = int(dt)

    if isinstance(dt, int):
        if dt >= 2400:
            return to_datetime(dt).time()
        else:
            h = int(dt / 100)
            m = dt % 100
            return datetime.time(hour=h, minute=m)

    if isinstance(dt, datetime.time):
        return dt

    if isinstance(dt, datetime.datetime):
        return dt.time()

    if isinstance(dt, datetime.date):
        return dt.time()

    if hasattr(dt, "dtype") and np.issubdtype(dt.dtype, np.datetime64):
        return numpy_datetime_to_datetime(dt).time()

    if hasattr(dt, "dtype") and np.issubdtype(dt.dtype, np.timedelta64):
        dt = numpy_timedelta_to_timedelta(dt)

    if isinstance(dt, datetime.timedelta):
        return datetime.time(
            hour=int(dt.total_seconds()) // 3600,
            minute=int(dt.total_seconds()) // 60 % 60,
            second=int(dt.total_seconds()) % 60,
        )

    raise ValueError(f"Failed to convert time={dt} of type={type(dt)} to datetime.time")


def to_time_list(times):
    if not isinstance(times, (list, tuple)):
        return to_time_list([times])
    return [to_time(x) for x in times]


def to_timedelta(td):
    if isinstance(td, int):
        return datetime.timedelta(hours=td)

    if isinstance(td, datetime.time):
        return datetime.timedelta(hours=td.hour, minutes=td.minute, seconds=td.second)

    # eccodes step format
    # TODO: make it work for all the ecCodes step formats
    if isinstance(td, str):
        if re.fullmatch(NUM_STEP_PATTERN, td):
            return datetime.timedelta(hours=int(td))

        if re.fullmatch(SUFFIX_STEP_PATTERN, td):
            factor = ECC_SECONDS_FACTORS.get(td[-1], None)
            if factor is None:
                raise ValueError(f"Unsupported ecCodes step units in step: {td}")
            return datetime.timedelta(seconds=int(td[:-1]) * factor)

    if isinstance(td, datetime.timedelta):
        return td

    if np.issubdtype(td, np.timedelta64):
        return numpy_timedelta_to_timedelta(td)

    raise ValueError(f"Failed to convert td={td} type={type(td)} to timedelta")


def numpy_timedelta_to_timedelta(td):
    td = td.astype("timedelta64[s]").astype(int)
    return datetime.timedelta(seconds=int(td))


def numpy_datetime_to_datetime(dt):
    dt = dt.astype("datetime64[s]").astype(int)
    return datetime.datetime.fromtimestamp(int(dt), datetime.timezone.utc).replace(tzinfo=None)


def timedeltas_to_int(td):
    def _gcd(td):
        if td.total_seconds() % 3600 == 0:
            return datetime.timedelta(hours=1)
        if td.total_seconds() % 60 == 0:
            return datetime.timedelta(minutes=1)
        if td.microseconds == 0:
            return datetime.timedelta(seconds=1)
        else:
            return td.resolution

    if not isinstance(td, (list, tuple)):
        td = [td]

    resolution = min([_gcd(x) for x in td])
    resolution_secs = int(resolution.total_seconds())
    return [int(x.total_seconds() / resolution_secs) for x in td], resolution


def date_to_grib(d):
    try:
        d = to_datetime(d)
        if isinstance(d, datetime.datetime):
            return int(d.year * 10000 + d.month * 100 + d.day)
    except Exception as e:
        raise ValueError(f"Cannot convert date={d} of type={type(d)} to grib metadata. {e}")


def time_to_grib(t):
    t = to_time(t)

    if isinstance(t, datetime.time):
        return t.hour * 100 + t.minute
    try:
        t = int(t)
        if t < 100:
            t = t * 100
    except ValueError:
        pass

    return t


def step_to_grib(step):
    if isinstance(step, (int, str)):
        return step
    elif isinstance(step, np.int64):
        return int(step)

    step = to_timedelta(step)

    if isinstance(step, datetime.timedelta):
        hours, minutes, seconds = (
            int(step.total_seconds() // 3600),
            int(step.seconds // 60 % 60),
            int(step.seconds % 60),
        )
        if seconds == 0:
            if minutes == 0:
                return hours
            else:
                return f"{hours*60}{minutes}m"
        else:
            return f"{int(step.total_seconds())}s"

    raise ValueError(f"Cannot convert step={step} of type={type(step)} to grib metadata")


def datetime_to_grib(dt):
    dt = to_datetime(dt)
    date = int(dt.strftime("%Y%m%d"))
    time = dt.hour * 100 + dt.minute
    return date, time


def datetime_from_grib(date, time):
    date = int(date)
    time = int(time)

    return datetime.datetime(
        date // 10000,
        date % 10000 // 100,
        date % 100,
        time // 100,
        time % 100,
    )
