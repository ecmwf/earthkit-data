# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.utils.dates import datetime_from_grib
from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.dates import to_timedelta


def from_grib(handle):
    def _get(key, default=None):
        return handle.get(key, default)

    def _datetime(date_key, time_key):
        date = _get(date_key, None)
        if date is not None:
            time = _get(time_key, None)
            if time is not None:
                return datetime_from_grib(date, time)
        return None

    base = _datetime("dataDate", "dataTime")
    v = _get("endStep", None)
    if v is None:
        v = _get("step", None)
    step = to_timedelta(v)

    end = _get("endStep", None)
    if end is None:
        return to_timedelta(0)

    start = _get("startStep", None)
    if start is None:
        start = to_timedelta(0)

    step_range = to_timedelta(end) - to_timedelta(start)

    return dict(
        base_datetime=to_datetime(base),
        step=step,
        step_range=step_range,
    )


def to_grib(spec):
    raise NotImplementedError("GRIB encoding not implemented.")
