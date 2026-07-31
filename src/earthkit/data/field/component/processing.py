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

The processing component uses a **tuple-based** data model:

- :class:`Processing` holds an immutable tuple of :class:`ProcessingItemBase` nodes.
- :class:`ProcessingItemBase` is an abstract base declaring the full accessor interface.
- :class:`ProcessingItem` implements the logic shared by the concrete subclasses
  :class:`TimeProcessingItem` and :class:`EnsembleProcessingItem`.
- :class:`EmptyProcessingItem` is a terminal singleton that is returned when
  accessing out-of-range indices.

The :class:`Processing` class exposes a partial tuple interface
(``__getitem__``, ``__iter__``, ``__len__``, ``__add__``, ``__eq__``)
and propagates item-level accessors (e.g. ``.kind()``, ``.method()``) as
tuples of values across all items.
"""

from abc import abstractmethod
from enum import Enum
from typing import Optional, Tuple

from .component import SimpleFieldComponent, component_keys, mark_get_key
from .duration import Duration, to_duration

# ===========================================================================
# Enums
# ===========================================================================


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

    - ``FORECAST_REFERENCE_TIME``: successive samples share the same forecast
      period but have different base datetimes (GRIB ``typeOfTimeInterval=1``).
    - ``FORECAST_PERIOD``: successive samples share the same base datetime but
      have different forecast periods (GRIB ``typeOfTimeInterval=2``).
    """

    FORECAST_REFERENCE_TIME = "forecast_reference_time"
    FORECAST_PERIOD = "forecast_period"


# ===========================================================================
# Enum conversion helpers
# ===========================================================================


def get_processing_kind(value) -> ProcessingKind:
    """Convert a value to a ProcessingKind enum member."""
    if isinstance(value, ProcessingKind):
        return value
    if isinstance(value, str):
        try:
            return ProcessingKind(value)
        except ValueError:
            try:
                return ProcessingKind[value.upper()]
            except KeyError:
                pass
    raise ValueError(f"Unknown processing kind: {value!r}")


def get_processing_method(value) -> ProcessingMethod:
    """Convert a value to a ProcessingMethod enum member."""
    if isinstance(value, ProcessingMethod):
        return value
    if isinstance(value, str):
        try:
            return ProcessingMethod(value)
        except ValueError:
            try:
                return ProcessingMethod[value.upper()]
            except KeyError:
                pass
    raise ValueError(f"Unknown processing method: {value!r}")


def get_incrementing_type(value) -> Optional[IncrementingType]:
    """Convert a value to an IncrementingType enum member (None passthrough)."""
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


# ===========================================================================
# ProcessingItemBase — abstract base
# ===========================================================================


@component_keys
class ProcessingItemBase(SimpleFieldComponent):
    """Abstract base class for a single processing item.

    This class defines the interface for a processing item. Some of the accessors are
    not applicable to all processing item types (e.g. :meth:`ensemble_size` only applies
    to :class:`EnsembleProcessingItem`), and return None when not applicable.

    The processing information can be accessed by methods like :meth:`kind`,
    :meth:`method`, :meth:`window_length`, :meth:`sampling_frequency`,
    :meth:`incrementing`, and :meth:`ensemble_size`. Each of these methods has an
    associated key that can be used in the :meth:`get` method to retrieve the
    corresponding information. The list of supported keys is as follows:

    - "kind": the :class:`ProcessingKind` of this item
    - "method": the :class:`ProcessingMethod` used
    - "window_length": the :class:`Duration` of the time window, or None
    - "sampling_frequency": the sampling frequency within the window as a :class:`Duration`, or None
    - "incrementing": the :class:`IncrementingType` (which time coordinate is incremented), or None
    - "ensemble_size": the number of ensemble members as an int, or None

    Subclasses: :class:`EmptyProcessingItem`, :class:`ProcessingItem` (and, in turn,
    :class:`TimeProcessingItem` and :class:`EnsembleProcessingItem`).
    """

    @mark_get_key
    @abstractmethod
    def kind(self) -> Optional[ProcessingKind]:
        """Return the kind of this processing item.

        The kind is a :class:`ProcessingKind` enum member identifying the family of
        processing (e.g. time processing or ensemble statistics).
        """
        pass

    @mark_get_key
    @abstractmethod
    def method(self) -> Optional[ProcessingMethod]:
        """Return the statistical method.

        The method is a :class:`ProcessingMethod` enum member describing the statistical
        operation applied (e.g. mean, maximum, standard deviation).
        """
        pass

    @mark_get_key
    @abstractmethod
    def window_length(self) -> Optional[Duration]:
        """Return the length of the time window as a :class:`Duration`.

        Only applicable to time-processing items; returns None otherwise.
        """
        pass

    @mark_get_key
    @abstractmethod
    def sampling_frequency(self) -> Optional[Duration]:
        """Return the sampling frequency within the window as a :class:`Duration`.

        Only applicable to time-processing items; returns None otherwise.
        """
        pass

    @mark_get_key
    @abstractmethod
    def incrementing(self) -> Optional[IncrementingType]:
        """Return which time coordinate is incremented as an :class:`IncrementingType`.

        Only applicable to time-processing items; returns None otherwise.
        """
        pass

    @mark_get_key
    @abstractmethod
    def ensemble_size(self) -> Optional[int]:
        """Return the number of ensemble members.

        Only applicable to ensemble-statistics items; returns None otherwise.
        """
        pass

    @abstractmethod
    def _own_to_dict(self) -> dict:
        """Serialize this item to a dictionary."""
        pass

    def to_dict(self) -> dict:
        """Serialize this item to a dictionary."""
        return self._own_to_dict()

    @abstractmethod
    def __eq__(self, other) -> bool:
        pass

    def __hash__(self):
        return hash(id(self))

    def __contains__(self, name):
        return name in self._KEYS

    def keys(self):
        return self._KEYS

    def aliases(self):
        return self._ALIASES

    def _get_single(self, key, default=None, astype=None, raise_on_missing=False):
        if key in self._KEYS:
            v = getattr(self, key)()
            if astype and v is not None and callable(astype):
                try:
                    return astype(v)
                except Exception:
                    return default
            return v
        if raise_on_missing:
            raise KeyError(f"Key {key!r} not found on {type(self).__name__}")
        return default

    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        return self._get_single(key, default=default, astype=astype, raise_on_missing=raise_on_missing)

    def set(self, *args, **kwargs):
        """Return a new item with updated attributes."""
        updates = {}
        for a in args:
            if a is None:
                continue
            if isinstance(a, dict):
                updates.update(a)
            else:
                raise ValueError(f"Cannot use arg={a}. Only dict allowed.")
        updates.update(kwargs)
        if not updates:
            return self
        d = self._own_to_dict()
        d.update(updates)
        return item_from_dict(d)

    @classmethod
    def from_dict(cls, d: dict) -> "ProcessingItemBase":
        """Dispatch to the appropriate subclass based on 'kind'."""
        return item_from_dict(d)

    def __getstate__(self):
        return self._own_to_dict()

    def __setstate__(self, state):
        rebuilt = item_from_dict(state)
        self.__dict__.update(rebuilt.__dict__)


# ===========================================================================
# EmptyProcessingItem — terminal / out-of-range sentinel
# ===========================================================================


class EmptyProcessingItem(ProcessingItemBase):
    """A terminal processing item returned for out-of-range access.

    All attribute accessors return None.  ``get()`` respects
    ``raise_on_missing``.
    """

    def kind(self) -> None:
        """Return the kind of this processing item.

        An EmptyProcessingItem does not contain any processing information, and this
        method returns None.
        """
        return None

    def method(self) -> None:
        """Return the statistical method.

        An EmptyProcessingItem does not contain any processing information, and this
        method returns None.
        """
        return None

    def window_length(self) -> None:
        """Return the length of the time window.

        An EmptyProcessingItem does not contain any processing information, and this
        method returns None.
        """
        return None

    def sampling_frequency(self) -> None:
        """Return the sampling frequency within the window.

        An EmptyProcessingItem does not contain any processing information, and this
        method returns None.
        """
        return None

    def incrementing(self) -> None:
        """Return which time coordinate is incremented.

        An EmptyProcessingItem does not contain any processing information, and this
        method returns None.
        """
        return None

    def ensemble_size(self) -> None:
        """Return the number of ensemble members.

        An EmptyProcessingItem does not contain any processing information, and this
        method returns None.
        """
        return None

    def _own_to_dict(self) -> dict:
        return {}

    def to_dict(self) -> dict:
        return {}

    def _get_single(self, key, default=None, astype=None, raise_on_missing=False):
        if raise_on_missing:
            raise KeyError(f"Key {key!r} not found: empty processing item (out of range)")
        return default

    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        return self._get_single(key, default=default, astype=astype, raise_on_missing=raise_on_missing)

    def set(self, *args, **kwargs):
        raise ValueError("Cannot set values on EmptyProcessingItem")

    def __eq__(self, other):
        return isinstance(other, EmptyProcessingItem)

    def __repr__(self):
        return "EmptyProcessingItem()"

    @classmethod
    def from_dict(cls, d: dict):
        return _EMPTY_PROCESSING_ITEM

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        pass


_EMPTY_PROCESSING_ITEM = EmptyProcessingItem()


# ===========================================================================
# ProcessingItem — common base for non-empty items
# ===========================================================================


class ProcessingItem(ProcessingItemBase):
    """Common base for concrete (non-empty) processing items.

    Implements the logic shared by :class:`TimeProcessingItem` and
    :class:`EnsembleProcessingItem`: the :meth:`kind` and :meth:`method` accessors
    (backed by ``self._kind`` and ``self._method``), and default None implementations
    for the type-specific accessors, which the relevant subclass overrides.
    """

    def kind(self) -> ProcessingKind:
        return self._kind

    def method(self) -> ProcessingMethod:
        return self._method

    def window_length(self) -> None:
        """Return the length of the time window.

        This processing item does not have a time window, and this method returns None.
        """
        return None

    def sampling_frequency(self) -> None:
        """Return the sampling frequency within the window.

        This processing item does not have a sampling frequency, and this method returns None.
        """
        return None

    def incrementing(self) -> None:
        """Return which time coordinate is incremented.

        This processing item does not have an incrementing type, and this method returns None.
        """
        return None

    def ensemble_size(self) -> None:
        """Return the number of ensemble members.

        This processing item does not have an ensemble size, and this method returns None.
        """
        return None


# ===========================================================================
# TimeProcessingItem
# ===========================================================================


class TimeProcessingItem(ProcessingItem):
    """A time-based processing item.

    Parameters
    ----------
    method : ProcessingMethod or str
        The statistical method (e.g. ``"maximum"``, ``"mean"``).
    window_length : Duration, datetime.timedelta, str, or None
        The length of the time window (ISO 8601 duration string accepted).
    sampling_frequency : Duration, datetime.timedelta, str, or None
        The sampling frequency within the window.
    incrementing : IncrementingType, str, or None
        Which time coordinate is incremented. Default ``"forecast_period"``.
    """

    DEFAULT_INCREMENTING = IncrementingType.FORECAST_PERIOD

    def __init__(
        self,
        method="point",
        window_length=None,
        sampling_frequency=None,
        incrementing=None,
    ) -> None:
        self._kind = ProcessingKind.TIME_PROCESSING
        self._method = get_processing_method(method)
        self._window_length = to_duration(window_length)
        self._sampling_frequency = to_duration(sampling_frequency)
        self._incrementing = get_incrementing_type(
            incrementing if incrementing is not None else self.DEFAULT_INCREMENTING
        )

    def window_length(self) -> Optional[Duration]:
        return self._window_length

    def sampling_frequency(self) -> Optional[Duration]:
        return self._sampling_frequency

    def incrementing(self) -> Optional[IncrementingType]:
        return self._incrementing

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
    def _from_dict(cls, d: dict) -> "TimeProcessingItem":
        return cls(
            method=d.get("method", "point"),
            window_length=d.get("window_length"),
            sampling_frequency=d.get("sampling_frequency"),
            incrementing=d.get("incrementing"),
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, TimeProcessingItem):
            return NotImplemented
        return (
            self._method == other._method
            and self._window_length == other._window_length
            and self._sampling_frequency == other._sampling_frequency
            and self._incrementing == other._incrementing
        )

    def __repr__(self) -> str:
        parts = [f"method={self._method.value!r}"]
        if self._window_length is not None:
            parts.append(f"window_length={self._window_length!r}")
        if self._sampling_frequency is not None:
            parts.append(f"sampling_frequency={self._sampling_frequency!r}")
        if self._incrementing is not None and self._incrementing != self.DEFAULT_INCREMENTING:
            parts.append(f"incrementing={self._incrementing.value!r}")
        return f"TimeProcessingItem({', '.join(parts)})"


# ===========================================================================
# EnsembleProcessingItem
# ===========================================================================


class EnsembleProcessingItem(ProcessingItem):
    """An ensemble statistics processing item.

    Parameters
    ----------
    method : ProcessingMethod or str
        The statistical method (e.g. ``"mean"``, ``"standard_deviation"``).
    ensemble_size : int
        The number of ensemble members.
    """

    def __init__(
        self,
        method="mean",
        ensemble_size: int = 0,
    ) -> None:
        self._kind = ProcessingKind.ENSEMBLE_STATISTICS
        self._method = get_processing_method(method)
        self._ensemble_size = int(ensemble_size)

    def ensemble_size(self) -> int:
        return self._ensemble_size

    def _own_to_dict(self) -> dict:
        return {
            "kind": self._kind.value,
            "method": self._method.value,
            "ensemble_size": self._ensemble_size,
        }

    @classmethod
    def _from_dict(cls, d: dict) -> "EnsembleProcessingItem":
        return cls(
            method=d.get("method", "mean"),
            ensemble_size=d.get("ensemble_size", 0),
        )

    def __eq__(self, other) -> bool:
        if not isinstance(other, EnsembleProcessingItem):
            return NotImplemented
        return self._method == other._method and self._ensemble_size == other._ensemble_size

    def __repr__(self) -> str:
        return f"EnsembleProcessingItem(method={self._method.value!r}, ensemble_size={self._ensemble_size})"


# ===========================================================================
# Item factory
# ===========================================================================


def item_from_dict(d: dict) -> ProcessingItemBase:
    """Create a ProcessingItemBase from a dictionary, dispatching by 'kind'.

    Parameters
    ----------
    d : dict
        Must contain at least ``"kind"`` and ``"method"``.

    Returns
    -------
    TimeProcessingItem or EnsembleProcessingItem
    """
    if not d:
        return _EMPTY_PROCESSING_ITEM
    kind = get_processing_kind(d["kind"])
    if kind == ProcessingKind.TIME_PROCESSING:
        return TimeProcessingItem._from_dict(d)
    elif kind == ProcessingKind.ENSEMBLE_STATISTICS:
        return EnsembleProcessingItem._from_dict(d)
    else:
        raise ValueError(f"Unknown processing kind: {kind}")


# ===========================================================================
# Processing — the field component (tuple of ProcessingItems)
# ===========================================================================


import re  # noqa: E402

_INDEX_RE = re.compile(r"^\[(\d+)\](?:\.(.+))?$")


@component_keys
class Processing(SimpleFieldComponent):
    """The processing component of a field.

    Contains an immutable tuple of :class:`ProcessingItemBase` instances describing
    the processing chain applied to the field (outermost first).

    Implements a partial tuple interface and propagates item-level accessors
    as tuples.

    Parameters
    ----------
    items : tuple or list of ProcessingItemBase
        The processing items (outermost operation first).

    Examples
    --------
    >>> f.processing[0].kind()
    <ProcessingKind.TIME_PROCESSING: 'time_processing'>
    >>> f.processing.kind()
    (<ProcessingKind.TIME_PROCESSING: ...>, ...)
    >>> len(f.processing)
    2
    """

    def __init__(self, items: "Tuple[ProcessingItemBase, ...] | list" = ()) -> None:
        if isinstance(items, list):
            items = tuple(items)
        self._items = items

    # -------------------------------------------------------------------
    # Tuple-like interface
    # -------------------------------------------------------------------

    def __getitem__(self, index) -> ProcessingItemBase:
        """Return the item at ``index``, or :class:`EmptyProcessingItem` if out of range."""
        if isinstance(index, int):
            if 0 <= index < len(self._items):
                return self._items[index]
            # Negative indexing
            if -len(self._items) <= index < 0:
                return self._items[index]
            return _EMPTY_PROCESSING_ITEM
        elif isinstance(index, slice):
            return Processing(self._items[index])
        raise TypeError(f"indices must be integers or slices, not {type(index).__name__}")

    def __iter__(self):
        """Iterate over processing items."""
        return iter(self._items)

    def __len__(self) -> int:
        """Return the number of processing items."""
        return len(self._items)

    def __add__(self, other) -> "Processing":
        """Concatenate two Processing objects."""
        if isinstance(other, Processing):
            return Processing(self._items + other._items)
        if isinstance(other, (tuple, list)):
            return Processing(self._items + tuple(other))
        return NotImplemented

    def __eq__(self, other) -> bool:
        """Compare processing items one-by-one."""
        if isinstance(other, Processing):
            return self._items == other._items
        if isinstance(other, tuple):
            return self._items == other
        return NotImplemented

    def __hash__(self):
        return hash(self._items)

    def __repr__(self) -> str:
        return f"Processing({list(self._items)!r})"

    # -------------------------------------------------------------------
    # Propagated accessors (return tuples)
    # -------------------------------------------------------------------

    def kind(self) -> Tuple[Optional[ProcessingKind], ...]:
        """Return a tuple of kinds for all items."""
        return tuple(item.kind() for item in self._items)

    def method(self) -> Tuple[Optional[ProcessingMethod], ...]:
        """Return a tuple of methods for all items."""
        return tuple(item.method() for item in self._items)

    def window_length(self) -> Tuple[Optional[Duration], ...]:
        """Return a tuple of window lengths (None if not applicable)."""
        return tuple(item.window_length() for item in self._items)

    def sampling_frequency(self) -> Tuple[Optional[Duration], ...]:
        """Return a tuple of sampling frequencies (None if not applicable)."""
        return tuple(item.sampling_frequency() for item in self._items)

    def incrementing(self) -> Tuple[Optional[IncrementingType], ...]:
        """Return a tuple of incrementing types (None if not applicable)."""
        return tuple(item.incrementing() for item in self._items)

    def ensemble_size(self) -> Tuple[Optional[int], ...]:
        """Return a tuple of ensemble sizes (None if not applicable)."""
        return tuple(item.ensemble_size() for item in self._items)

    # -------------------------------------------------------------------
    # SimpleFieldComponent interface
    # -------------------------------------------------------------------

    def __contains__(self, name):
        """Check if the key is supported.

        Supports both plain keys (e.g. "kind") and indexed keys (e.g. "[0].kind").
        """
        if name in self._KEYS:
            return True
        # Check for indexed access pattern [i].key
        m = _INDEX_RE.match(name)
        if m:
            return True
        return False

    def _get_single(self, key, default=None, astype=None, raise_on_missing=False):
        """Get a value, supporting indexed access like ``[0].kind``."""
        # Check for indexed access: "[i].key" or "[i]"
        m = _INDEX_RE.match(key)
        if m:
            idx = int(m.group(1))
            sub_key = m.group(2)
            item = self[idx]
            if sub_key:
                return item.get(sub_key, default=default, astype=astype, raise_on_missing=raise_on_missing)
            else:
                # "[i]" alone — return the item's dict
                if isinstance(item, EmptyProcessingItem):
                    if raise_on_missing:
                        raise KeyError(f"Processing item at index {idx} does not exist")
                    return default
                return item.to_dict()

        # Plain key — propagated accessor (returns tuple)
        return super()._get_single(key, default=default, astype=astype, raise_on_missing=raise_on_missing)

    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        """Return the value for the specified key.

        Supports:
        - ``"kind"``, ``"method"``, etc. → tuple of values across all items
        - ``"[i].kind"`` → value from the i-th item
        - ``"[i]"`` → dict of the i-th item
        """
        return self._get_single(key, default=default, astype=astype, raise_on_missing=raise_on_missing)

    def set(self, *args, **kwargs) -> "Processing":
        """Return a new Processing with updated items.

        Accepts:
        - Indexed keys: ``{"[0].method": "mean"}`` → update item at index 0
        - Indexed item replacement: ``{"[0]": {...}}`` → replace item at index 0
        - Full replacement: a list/tuple of dicts passed directly

        Parameters
        ----------
        *args : dict
            Dictionaries of key-value pairs.
        **kwargs
            Key-value pairs.

        Returns
        -------
        Processing
        """
        updates = {}
        for a in args:
            if a is None:
                continue
            if isinstance(a, dict):
                updates.update(a)
            elif isinstance(a, (list, tuple)):
                # Full replacement from a list of dicts
                return Processing(tuple(item_from_dict(d) for d in a))
            else:
                raise ValueError(f"Cannot use arg={a}. Only dict or list allowed.")
        updates.update(kwargs)

        if not updates:
            return self

        # Group updates by index
        items_list = list(self._items)
        indexed_updates = {}  # idx -> dict of sub_key -> value
        item_replacements = {}  # idx -> full dict

        for key, value in updates.items():
            m = _INDEX_RE.match(key)
            if m:
                idx = int(m.group(1))
                sub_key = m.group(2)
                if sub_key:
                    indexed_updates.setdefault(idx, {})[sub_key] = value
                else:
                    # "[i]" = full item replacement
                    if isinstance(value, dict):
                        item_replacements[idx] = value
                    elif isinstance(value, ProcessingItemBase):
                        item_replacements[idx] = value._own_to_dict()
                    else:
                        raise ValueError(f"Value for '{key}' must be a dict or ProcessingItemBase")
            else:
                raise KeyError(f"Key {key!r} not supported in Processing.set(). Use indexed keys like '[0].method'.")

        # Apply item replacements
        for idx, d in item_replacements.items():
            while len(items_list) <= idx:
                items_list.append(_EMPTY_PROCESSING_ITEM)
            items_list[idx] = item_from_dict(d)

        # Apply indexed updates (modify existing items)
        for idx, sub_updates in indexed_updates.items():
            if idx < len(items_list) and not isinstance(items_list[idx], EmptyProcessingItem):
                items_list[idx] = items_list[idx].set(sub_updates)
            else:
                raise KeyError(f"Cannot update item at index {idx}: out of range")

        return Processing(tuple(items_list))

    # -------------------------------------------------------------------
    # Serialization
    # -------------------------------------------------------------------

    def to_dict(self) -> dict:
        """Serialize to a dictionary with an 'items' key.

        Returns
        -------
        dict
            ``{"items": [item0.to_dict(), item1.to_dict(), ...]}``
        """
        return {"items": [item.to_dict() for item in self._items]}

    @classmethod
    def from_dict(cls, d) -> "Processing":
        """Create a Processing from a dictionary or list.

        Parameters
        ----------
        d : dict or list
            If dict, must have an ``"items"`` key with a list of item dicts.
            If list/tuple, each element is an item dict.

        Returns
        -------
        Processing
        """
        if isinstance(d, (list, tuple)):
            items = tuple(item_from_dict(item_d) for item_d in d)
            return cls(items)
        if not d:
            return cls(())
        if "items" in d:
            items = tuple(item_from_dict(item_d) for item_d in d["items"])
            return cls(items)
        # Single item dict (backward compat)
        return cls((item_from_dict(d),))

    def __getstate__(self):
        return {"items": [item.to_dict() for item in self._items]}

    def __setstate__(self, state):
        items_data = state.get("items", [])
        self._items = tuple(item_from_dict(d) for d in items_data)
