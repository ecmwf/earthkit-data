# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
from enum import Enum

from earthkit.data.core.constants import ZERO_TIMEDELTA
from earthkit.data.utils.dates import to_timedelta


class TimeSpanMethodItem:
    def __init__(
        self,
        name: str,
        standard_name: str,
        long_name: str,
    ) -> None:
        self.name = name
        self.standard_name = standard_name
        self.long_name = long_name

    def __eq__(self, other):
        return self.name == other.name


_defs = {
    "accum": {"name": "accum", "standard_name": "air_pressure", "long_name": "pressure"},
    "avg": {
        "name": "avg",
        "standard_name": "air_pressure",
        "long_name": "pressure",
    },
    "instant": {
        "name": "instant",
        "standard_name": "air_pressure",
        "long_name": "pressure",
    },
    "max": {
        "name": "max",
        "standard_name": "air_pressure",
        "long_name": "pressure",
    },
}


class TimeSpanMethod(Enum):
    ACCUMULATED = TimeSpanMethodItem(**_defs["accum"])
    AVERAGE = TimeSpanMethodItem(**_defs["avg"])
    INSTANT = TimeSpanMethodItem(**_defs["instant"])
    MAX = TimeSpanMethodItem(**_defs["max"])


class TimeSpan:
    def __init__(self, value=datetime.timedelta(), method=TimeSpanMethod.INSTANT):
        try:
            self._value = to_timedelta(value)
        except Exception as e:
            raise ValueError(f"Invalid time span value: {value}") from e

        self._method = method
        if not isinstance(self._method, TimeSpanMethod):
            raise ValueError(f"Invalid time span method: {method}")
        self._check()

    @property
    def value(self):
        return self._value

    @property
    def method(self):
        return self._method

    def __repr__(self):
        return f"TimeSpan({self._value}, {self._method.value.name})"

    @staticmethod
    def build(data):
        if isinstance(data, TimeSpan):
            return data
        else:
            return TimeSpan(value=data)

    def _check(self):
        if self._value != ZERO_TIMEDELTA and self._method == TimeSpanMethod.INSTANT:
            raise ValueError("A non-zero time_span cannot be of type instant")

        if self._value == ZERO_TIMEDELTA and self._method != TimeSpanMethod.INSTANT:
            raise ValueError("A zero time_span must be of type instant")

    def __eq__(self, data):
        value = TimeSpan.build(data)
        return self._value == value._value and self._method == value._method

    def __hash__(self):
        return hash((self._value, self._method))
