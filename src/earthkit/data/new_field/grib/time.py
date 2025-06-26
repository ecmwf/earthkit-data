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

from ..time import Time


def missing_is_none(x):
    return None if x == 2147483647 else x


class GribTime(Time):
    def __init__(self, handle):
        self.handle = handle

    @property
    def base_datetime(self):
        return self._datetime("dataDate", "dataTime")

    @property
    def valid_datetime(self):
        return self._datetime("validityDate", "validityTime")

    # def reference_datetime(self):
    #     return self._datetime("referenceDate", "referenceTime")

    # def indexing_datetime(self):
    #     return self._datetime("indexingDate", "indexingTime")

    @property
    def step(self):
        v = self._get("endStep", None)
        if v is None:
            v = self._get("step", None)
        return to_timedelta(v)

    @property
    def range(self):
        v = self._get("endStep", None)
        if v is None:
            v = self._get("step", None)
        return to_timedelta(v)

    def _get(self, key, default=None):
        """Get a value from the handle, returning default if not found."""
        return self.handle.get(key, default)

    def _datetime(self, date_key, time_key):
        date = self._get(date_key, None)
        if date is not None:
            time = self._get(time_key, None)
            if time is not None:
                return datetime_from_grib(date, time)
        return None

    # def set_step(self, step):
    #     """Set the step value."""
    #     if step is None:
    #         self.handle.set("step", 2147483647)
    #     else:
    #         self.handle.set("step", step.total_seconds() // 3600)


class WrappedTime(Time):
    def __init__(self, time):
        self._time = time

    def __getattr__(self, item):
        return getattr(self._time, item)


class NewStepTime(WrappedTime):
    """A modified time class that handles missing values as None."""

    def __init__(self, step, time):
        super().__init__(time)
        self._step = to_timedelta(step)

    @property
    def step(self):
        """Return the forecast period of the time object."""
        return self._step

    @property
    def valid_datetime(self):
        return self.data.base_datetime + self._step


class NewValidDateTime(WrappedTime):
    """A modified time class that handles missing values as None."""

    def __init__(self, valid_datetime, time):
        super().__init__(time)
        self._valid_datetime = to_datetime(valid_datetime)
        if self._valid_datetime == self._time.base_datetime:
            raise ValueError("Valid datetime cannot be the same as base datetime.")

    @property
    def valid_datetime(self):
        """Return the valid datetime of the time object."""
        return self._valid_datetime

    @property
    def base_datetime(self):
        return self._valid_datetime - self.step
