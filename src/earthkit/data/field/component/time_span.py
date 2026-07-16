# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from enum import Enum


class TimeMethod:
    def __init__(self, name: str) -> None:
        self.name = name

    def __eq__(self, other):
        if isinstance(other, TimeMethod):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other
        return False

    def __repr__(self):
        return self.name


_defs = {
    "ACCUMULATED": {
        "name": "accum",
    },
    "AVERAGE": {
        "name": "avg",
    },
    "INSTANT": {
        "name": "instant",
    },
    "MAX": {
        "name": "max",
    },
}


TimeMethods = Enum("TimeMethods", [(k, TimeMethod(**v)) for k, v in _defs.items()])

_TIME_METHODS = {t.value.name: t.value for t in TimeMethods}


def get_time_method(item: str, default=TimeMethods.INSTANT) -> TimeMethod:
    if isinstance(item, TimeMethods):
        return item.value
    elif isinstance(item, TimeMethod):
        if item.name in _TIME_METHODS:
            return item
    elif isinstance(item, str):
        if item in _TIME_METHODS:
            return _TIME_METHODS[item]
    elif item is None:
        return default.value

    raise ValueError(f"Unsupported time method type: {item}")
