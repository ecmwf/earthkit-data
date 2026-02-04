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
from abc import abstractmethod

from earthkit.data.utils.dates import to_timedelta

from .part import SimpleFieldPart
from .part import mark_key
from .part import part_keys
from .time_span import TimeMethods
from .time_span import get_time_method


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

        self.method = get_time_method(method)
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
        return f"TimeProcItem({self.value}, {self.method.name})"

    @classmethod
    def from_dict(cls, d: dict):
        value = d.get("value")
        method = d.get("method")

        return cls(value=value, method=method)

    def set(self, *, value=None, method=None):
        if value is None:
            value = self.value
        if method is None:
            method = self.method
        return TimeProcItem(value=value, method=method)

    # taticmethod
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


@part_keys
class BaseProc(SimpleFieldPart):
    """A specification of a parameter."""

    @mark_key("get")
    @abstractmethod
    def time(self) -> TimeProcItem:
        r"""TimeProcItem: Return the time processing item."""
        pass

    @mark_key("get")
    @abstractmethod
    def time_value(self) -> str:
        r"""str: Return the time processing value."""
        pass

    @mark_key("get")
    @abstractmethod
    def time_method(self) -> str:
        r"""str: Return the time processing method."""
        pass


class Proc(BaseProc):
    """A specification of processing."""

    def __init__(self, items) -> None:
        self.items = items

    @mark_key("get")
    def time(self) -> TimeProcItem:
        r"""str: Return the parameter variable."""
        for item in self.items:
            if isinstance(item, TimeProcItem):
                return item
        return None

    @mark_key("get")
    def time_value(self) -> str:
        r"""str: Return the parameter variable."""
        time = self.time
        if time is not None:
            return time.value
        return None

    @mark_key("get")
    def time_method(self) -> str:
        r"""str: Return the parameter variable."""
        time = self.time
        if time is not None:
            return time.method
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

    def set(self, *args, **kwargs):
        pass
        # d = normalise_set_kwargs_2(self, *args, allowed_keys=self._SET_KEYS, remove_nones=False, **kwargs)

        # current = {
        #     "level": self._level,
        #     "layer": self._layer,
        #     "type": self._type,
        # }

        # current.update(d)
        # return self.from_dict(current)


@part_keys
class ProcOri:
    """A specification of a parameter."""

    _SET_KEYS = tuple()
    _ALIASES = {}

    def __init__(self, items) -> None:
        self.items = items

    @mark_key("get")
    def time(self) -> str:
        r"""str: Return the parameter variable."""
        for item in self.items:
            if isinstance(item, TimeProcItem):
                return item
        return None

    @mark_key("get")
    def time_value(self) -> str:
        r"""str: Return the parameter variable."""
        time = self.time
        if time is not None:
            return time.value
        return None

    @mark_key("get")
    def time_method(self) -> str:
        r"""str: Return the parameter variable."""
        time = self.time
        if time is not None:
            return time.method
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

    def set(self, *args, **kwargs):
        pass
        # d = normalise_set_kwargs_2(self, *args, allowed_keys=self._SET_KEYS, remove_nones=False, **kwargs)

        # current = {
        #     "level": self._level,
        #     "layer": self._layer,
        #     "type": self._type,
        # }

        # current.update(d)
        # return self.from_dict(current)


_MAKERS = {
    "time": TimeProcItem,
}
