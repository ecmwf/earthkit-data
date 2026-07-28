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

The processing component is a recursive linked-list structure: each node is
both a field component (with ``get``/``set``/``push``/``pop``) and a linked-list
node (with ``next()``).  Concrete subclasses are :class:`TimeProcessing` and
:class:`EnsembleProcessing`.  :class:`EmptyProcessing` represents the absence
of processing information.
"""

from abc import abstractmethod
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


# ---------------------------------------------------------------------------
# Enum conversion helpers
# ---------------------------------------------------------------------------


def get_processing_kind(value) -> ProcessingKind:
    """Convert a value to a ProcessingKind enum member.

    Parameters
    ----------
    value : ProcessingKind, str, or None
        The value to convert.

    Returns
    -------
    ProcessingKind

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


# ---------------------------------------------------------------------------
# Helper: apply dotted-key updates to a nested processing dict
# ---------------------------------------------------------------------------


def _apply_updates(d, updates):
    """Apply dotted-key updates to a nested processing dict in place.

    Keys without a ``"next."`` prefix update the current dict directly.
    Keys starting with ``"next."`` recurse into ``d["next"]``.
    """
    nested = {}
    for key, value in updates.items():
        if key.startswith("next."):
            nested[key[len("next.") :]] = value
        else:
            if isinstance(value, ProcessingKind):
                value = value.value
            elif isinstance(value, ProcessingMethod):
                value = value.value
            elif isinstance(value, IncrementingType):
                value = value.value
            elif isinstance(value, Duration):
                value = value.to_iso_string()
            d[key] = value

    if nested:
        if "next" not in d:
            d["next"] = {}
        _apply_updates(d["next"], nested)


# ---------------------------------------------------------------------------
# Helper: retrieve a value from a ProcessingBase node by dotted key
# ---------------------------------------------------------------------------


def _get_from_node(node, key, default=None, raise_on_missing=False):
    """Retrieve a value from a ProcessingBase node by key, supporting 'next.' navigation."""
    if key == "len":
        return len(node)

    if key.startswith("next."):
        remainder = key[len("next.") :]
        next_node = node.next()
        if next_node is None:
            if raise_on_missing:
                raise KeyError(f"Key {key} not found: no next processing item")
            return default
        return _get_from_node(next_node, remainder, default=default, raise_on_missing=raise_on_missing)

    if hasattr(node, key) and callable(getattr(node, key)):
        return getattr(node, key)()

    if raise_on_missing:
        raise KeyError(f"Key {key!r} not found on {type(node).__name__}")
    return default


# ---------------------------------------------------------------------------
# ProcessingBase — abstract base for the recursive processing chain
# ---------------------------------------------------------------------------


@component_keys
class ProcessingBase(SimpleFieldComponent):
    """Abstract base for processing components.

    Each concrete subclass (:class:`TimeProcessing`, :class:`EnsembleProcessing`)
    is simultaneously a field component (with ``get``/``set``/``push``/``pop``)
    and a linked-list node (with :meth:`next`).

    :class:`EmptyProcessing` represents the absence of any processing.

    Concrete subclasses store their ``_next`` pointer and inherit the linked-list
    traversal logic (``next``, ``__len__``, ``__iter__``, ``__next__``,
    ``to_dict``, ``push``, ``pop``) from this base class.

    Supported ``get`` keys:

    - ``"kind"``, ``"method"``
    - ``"window_length"``, ``"sampling_frequency"``, ``"incrementing"`` (time only)
    - ``"ensemble_size"`` (ensemble only)
    - ``"len"``
    - ``"next.kind"``, ``"next.method"``, … (chained navigation)
    """

    # Subclasses that represent actual processing nodes set this to their
    # next node (or None).  EmptyProcessing leaves it as None and overrides
    # the relevant methods.
    _next: Optional["ProcessingBase"] = None

    # -----------------------------------------------------------------------
    # Attribute accessors (defaults return None; overridden by subclasses)
    # -----------------------------------------------------------------------

    @mark_get_key
    def kind(self) -> Optional[ProcessingKind]:
        """Return the kind of this processing node."""
        return None

    @mark_get_key
    def method(self) -> Optional[ProcessingMethod]:
        """Return the statistical method of this processing node."""
        return None

    @mark_get_key
    def window_length(self) -> Optional[Duration]:
        """Return the window length (TimeProcessing only)."""
        return None

    @mark_get_key
    def sampling_frequency(self) -> Optional[Duration]:
        """Return the sampling frequency (TimeProcessing only)."""
        return None

    @mark_get_key
    def incrementing(self) -> Optional[IncrementingType]:
        """Return the incrementing type (TimeProcessing only)."""
        return None

    @mark_get_key
    def ensemble_size(self) -> Optional[int]:
        """Return the ensemble size (EnsembleProcessing only)."""
        return None

    # -----------------------------------------------------------------------
    # Linked-list traversal
    # -----------------------------------------------------------------------

    def next(self) -> Optional["ProcessingBase"]:
        """Return the next processing node in the chain.

        Returns
        -------
        ProcessingBase or None
        """
        return self._next

    def _has_next(self) -> bool:
        """Return True if there is a meaningful next node."""
        return self._next is not None and not isinstance(self._next, EmptyProcessing)

    def __len__(self) -> int:
        """Return the length of the processing chain from this node onwards."""
        if self.kind() is None:
            # EmptyProcessing
            return 0
        count = 1
        node = self._next
        while node is not None and not isinstance(node, EmptyProcessing):
            count += 1
            node = node._next
        return count

    def __iter__(self) -> Iterator["ProcessingBase"]:
        """Iterate over processing nodes from this node onwards."""
        if self.kind() is None:
            return
        node = self
        while node is not None and not isinstance(node, EmptyProcessing):
            yield node
            node = node._next

    def __next__(self) -> "ProcessingBase":
        """Return the next processing node, or raise StopIteration.

        This allows using ``next(node)`` as an alternative to ``node.next()``,
        raising ``StopIteration`` when the chain is exhausted.

        Returns
        -------
        ProcessingBase

        Raises
        ------
        StopIteration
            If there is no next node.
        """
        nxt = self._next
        if nxt is None or isinstance(nxt, EmptyProcessing):
            raise StopIteration
        return nxt

    # -----------------------------------------------------------------------
    # Serialization
    # -----------------------------------------------------------------------

    @abstractmethod
    def _own_to_dict(self) -> dict:
        """Serialize only this node's own attributes (without ``next``)."""
        pass

    def to_dict(self) -> dict:
        """Serialize the processing chain to a nested dictionary.

        The ``"next"`` key contains the nested dict of the following node.

        Returns
        -------
        dict
        """
        d = self._own_to_dict()
        if self._has_next():
            d["next"] = self._next.to_dict()
        return d

    def __getstate__(self):
        return self.to_dict()

    def __setstate__(self, state):
        if state:
            rebuilt = from_dict(state)
            self.__dict__.update(rebuilt.__dict__)

    # -----------------------------------------------------------------------
    # push / pop
    # -----------------------------------------------------------------------

    def push(self, item_dict: dict) -> "ProcessingBase":
        """Add a new processing node at the head of the chain.

        The new node becomes the outermost (first) operation and the current
        chain becomes its ``next``.

        Parameters
        ----------
        item_dict : dict
            Dictionary specifying the new processing node. Must contain at
            least ``"kind"`` and ``"method"`` keys.

        Returns
        -------
        TimeProcessing or EnsembleProcessing
            A new node with the current chain as its ``next``.

        Examples
        --------
        >>> p2 = p.push({"kind": "ensemble_statistics", "method": "mean", "ensemble_size": 50})
        """
        return _from_dict(item_dict, next_node=self if len(self) > 0 else None)

    def pop(self) -> "ProcessingBase":
        """Remove the head node and return the remainder of the chain.

        Returns
        -------
        ProcessingBase
            The next node, or :class:`EmptyProcessing` if the chain had at
            most one item.

        Examples
        --------
        >>> p2 = p.pop()
        """
        nxt = self._next
        if nxt is None or isinstance(nxt, EmptyProcessing):
            return EmptyProcessing()
        return nxt

    # -----------------------------------------------------------------------
    # get / set
    # -----------------------------------------------------------------------

    def _get_single(self, key, default=None, astype=None, raise_on_missing=False):
        """Extended get supporting dotted 'next.' prefix navigation."""
        if key == "len":
            return len(self)

        if key.startswith("next."):
            remainder = key[len("next.") :]
            next_node = self._next
            if next_node is None or isinstance(next_node, EmptyProcessing):
                if raise_on_missing:
                    raise KeyError(f"Key {key} not found: no next processing node")
                return default
            return _get_from_node(next_node, remainder, default=default, raise_on_missing=raise_on_missing)

        return super()._get_single(key, default=default, astype=astype, raise_on_missing=raise_on_missing)

    def set(self, *args, **kwargs) -> "ProcessingBase":
        """Create a new processing chain with updated values.

        Accepts dictionaries and/or keyword arguments. Keys prefixed with
        ``next.`` navigate to deeper nodes.

        Parameters
        ----------
        *args : dict
            Dictionaries of key-value pairs to set.
        **kwargs
            Key-value pairs to set.

        Returns
        -------
        ProcessingBase
            A new processing chain with the updated values.
        """
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

        d = self.to_dict()
        if not d:
            _apply_updates(d, updates)
            return from_dict(d)

        _apply_updates(d, updates)
        return from_dict(d)


# ---------------------------------------------------------------------------
# EmptyProcessing
# ---------------------------------------------------------------------------


class EmptyProcessing(ProcessingBase):
    """An empty processing component representing no processing information."""

    def _own_to_dict(self) -> dict:
        return {}

    def to_dict(self) -> dict:
        return {}

    @classmethod
    def from_dict(cls, d: dict):
        return cls()

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        pass


# ---------------------------------------------------------------------------
# TimeProcessing
# ---------------------------------------------------------------------------


class TimeProcessing(ProcessingBase):
    """A time-based processing node.

    Describes time-based statistical processing of a field, such as computing
    the maximum over a time window.  Also serves as a linked-list node via
    :meth:`next`.

    Parameters
    ----------
    method : ProcessingMethod or str
        The statistical method (e.g. ``"maximum"``, ``"mean"``).
    window_length : Duration, datetime.timedelta, str, or None
        The length of the time window.  ISO 8601 duration string accepted.
    sampling_frequency : Duration, datetime.timedelta, str, or None
        The sampling frequency within the window.  ISO 8601 duration string accepted.
    incrementing : IncrementingType, str, or None
        Which time coordinate is incremented across successive samples.
        Default is ``"forecast_period"``.
    next_node : ProcessingBase or None
        The next processing node in the chain.
    """

    DEFAULT_INCREMENTING = IncrementingType.FORECAST_PERIOD

    def __init__(
        self,
        method: ProcessingMethod = ProcessingMethod.POINT,
        window_length: Optional[Duration] = None,
        sampling_frequency: Optional[Duration] = None,
        incrementing: Optional[IncrementingType] = None,
        next_node: Optional[ProcessingBase] = None,
    ) -> None:
        self._kind = ProcessingKind.TIME_PROCESSING
        self._method = get_processing_method(method)
        self._window_length = to_duration(window_length)
        self._sampling_frequency = to_duration(sampling_frequency)
        self._incrementing = get_incrementing_type(
            incrementing if incrementing is not None else self.DEFAULT_INCREMENTING
        )
        self._next = next_node

    # -- attribute accessors (override base defaults) ------------------------

    def kind(self) -> ProcessingKind:
        return self._kind

    def method(self) -> ProcessingMethod:
        return self._method

    def window_length(self) -> Optional[Duration]:
        return self._window_length

    def sampling_frequency(self) -> Optional[Duration]:
        return self._sampling_frequency

    def incrementing(self) -> Optional[IncrementingType]:
        return self._incrementing

    # -- repr / serialization ------------------------------------------------

    def __repr__(self) -> str:
        parts = [f"method={self._method.value!r}"]
        if self._window_length is not None:
            parts.append(f"window_length={self._window_length!r}")
        if self._sampling_frequency is not None:
            parts.append(f"sampling_frequency={self._sampling_frequency!r}")
        if self._incrementing is not None and self._incrementing != self.DEFAULT_INCREMENTING:
            parts.append(f"incrementing={self._incrementing.value!r}")
        if self._has_next():
            parts.append(f"next={self._next!r}")
        return f"TimeProcessing({', '.join(parts)})"

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
    def from_dict(cls, d: dict) -> "TimeProcessing":
        """Create a TimeProcessing from a (possibly nested) dictionary."""
        next_node = None
        if "next" in d:
            next_node = from_dict(d["next"])
        return cls._from_dict(d, next_node=next_node)

    @classmethod
    def _from_dict(cls, d: dict, next_node=None) -> "TimeProcessing":
        """Create a TimeProcessing from a dictionary with a given next_node."""
        return cls(
            method=d.get("method", "point"),
            window_length=d.get("window_length"),
            sampling_frequency=d.get("sampling_frequency"),
            incrementing=d.get("incrementing"),
            next_node=next_node,
        )


# ---------------------------------------------------------------------------
# EnsembleProcessing
# ---------------------------------------------------------------------------


class EnsembleProcessing(ProcessingBase):
    """An ensemble statistics processing node.

    Describes statistical processing across ensemble members.  Also serves
    as a linked-list node via :meth:`next`.

    Parameters
    ----------
    method : ProcessingMethod or str
        The statistical method (e.g. ``"mean"``, ``"standard_deviation"``).
    ensemble_size : int
        The number of ensemble members used in the computation.
    next_node : ProcessingBase or None
        The next processing node in the chain.
    """

    def __init__(
        self,
        method: ProcessingMethod = ProcessingMethod.MEAN,
        ensemble_size: int = 0,
        next_node: Optional[ProcessingBase] = None,
    ) -> None:
        self._kind = ProcessingKind.ENSEMBLE_STATISTICS
        self._method = get_processing_method(method)
        self._ensemble_size = int(ensemble_size)
        self._next = next_node

    # -- attribute accessors (override base defaults) ------------------------

    def kind(self) -> ProcessingKind:
        return self._kind

    def method(self) -> ProcessingMethod:
        return self._method

    def ensemble_size(self) -> int:
        return self._ensemble_size

    # -- repr / serialization ------------------------------------------------

    def __repr__(self) -> str:
        parts = [f"method={self._method.value!r}", f"ensemble_size={self._ensemble_size}"]
        if self._has_next():
            parts.append(f"next={self._next!r}")
        return f"EnsembleProcessing({', '.join(parts)})"

    def _own_to_dict(self) -> dict:
        return {
            "kind": self._kind.value,
            "method": self._method.value,
            "ensemble_size": self._ensemble_size,
        }

    @classmethod
    def from_dict(cls, d: dict) -> "EnsembleProcessing":
        """Create an EnsembleProcessing from a (possibly nested) dictionary."""
        next_node = None
        if "next" in d:
            next_node = from_dict(d["next"])
        return cls._from_dict(d, next_node=next_node)

    @classmethod
    def _from_dict(cls, d: dict, next_node=None) -> "EnsembleProcessing":
        """Create an EnsembleProcessing from a dictionary with a given next_node."""
        return cls(
            method=d.get("method", "mean"),
            ensemble_size=d.get("ensemble_size", 0),
            next_node=next_node,
        )


# ---------------------------------------------------------------------------
# Module-level factory (kind dispatch)
# ---------------------------------------------------------------------------


def _from_dict(d: dict, next_node: ProcessingBase | None = None) -> ProcessingBase:
    """Create a single ProcessingBase node from a dictionary with a given next_node.

    Does NOT recurse into ``d["next"]``.

    Parameters
    ----------
    d : dict
        Dictionary with at least ``kind`` and ``method`` keys.
    next_node : ProcessingBase or None
        The next node to attach.

    Returns
    -------
    TimeProcessing or EnsembleProcessing
    """
    kind = get_processing_kind(d["kind"])
    if kind == ProcessingKind.TIME_PROCESSING:
        return TimeProcessing._from_dict(d, next_node=next_node)
    elif kind == ProcessingKind.ENSEMBLE_STATISTICS:
        return EnsembleProcessing._from_dict(d, next_node=next_node)
    else:
        raise ValueError(f"Unknown processing kind: {kind}")


def from_dict(d: dict) -> ProcessingBase:
    """Create a processing chain from a (possibly nested) dictionary.

    This is the main entry point for deserializing a processing chain.

    Parameters
    ----------
    d : dict
        Dictionary with at least ``kind`` and ``method`` keys. May contain
        a ``"next"`` key with the nested next node's dict.

    Returns
    -------
    ProcessingBase
        The head of the reconstructed chain, or :class:`EmptyProcessing`
        if the dict is empty.
    """
    if not d:
        return EmptyProcessing()

    next_node = None
    if "next" in d:
        next_node = from_dict(d["next"])

    return _from_dict(d, next_node=next_node)
