# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
from abc import ABCMeta

from earthkit.data.utils.dates import to_timedelta

from .spec import spec_aliases
from .time_span import TimeMethods


class ProcItem(metaclass=ABCMeta):
    def __init__(self, value, name) -> None:
        self.value = value
        self.name = name


class TimeProcItem(ProcItem):
    def __init__(self, value=datetime.timedelta(), method=TimeMethods.INSTANT):
        try:
            self.value = to_timedelta(value)
        except Exception as e:
            raise ValueError(f"Invalid time span value: {value}") from e

        self.method = method
        # if not isinstance(self.method, TimeSpanMethod):
        #     raise ValueError(f"Invalid time span method: {method}")
        # self._check()

    # @property
    # def value(self):
    #     return self._value

    # @property
    # def method(self):
    #     return self._method

    def __repr__(self):
        return f"TimeProcItem({self.value}, {self.method.value.name})"

    @classmethod
    def from_dict(cls, d: dict):
        value = d.get("value")
        method = d.get("method")

        return cls(value=value, method=method)

    # @staticmethod
    # def build(data):
    #     if isinstance(data, TimeSpan):
    #         return data
    #     else:
    #         return TimeSpan(value=data)

    # def _check(self):
    #     if self._value != ZERO_TIMEDELTA and self._method == TimeSpanMethods.INSTANT:
    #         raise ValueError("A non-zero time_span cannot be of type instant")

    #     if self._value == ZERO_TIMEDELTA and self._method != TimeSpanMethods.INSTANT:
    #         raise ValueError("A zero time_span must be of type instant")

    # def __eq__(self, data):
    #     value = TimeSpan.build(data)
    #     return self._value == value._value and self._method == value._method

    # def __hash__(self):
    #     return hash((self._value, self._method))


@spec_aliases
class Proc:
    """A specification of a parameter."""

    _SET_KEYS = tuple()

    def __init__(self, items) -> None:
        self.items = items

    @property
    def time(self) -> str:
        r"""str: Return the parameter variable."""
        for item in self.items:
            if isinstance(item, TimeProcItem):
                return item
        return None

    @classmethod
    def from_dict(cls, d: dict, allow_unused=False):
        """Create a Ensemble object from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing parameter data.

        Returns
        -------
        Realisation
            The created Realisation instance.
        """

        r = []
        for k, v in d.items():
            maker = _MAKERS.get(k, None)
            if maker is not None:
                r.append(maker.from_dict(v))
            else:
                raise ValueError(f"Unknown Proc item: {k}")

        return cls(r)


_MAKERS = {
    "time": TimeProcItem,
}
