# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
from abc import ABCMeta, abstractmethod
from typing import Any, Optional

from earthkit.data.utils.dates import to_timedelta

from .component import SimpleFieldComponent, component_keys, mark_get_key
from .time_span import TimeMethod, TimeMethods, get_time_method


class ProcItem(metaclass=ABCMeta):
    """A base class for field processing items.

    Parameters
    ----------
    value : Any
        The value associated with the processing item. The type of this
        value depends on the specific type.
    method : Any
        The method of the processing item, which can be used to identify the type of processing.

    """

    def __init__(self, value, method) -> None:
        self.value = value
        self.method = method


class TimeProcItem(ProcItem):
    """A time processing item, which consists of a time span value and a time processing method.

    Parameters
    ----------
    value : Union[datetime.timedelta, str, int]
        The time span value, which can be a datetime.timedelta or any value that can be converted
        to a datetime.timedelta using the to_timedelta function.
    method : TimeMethod, str
        The time processing method, which can be a string that identifies the
        method or a TimeMethod
    """

    def __init__(self, value=datetime.timedelta(), method=TimeMethods.INSTANT):
        try:
            self.value = to_timedelta(value)
        except Exception as e:
            raise ValueError(f"Invalid time span value: {value}") from e

        self.method = get_time_method(method)
        # if not isinstance(self.method, TimeSpanMethod):
        #     raise ValueError(f"Invalid time span method: {method}")
        # self._check()

    def __repr__(self):
        return f"TimeProcItem({self.value}, {self.method.name})"

    @classmethod
    def from_dict(cls, d: dict):
        """Create a TimeProcItem object from a dictionary."""
        value = d.get("value")
        method = d.get("method")

        return cls(value=value, method=method)

    def set(self, *, value=None, method=None):
        if value is None:
            value = self.value
        if method is None:
            method = self.method
        return TimeProcItem(value=value, method=method)


@component_keys
class ProcBase(SimpleFieldComponent):
    """Base class to describe post-processing operations related to a field.

    This class defines the interface for processing components, which can represent
    different types of temporal or spatial processing operations.

    Please note this is interface is still under development and and its final form
    is not yet fully defined.

    The processing information is stored as a list of ProcItem instances, which can include different types
    of processing items. Currently, the only supported type of processing item is TimeProcItem,
    which represents certain time processing operations.

    The current interface only allows access to the first temporal processing item in the list of
    processing items (if any), and its associated value and method. Each of these methods has an associated key
    that can be used in the :meth:`get` method to retrieve the corresponding information. The list
    of supported keys are as follows:

    - "time"
    - "time_value"
    - "time_method"

    Typically, this object is used as a component of a field, and can be accessed via the :attr:`time`
    attribute of a field. The keys above can also be accessed via the :meth:`get` method of the field,
    using the "proc." prefix.

    The following example demonstrates how to access the time information from a field using
    various methods and keys:

        >>> import earthkit.data as ekd
        >>> field = ekd.from_source("file", "lsp_step_range.grib2").to_fieldlist()[0]
        >>> field.proc.time()
        TimeProcItem(datetime.timedelta(hours=72), <TimeMethods.ACCUM: 'accum
        >>> field.proc.time_value()
        datetime.timedelta(hours=72)
        >>> field.proc.get("time_value")
        datetime.timedelta(hours=72)
        >>> field.proc.get("time_method")
        <TimeMethods.ACCUM: 'accum'>

    The time component is immutable. Currently, no set method is implemented, but in the future, a set
    method will be added to create a new instance with updated values.
    """

    @abstractmethod
    def items(self):
        pass

    @mark_get_key
    @abstractmethod
    def time(self) -> Optional[TimeProcItem]:
        r"""Return the first time processing item.

        Returns
        -------
        TimeProcItem, None
            The first time processing item or None if not available.
        """
        pass

    @mark_get_key
    @abstractmethod
    def time_value(self) -> Optional[Any]:
        r"""Return the processing value from the first time processing item.

        Returns
        -------
        str, None
            The processing value from the first time processing item or None if not available.
        """
        pass

    @mark_get_key
    @abstractmethod
    def time_method(self) -> Optional[TimeMethod]:
        r"""Return the processing method from the first time processing item.

        Returns
        -------
        str, None
            The processing method from the first time processing item or None if not available.
        """
        pass


class EmptyProc(ProcBase):
    """An empty processing component, which represents the absence of any processing information."""

    def items(self):
        return []

    def time(self) -> None:
        return None

    def time_value(self) -> None:
        return None

    def time_method(self) -> None:
        return None

    @classmethod
    def from_dict(cls, d: dict):
        return cls()

    def to_dict(self) -> dict:
        return dict()

    def set(self, *args, **kwargs):
        raise ValueError("Cannot set values on EmptyProc")

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        pass


class Proc(ProcBase):
    """A class to describe post-processing operations related to a field.

    Parameters
    ----------
    items : list of ProcItem
        A list of processing items, which can include different types of processing items. Currently, the
        only supported type of processing item is TimeProcItem, which represents certain
        time processing operations.

    """

    def __init__(self, items) -> None:
        self._items = items

    def items(self):
        return self._items

    @mark_get_key
    def time(self) -> Optional[TimeProcItem]:
        r"""Return the time processing item."""
        for item in self._items:
            if isinstance(item, TimeProcItem):
                return item
        return None

    @mark_get_key
    def time_value(self) -> Optional[Any]:
        r"""Return the time processing value."""
        time = self.time
        if time is not None:
            return time.value
        return None

    @mark_get_key
    def time_method(self) -> Optional[TimeMethod]:
        r"""Return the time processing method."""
        time = self.time
        if time is not None:
            return time.method
        return None

    @classmethod
    def from_dict(cls, d: dict):
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

    def to_dict(self):
        return dict()

    def set(self, *args, **kwargs):
        """Set new values for the processing component and return a new instance.

        This method is currently not implemented, and raises a NotImplementedError.
        """
        raise NotImplementedError("Setting values on Proc is not yet implemented")

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        pass


_MAKERS = {
    "time": TimeProcItem,
}
