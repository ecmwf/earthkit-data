# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Processing component for fields.

A processing component describes post-processing operations applied to a field,
such as time-based statistical processing or ensemble statistics.
"""

from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import List, Optional

from .component import SimpleFieldComponent, component_keys, mark_get_key
from .duration import Duration, to_duration


class ProcessingKind(Enum):
    """The kind of processing applied to a field."""

    TIME_PROCESSING = "time_processing"
    ENSEMBLE_STATISTICS = "ensemble_statistics"


class ProcessingMethod(Enum):
    """The statistical method used in processing."""

    MAXIMUM = "maximum"
    MINIMUM = "minimum"
    POINT = "point"
    MEAN = "mean"
    SUM = "sum"
    MEDIAN = "median"
    STANDARD_DEVIATION = "standard_deviation"
    VARIANCE = "variance"


def get_processing_kind(value) -> ProcessingKind:
    """Convert a value to a ProcessingKind enum member.

    Parameters
    ----------
    value : ProcessingKind, str, or None
        The value to convert.

    Returns
    -------
    ProcessingKind
        The corresponding enum member.

    Raises
    ------
    ValueError
        If the value cannot be mapped to a ProcessingKind.
    """
    if isinstance(value, ProcessingKind):
        return value
    if isinstance(value, str):
        try:
            return ProcessingKind(value)
        except ValueError:
            # Try uppercase name match
            try:
                return ProcessingKind[value.upper()]
            except KeyError:
                pass
    raise ValueError(f"Unknown processing kind: {value!r}")


def get_processing_method(value) -> ProcessingMethod:
    """Convert a value to a ProcessingMethod enum member.

    Parameters
    ----------
    value : ProcessingMethod, str, or None
        The value to convert.

    Returns
    -------
    ProcessingMethod
        The corresponding enum member.

    Raises
    ------
    ValueError
        If the value cannot be mapped to a ProcessingMethod.
    """
    if isinstance(value, ProcessingMethod):
        return value
    if isinstance(value, str):
        try:
            return ProcessingMethod(value)
        except ValueError:
            # Try uppercase name match
            try:
                return ProcessingMethod[value.upper()]
            except KeyError:
                pass
    raise ValueError(f"Unknown processing method: {value!r}")


class ProcessingItem(metaclass=ABCMeta):
    """Base class for processing items.

    A processing item describes a single processing operation applied to a field.

    Parameters
    ----------
    kind : ProcessingKind
        The kind of processing (time_processing, ensemble_statistics).
    method : ProcessingMethod
        The statistical method used (maximum, minimum, mean, etc.).
    """

    def __init__(self, kind: ProcessingKind, method: ProcessingMethod) -> None:
        self.kind = get_processing_kind(kind)
        self.method = get_processing_method(method)

    @abstractmethod
    def to_dict(self) -> dict:
        """Serialize the processing item to a dictionary."""
        pass

    @classmethod
    def from_dict(cls, d: dict) -> "ProcessingItem":
        """Create a ProcessingItem from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary with at least ``kind`` and ``method`` keys.

        Returns
        -------
        ProcessingItem
            The appropriate subclass instance.
        """
        kind = get_processing_kind(d["kind"])
        if kind == ProcessingKind.TIME_PROCESSING:
            return TimeProcessingItem.from_dict(d)
        elif kind == ProcessingKind.ENSEMBLE_STATISTICS:
            return EnsembleProcessingItem.from_dict(d)
        else:
            raise ValueError(f"Unknown processing kind: {kind}")


class TimeProcessingItem(ProcessingItem):
    """A time-based processing item.

    Describes time-based statistical processing of a field, such as computing
    the maximum over a time window.

    Parameters
    ----------
    method : ProcessingMethod or str
        The statistical method (e.g. "maximum", "mean").
    window_length : Duration, datetime.timedelta, str, or None
        The length of the time window over which the processing is applied.
        Can be an ISO 8601 duration string (e.g. ``"PT6H"``).
    sampling_frequency : Duration, datetime.timedelta, str, or None
        The sampling frequency of the input data within the window.
        Can be an ISO 8601 duration string (e.g. ``"PT1H"``).
    """

    def __init__(
        self,
        method: ProcessingMethod = ProcessingMethod.POINT,
        window_length: Optional[Duration] = None,
        sampling_frequency: Optional[Duration] = None,
    ) -> None:
        super().__init__(kind=ProcessingKind.TIME_PROCESSING, method=method)
        self.window_length = to_duration(window_length)
        self.sampling_frequency = to_duration(sampling_frequency)

    def __repr__(self) -> str:
        parts = [f"method={self.method.value!r}"]
        if self.window_length is not None:
            parts.append(f"window_length={self.window_length!r}")
        if self.sampling_frequency is not None:
            parts.append(f"sampling_frequency={self.sampling_frequency!r}")
        return f"TimeProcessingItem({', '.join(parts)})"

    def to_dict(self) -> dict:
        d = {
            "kind": self.kind.value,
            "method": self.method.value,
        }
        if self.window_length is not None:
            d["window_length"] = self.window_length.to_iso_string()
        if self.sampling_frequency is not None:
            d["sampling_frequency"] = self.sampling_frequency.to_iso_string()
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "TimeProcessingItem":
        """Create a TimeProcessingItem from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary with ``method`` and optionally ``window_length``, ``sampling_frequency``.

        Returns
        -------
        TimeProcessingItem
        """
        return cls(
            method=d.get("method", "point"),
            window_length=d.get("window_length"),
            sampling_frequency=d.get("sampling_frequency"),
        )


class EnsembleProcessingItem(ProcessingItem):
    """An ensemble statistics processing item.

    Describes statistical processing across ensemble members.

    Parameters
    ----------
    method : ProcessingMethod or str
        The statistical method (e.g. "mean", "standard_deviation").
    ensemble_size : int
        The number of ensemble members used in the computation.
    """

    def __init__(
        self,
        method: ProcessingMethod = ProcessingMethod.MEAN,
        ensemble_size: int = 0,
    ) -> None:
        super().__init__(kind=ProcessingKind.ENSEMBLE_STATISTICS, method=method)
        self.ensemble_size = int(ensemble_size)

    def __repr__(self) -> str:
        return f"EnsembleProcessingItem(method={self.method.value!r}, ensemble_size={self.ensemble_size})"

    def to_dict(self) -> dict:
        return {
            "kind": self.kind.value,
            "method": self.method.value,
            "ensemble_size": self.ensemble_size,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EnsembleProcessingItem":
        """Create an EnsembleProcessingItem from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary with ``method`` and ``ensemble_size``.

        Returns
        -------
        EnsembleProcessingItem
        """
        return cls(
            method=d.get("method", "mean"),
            ensemble_size=d.get("ensemble_size", 0),
        )


@component_keys
class ProcessingBase(SimpleFieldComponent):
    """Base class for the processing component of a field.

    The processing component is a list of :class:`ProcessingItem` instances describing
    post-processing operations applied to the field (e.g. time statistics, ensemble statistics).

    The supported keys for :meth:`get` are:

    - "items": the full list of processing items
    - "time_processing": the first TimeProcessingItem, or None
    - "ensemble_statistics": the first EnsembleProcessingItem, or None

    This object is accessed via the :attr:`processing` attribute of a field.
    Keys can also be accessed via the field's :meth:`get` method using the
    ``"processing."`` prefix.

    Examples
    --------
    >>> import earthkit.data as ekd
    >>> field = ekd.from_source("file", "example.grib2").to_fieldlist()[0]
    >>> field.processing.time_processing()
    TimeProcessingItem(method='maximum', window_length=Duration(hours=6))
    >>> field.processing.get("time_processing")
    TimeProcessingItem(method='maximum', window_length=Duration(hours=6))
    """

    @abstractmethod
    def items(self) -> List[ProcessingItem]:
        """Return the list of processing items."""
        pass

    @mark_get_key
    @abstractmethod
    def time_processing(self) -> Optional[TimeProcessingItem]:
        r"""Return the first time processing item.

        Returns
        -------
        TimeProcessingItem or None
            The first time processing item, or None if not available.
        """
        pass

    @mark_get_key
    @abstractmethod
    def ensemble_statistics(self) -> Optional[EnsembleProcessingItem]:
        r"""Return the first ensemble statistics item.

        Returns
        -------
        EnsembleProcessingItem or None
            The first ensemble statistics item, or None if not available.
        """
        pass


class EmptyProcessing(ProcessingBase):
    """An empty processing component representing no processing information."""

    def items(self) -> List[ProcessingItem]:
        return []

    def time_processing(self) -> None:
        return None

    def ensemble_statistics(self) -> None:
        return None

    @classmethod
    def from_dict(cls, d: dict):
        return cls()

    def to_dict(self) -> dict:
        return dict()

    def set(self, *args, **kwargs):
        raise ValueError("Cannot set values on EmptyProcessing")

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        pass


class Processing(ProcessingBase):
    """A processing component containing a list of processing items.

    Parameters
    ----------
    items : list of ProcessingItem
        The processing items describing operations applied to the field.
    """

    def __init__(self, items: List[ProcessingItem]) -> None:
        self._items = items

    def items(self) -> List[ProcessingItem]:
        return self._items

    @mark_get_key
    def time_processing(self) -> Optional[TimeProcessingItem]:
        r"""Return the first time processing item."""
        for item in self._items:
            if isinstance(item, TimeProcessingItem):
                return item
        return None

    @mark_get_key
    def ensemble_statistics(self) -> Optional[EnsembleProcessingItem]:
        r"""Return the first ensemble statistics item."""
        for item in self._items:
            if isinstance(item, EnsembleProcessingItem):
                return item
        return None

    @classmethod
    def from_dict(cls, d: dict) -> "Processing":
        """Create a Processing component from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary with an ``"items"`` key containing a list of item dicts.

        Returns
        -------
        Processing
        """
        items = [ProcessingItem.from_dict(item) for item in d["items"]]
        return cls(items)

    def to_dict(self) -> dict:
        return {"items": [item.to_dict() for item in self._items]}

    def set(self, *args, **kwargs):
        """Set new values for the processing component and return a new instance.

        Not yet implemented.
        """
        raise NotImplementedError("Setting values on Processing is not yet implemented")

    def __getstate__(self):
        return {"items": [item.to_dict() for item in self._items]}

    def __setstate__(self, state):
        items_data = state.get("items", [])
        self._items = [ProcessingItem.from_dict(item) for item in items_data]
