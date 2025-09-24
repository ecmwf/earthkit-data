# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from enum import Enum

from earthkit.data.core.config import ZERO_TIMEDELTA
from earthkit.data.utils.dates import to_timedelta

STATS = {}
TIME_SPAN_TYPE_ENUM = []


class TimeSpanStatsItem:
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

    # #
    # def is_level_type(data):
    #     return isinstance(data, TimeSpanType)


_defs = {
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
}


class TimeSpanStats(Enum):
    AVERAGE = TimeSpanStatsItem(**_defs["avg"])
    INSTANT = TimeSpanStatsItem(**_defs["instant"])


# for _, v in _defs.items():
#     t = TimeSpanStats(**v)
#     assert t.name not in STATS, f"Time span type {t.name} already defined"
#     STATS[t.name] = t
#     # TIME_SPAN_TYPE_ENUM.append(t)
#     # name = t.name.upper()
#     # setattr(TimeSpanStats, name, len(TIME_SPAN_TYPE_ENUM) - 1)

# TimeSpanType.AVERAGE = TIME_SPAN_TYPES["avg"]
# TimeSpanType.INSTANT = TIME_SPAN_TYPES["instant"]

# INSTANT_TIME_SPAN_TYPE = TIME_SPAN_TYPES["instant"]
# AVGERAGE_TIME_SPAN_TYPE = TIME_SPAN_TYPES["avg"]


def get_time_span_stats(data, default=TimeSpanStats.INSTANT):
    # if isinstance(data, TimeSpanStatsItem):
    #     if data in TIME_SPAN_TYPE_MAP.values():
    #         return data
    #     else:
    #         raise ValueError(f"Unsupported time span type: {type(data)}")
    # elif isinstance(data, int):
    #     return TIME_SPAN_TYPE_ENUM[data]
    # elif isinstance(data, str):
    #     return TIME_SPAN_TYPE_MAP.get(data, default)

    raise ValueError(f"Cannot find  time span type for {data=}")


# class TimeSpanTypes:
#     AVERAGE = TIME_SPAN_TYPES["avg"]
#     INSTANT = TIME_SPAN_TYPES["instant"]

#     @staticmethod
#     def get(name_or_object, default=INSTANT):
#         if isinstance(name_or_object, TimeSpanType):
#             if name_or_object in TIME_SPAN_TYPES.values():
#                 return name_or_object
#             else:
#                 raise ValueError(f"Unsupported time span type: {type(name_or_object)}")
#         return TIME_SPAN_TYPES.get(name_or_object, default)

#     def is_level_type(data):
#         return isinstance(data, TimeSpanType)


class TimeSpan:
    # INSTANT_STATS = TIME_SPAN_TYPE_MAP["instant"]

    def __init__(self, value=ZERO_TIMEDELTA, stats=TimeSpanStats.INSTANT):
        self._value = to_timedelta(value)
        self._stats = stats
        self._check()

    @property
    def value(self):
        return self._value

    @property
    def stats(self):
        return self._stats

    def __repr__(self):
        return f"TimeSpan({self._value}, {self._stats.name})"

    @staticmethod
    def build(data):
        if isinstance(data, TimeSpan):
            return data
        if isinstance(data, tuple):
            return TimeSpan(value=data[0], stats=data[1])
        return TimeSpan(value=data)

    def _check(self):
        if self._value != ZERO_TIMEDELTA and self._stats == TimeSpanStats.INSTANT:
            raise ValueError("A non-zero time_span cannot be of type instant")

        if self._value == ZERO_TIMEDELTA and self._stats != TimeSpanStats.INSTANT:
            raise ValueError("A zero time_span must be of type instant")

    def __eq__(self, data):
        value = TimeSpan.build(data)
        return self._value == value._value and self._stats == value._stats


INSTANT_TIME_SPAN = TimeSpan()
