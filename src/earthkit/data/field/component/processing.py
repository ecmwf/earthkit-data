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

The processing component follows a linked-list design (Proposition #2):
the component itself acts as the head of a linked list of ProcessingItem nodes.
Each node exposes its attributes directly and links to the next via ``.next()``.
"""

from abc import ABCMeta, abstractmethod
from enum import Enum
from typing import Iterator, Optional

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


class IncrementingType(Enum):
    """Which time coordinate is incremented across successive samples.

    In GRIB, this corresponds to ``typeOfTimeInterval``:

    - ``FORECAST_REFERENCE_TIME``: successive samples share the same forecast
      period (step) but have different base datetimes (``typeOfTimeInterval=1``).
    - ``FORECAST_PERIOD``: successive samples share the same base datetime but
      have different forecast periods / steps (``typeOfTimeInterval=2``).
    """

    FORECAST_REFERENCE_TIME = "forecast_reference_time"
    FORECAST_PERIOD = "forecast_period"


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


def get_incrementing_type(value) -> Optional["IncrementingType"]:
    """Convert a value to an IncrementingType enum member.

    Parameters
    ----------
    value : IncrementingType, str, or None
        The value to convert. If None, returns None.

    Returns
    -------
    IncrementingType or None

    Raises
    ------
    ValueError
        If the value cannot be mapped to an IncrementingType.
    """
    if value is None:
        return None
    if isinstance(value, IncrementingType):
        return value
    if isinstance(value, str):
        try:
            return IncrementingType(value)
        except ValueError:
            try:
                return IncrementingType[value.upper()]
            except KeyError:
                pass
    raise ValueError(f"Unknown incrementing type: {value!r}")


class ProcessingItem(metaclass=ABCMeta):
    """Base class for processing items (linked-list nodes).

    A processing item describes a single processing operation applied to a field.
    Items form a linked list: each item optionally links to the next via
    :meth:`next`.

    Parameters
    ----------
    kind : ProcessingKind
        The kind of processing (time_processing, ensemble_statistics).
    method : ProcessingMethod
        The statistical method used (maximum, minimum, mean, etc.).
    next_item : ProcessingItem or None
        The next processing item in the chain.
    """

    def __init__(
        self,
        kind: ProcessingKind,
        method: ProcessingMethod,
        next_item: Optional["ProcessingItem"] = None,
    ) -> None:
        self._kind = get_processing_kind(kind)
        self._method = get_processing_method(method)
        self._next = next_item

    def kind(self) -> ProcessingKind:
        """Return the kind of this processing item.

        Returns
        -------
        ProcessingKind
        """
        return self._kind

    def method(self) -> ProcessingMethod:
        """Return the statistical method of this processing item.

        Returns
        -------
        ProcessingMethod
        """
        return self._method

    def next(self) -> Optional["ProcessingItem"]:
        """Return the next processing item in the chain.

        Returns
        -------
        ProcessingItem or None
            The next item, or None if this is the last item.
        """
        return self._next

    def __len__(self) -> int:
        """Return the length of the processing chain from this item onwards."""
        count = 1
        node = self._next
        while node is not None:
            count += 1
            node = node._next
        return count

    def __iter__(self) -> Iterator["ProcessingItem"]:
        """Iterate over processing items from this item onwards."""
        node = self
        while node is not None:
            yield node
            node = node._next

    def to_dict(self) -> dict:
        """Serialize the processing item (and its chain) to a nested dictionary.

        The ``"next"`` key contains the nested dict of the following item, if any.

        Returns
        -------
        dict
        """
        d = self._own_to_dict()
        if self._next is not None:
            d["next"] = self._next.to_dict()
        return d

    @abstractmethod
    def _own_to_dict(self) -> dict:
        """Serialize only this item's own attributes (without the 'next' chain)."""
        pass

    @classmethod
    def from_dict(cls, d: dict) -> "ProcessingItem":
        """Create a ProcessingItem chain from a (possibly nested) dictionary.

        Parameters
        ----------
        d : dict
            Dictionary with at least ``kind`` and ``method`` keys. May contain
            a ``"next"`` key with the nested next item's dict.

        Returns
        -------
        ProcessingItem
            The head of the reconstructed chain.
        """
        # Recursively build the next item first
        next_item = None
        if "next" in d:
            next_item = ProcessingItem.from_dict(d["next"])

        kind = get_processing_kind(d["kind"])
        if kind == ProcessingKind.TIME_PROCESSING:
            return TimeProcessingItem._from_dict(d, next_item=next_item)
        elif kind == ProcessingKind.ENSEMBLE_STATISTICS:
            return EnsembleProcessingItem._from_dict(d, next_item=next_item)
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
    incrementing : IncrementingType, str, or None
        Which time coordinate is incremented across successive samples in
        the processing window. ``"forecast_reference_time"`` means successive
        samples have different base datetimes but the same step (GRIB
        ``typeOfTimeInterval=1``). ``"forecast_period"`` means successive
        samples have the same base datetime but different steps (GRIB
        ``typeOfTimeInterval=2``). Default is ``"forecast_period"``.
    next_item : ProcessingItem or None
        The next processing item in the chain.
    """

    DEFAULT_INCREMENTING = IncrementingType.FORECAST_PERIOD

    def __init__(
        self,
        method: ProcessingMethod = ProcessingMethod.POINT,
        window_length: Optional[Duration] = None,
        sampling_frequency: Optional[Duration] = None,
        incrementing: Optional[IncrementingType] = None,
        next_item: Optional[ProcessingItem] = None,
    ) -> None:
        super().__init__(
            kind=ProcessingKind.TIME_PROCESSING,
            method=method,
            next_item=next_item,
        )
        self._window_length = to_duration(window_length)
        self._sampling_frequency = to_duration(sampling_frequency)
        self._incrementing = get_incrementing_type(
            incrementing if incrementing is not None else self.DEFAULT_INCREMENTING
        )

    def window_length(self) -> Optional[Duration]:
        """Return the time window length.

        Returns
        -------
        Duration or None
        """
        return self._window_length

    def sampling_frequency(self) -> Optional[Duration]:
        """Return the sampling frequency.

        Returns
        -------
        Duration or None
        """
        return self._sampling_frequency

    def incrementing(self) -> Optional[IncrementingType]:
        """Return the incrementing type.

        Returns
        -------
        IncrementingType or None
        """
        return self._incrementing

    def __repr__(self) -> str:
        parts = [f"method={self._method.value!r}"]
        if self._window_length is not None:
            parts.append(f"window_length={self._window_length!r}")
        if self._sampling_frequency is not None:
            parts.append(f"sampling_frequency={self._sampling_frequency!r}")
        if self._incrementing is not None and self._incrementing != self.DEFAULT_INCREMENTING:
            parts.append(f"incrementing={self._incrementing.value!r}")
        if self._next is not None:
            parts.append(f"next={self._next!r}")
        return f"TimeProcessingItem({', '.join(parts)})"

    def _own_to_dict(self) -> dict:
        d = {
            "kind": self._kind.value,
            "method": self._method.value,
        }
        if self._window_length is not None:
            d["window_length"] = self._window_length.to_iso_string()
        if self._sampling_frequency is not None:
            d["sampling_frequency"] = self._sampling_frequency.to_iso_string()
        if self._incrementing is not None:
            d["incrementing"] = self._incrementing.value
        return d

    @classmethod
    def _from_dict(cls, d: dict, next_item=None) -> "TimeProcessingItem":
        """Create a TimeProcessingItem from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary with ``method`` and optionally ``window_length``,
            ``sampling_frequency``, ``incrementing``.
        next_item : ProcessingItem or None
            The next item in the chain.

        Returns
        -------
        TimeProcessingItem
        """
        return cls(
            method=d.get("method", "point"),
            window_length=d.get("window_length"),
            sampling_frequency=d.get("sampling_frequency"),
            incrementing=d.get("incrementing"),
            next_item=next_item,
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
    next_item : ProcessingItem or None
        The next processing item in the chain.
    """

    def __init__(
        self,
        method: ProcessingMethod = ProcessingMethod.MEAN,
        ensemble_size: int = 0,
        next_item: Optional[ProcessingItem] = None,
    ) -> None:
        super().__init__(
            kind=ProcessingKind.ENSEMBLE_STATISTICS,
            method=method,
            next_item=next_item,
        )
        self._ensemble_size = int(ensemble_size)

    def ensemble_size(self) -> int:
        """Return the ensemble size.

        Returns
        -------
        int
        """
        return self._ensemble_size

    def __repr__(self) -> str:
        parts = [f"method={self._method.value!r}", f"ensemble_size={self._ensemble_size}"]
        if self._next is not None:
            parts.append(f"next={self._next!r}")
        return f"EnsembleProcessingItem({', '.join(parts)})"

    def _own_to_dict(self) -> dict:
        return {
            "kind": self._kind.value,
            "method": self._method.value,
            "ensemble_size": self._ensemble_size,
        }

    @classmethod
    def _from_dict(cls, d: dict, next_item=None) -> "EnsembleProcessingItem":
        """Create an EnsembleProcessingItem from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary with ``method`` and ``ensemble_size``.
        next_item : ProcessingItem or None
            The next item in the chain.

        Returns
        -------
        EnsembleProcessingItem
        """
        return cls(
            method=d.get("method", "mean"),
            ensemble_size=d.get("ensemble_size", 0),
            next_item=next_item,
        )


@component_keys
class ProcessingBase(SimpleFieldComponent):
    """Base class for the processing component of a field.

    The processing component follows a linked-list design (Proposition #2):
    it acts as the head of a chain of :class:`ProcessingItem` nodes. Attribute
    access on the component (e.g. ``f.processing.kind()``) delegates to the
    head item. The next item in the chain is accessed via ``f.processing.next()``.

    Supported keys for :meth:`get`:

    - ``"kind"``: the kind of the head processing item
    - ``"method"``: the method of the head processing item
    - ``"window_length"``: the window length (TimeProcessingItem only)
    - ``"sampling_frequency"``: the sampling frequency (TimeProcessingItem only)
    - ``"incrementing"``: the incrementing type (TimeProcessingItem only)
    - ``"ensemble_size"``: the ensemble size (EnsembleProcessingItem only)
    - ``"len"``: the length of the processing chain
    - ``"next.kind"``, ``"next.method"``, etc.: attributes of the next item

    This object is accessed via the :attr:`processing` attribute of a field.
    Keys can also be accessed via the field's :meth:`get` method using the
    ``"processing."`` prefix (e.g. ``f.get("processing.kind")``).

    Examples
    --------
    >>> f.processing.kind()
    <ProcessingKind.TIME_PROCESSING: 'time_processing'>
    >>> f.processing.method()
    <ProcessingMethod.MEAN: 'mean'>
    >>> f.processing.window_length()
    Duration(...)
    >>> f.processing.next().kind()
    <ProcessingKind.TIME_PROCESSING: 'time_processing'>
    >>> f.processing.next().method()
    <ProcessingMethod.MAXIMUM: 'maximum'>
    >>> len(f.processing)
    2
    >>> f.processing.to_dict()
    {'kind': 'time_processing', 'method': 'mean', 'window_length': 'P1M', ...}
    """

    @abstractmethod
    def _head(self) -> Optional[ProcessingItem]:
        """Return the head processing item, or None if empty."""
        pass

    @mark_get_key
    def kind(self) -> Optional[ProcessingKind]:
        """Return the kind of the head processing item.

        Returns
        -------
        ProcessingKind or None
        """
        head = self._head()
        return head.kind() if head is not None else None

    @mark_get_key
    def method(self) -> Optional[ProcessingMethod]:
        """Return the method of the head processing item.

        Returns
        -------
        ProcessingMethod or None
        """
        head = self._head()
        return head.method() if head is not None else None

    @mark_get_key
    def window_length(self) -> Optional[Duration]:
        """Return the window length of the head processing item.

        Returns
        -------
        Duration or None
            The window length, or None if not applicable or empty.
        """
        head = self._head()
        if head is not None and hasattr(head, "window_length"):
            return head.window_length()
        return None

    @mark_get_key
    def sampling_frequency(self) -> Optional[Duration]:
        """Return the sampling frequency of the head processing item.

        Returns
        -------
        Duration or None
            The sampling frequency, or None if not applicable or empty.
        """
        head = self._head()
        if head is not None and hasattr(head, "sampling_frequency"):
            return head.sampling_frequency()
        return None

    @mark_get_key
    def incrementing(self) -> Optional[IncrementingType]:
        """Return the incrementing type of the head processing item.

        Returns
        -------
        IncrementingType or None
            The incrementing type, or None if not applicable or empty.
        """
        head = self._head()
        if head is not None and hasattr(head, "incrementing"):
            return head.incrementing()
        return None

    @mark_get_key
    def ensemble_size(self) -> Optional[int]:
        """Return the ensemble size of the head processing item.

        Returns
        -------
        int or None
            The ensemble size, or None if not applicable or empty.
        """
        head = self._head()
        if head is not None and hasattr(head, "ensemble_size"):
            return head.ensemble_size()
        return None

    def next(self) -> Optional[ProcessingItem]:
        """Return the next processing item after the head.

        Returns
        -------
        ProcessingItem or None
        """
        head = self._head()
        return head.next() if head is not None else None

    def __len__(self) -> int:
        """Return the length of the processing chain."""
        head = self._head()
        return len(head) if head is not None else 0

    def __iter__(self) -> Iterator[ProcessingItem]:
        """Iterate over all processing items in the chain."""
        head = self._head()
        if head is not None:
            yield from head
        return

    def _get_single(self, key, default=None, astype=None, raise_on_missing=False):
        """Extended get supporting dotted 'next.' prefix navigation."""
        # Handle "len" specially
        if key == "len":
            return len(self)

        # Handle "next.X" keys by navigating the chain
        if key.startswith("next."):
            remainder = key[len("next.") :]
            next_item = self.next()
            if next_item is None:
                if raise_on_missing:
                    raise KeyError(f"Key {key} not found: no next processing item")
                return default
            return _get_from_item(next_item, remainder, default=default, raise_on_missing=raise_on_missing)

        # Fall back to standard SimpleFieldComponent behaviour
        return super()._get_single(key, default=default, astype=astype, raise_on_missing=raise_on_missing)


def _get_from_item(item: ProcessingItem, key: str, default=None, raise_on_missing=False):
    """Retrieve a value from a ProcessingItem by key, supporting 'next.' navigation."""
    if key == "len":
        return len(item)

    if key.startswith("next."):
        remainder = key[len("next.") :]
        next_item = item.next()
        if next_item is None:
            if raise_on_missing:
                raise KeyError(f"Key {key} not found: no next processing item")
            return default
        return _get_from_item(next_item, remainder, default=default, raise_on_missing=raise_on_missing)

    # Direct attribute access
    if hasattr(item, key) and callable(getattr(item, key)):
        return getattr(item, key)()

    if raise_on_missing:
        raise KeyError(f"Key {key!r} not found on {type(item).__name__}")
    return default


class EmptyProcessing(ProcessingBase):
    """An empty processing component representing no processing information."""

    def _head(self) -> None:
        return None

    @classmethod
    def from_dict(cls, d: dict):
        return cls()

    def to_dict(self) -> dict:
        return {}

    def set(self, *args, **kwargs):
        raise ValueError("Cannot set values on EmptyProcessing")

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        pass


class Processing(ProcessingBase):
    """A processing component containing a linked list of processing items.

    This is the concrete implementation of Proposition #2: the processing
    component holds the head of a linked list of :class:`ProcessingItem` nodes.

    Parameters
    ----------
    head : ProcessingItem
        The head (first) processing item in the chain.
    """

    def __init__(self, head: ProcessingItem) -> None:
        self._item = head

    def _head(self) -> ProcessingItem:
        return self._item

    def to_dict(self) -> dict:
        """Serialize the processing chain to a nested dictionary.

        Returns
        -------
        dict
            A nested dictionary where the ``"next"`` key links to the next
            item's dict representation.

        Examples
        --------
        >>> proc.to_dict()
        {
            "kind": "time_processing",
            "method": "mean",
            "window_length": "P1M",
            "sampling_frequency": "P1D",
            "next": {
                "kind": "time_processing",
                "method": "maximum",
                "window_length": "P1D",
                "sampling_frequency": "PT1H"
            }
        }
        """
        return self._item.to_dict()

    @classmethod
    def from_dict(cls, d: dict) -> "Processing":
        """Create a Processing component from a (possibly nested) dictionary.

        Parameters
        ----------
        d : dict
            Dictionary representing the head item, possibly with a ``"next"``
            key for subsequent items.

        Returns
        -------
        Processing
        """
        if not d:
            return EmptyProcessing()
        head = ProcessingItem.from_dict(d)
        return cls(head)

    def set(self, *args, **kwargs):
        """Set new values for the processing component and return a new instance.

        Not yet implemented.
        """
        raise NotImplementedError("Setting values on Processing is not yet implemented")

    def __getstate__(self):
        return self._item.to_dict()

    def __setstate__(self, state):
        if state:
            self._item = ProcessingItem.from_dict(state)
        else:
            self._item = None
