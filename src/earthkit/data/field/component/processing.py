# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Processing component of a field.

The processing component describes the processing that produced a given field:
time statistics (accumulations, min/max/mean over a window), ensemble statistics
(ensemble mean, spread, ...), ensemble probabilities, etc., as well as any ordered
sequence of such processing steps (e.g. the ensemble mean of a 6-hour maximum).

The representation is format-agnostic: the same model is used whatever the
underlying format (GRIB, CF-netCDF, ...) so the information can be inspected,
filtered on and round-tripped independently of the format.

A :class:`Processing` component is an ordered sequence of :class:`ProcessingStep`
objects. The steps appear on the list in the **reversed order of their application**:
the outermost operation (last applied) is first on the list and the innermost
operation (first applied) is last on the list.
"""

import datetime
import re
from abc import ABCMeta
from typing import Optional

from .component import SimpleFieldComponent

_SECONDS_PER_DAY = 24 * 3600

# fuzzy day spans used when comparing calendar durations (see Duration.matches)
_MONTH_MIN_DAYS = 28
_MONTH_MAX_DAYS = 31
_YEAR_MIN_DAYS = 360
_YEAR_MAX_DAYS = 366
_AVG_DAYS_PER_MONTH = 30.436875
_AVG_DAYS_PER_YEAR = 365.2425


class Kind:
    """Processing step kinds."""

    REDUCTION = "reduction"
    TIME_AGGREGATION = "time_aggregation"
    LAGGED_FORECASTS_AGGREGATION = "lagged_forecasts_aggregation"
    PROBABILITY = "probability"


class Axis:
    """Axes a processing step can operate on."""

    FORECAST_REFERENCE_TIME = "forecast_reference_time"
    FORECAST_PERIOD = "forecast_period"
    ENSEMBLE = "ensemble"
    VERTICAL = "vertical"


# axes a time aggregation step may use
TIME_AXES = (Axis.FORECAST_REFERENCE_TIME, Axis.FORECAST_PERIOD)


class WindowAnchor:
    """Anchor of an aggregation window relative to the reference time/period."""

    LEFT = "left"
    RIGHT = "right"


class Method:
    """Statistical methods."""

    MEAN = "mean"
    SUM = "sum"
    MAXIMUM = "maximum"
    MINIMUM = "minimum"
    STANDARD_DEVIATION = "standard_deviation"
    VARIANCE = "variance"
    MODE = "mode"
    MEDIAN = "median"
    QUANTILE = "quantile"


class Duration:
    """An ISO 8601 duration.

    See https://en.wikipedia.org/wiki/ISO_8601#Durations.

    The duration is stored as a number of calendar ``months`` (capturing the years
    and months components, which have no fixed length) and a number of ``seconds``
    (capturing the weeks, days, hours, minutes and seconds components).

    Parameters
    ----------
    value : str, Duration, datetime.timedelta or int
        The duration value. A :class:`str` is parsed as an ISO 8601 duration
        (e.g. ``"PT6H"``, ``"P1M"``, ``"P30Y"``). An :class:`int` is interpreted
        as a number of hours.
    """

    _PATTERN = re.compile(
        r"^(?P<sign>[+-])?P"
        r"(?:(?P<years>\d+)Y)?"
        r"(?:(?P<months>\d+)M)?"
        r"(?:(?P<weeks>\d+)W)?"
        r"(?:(?P<days>\d+)D)?"
        r"(?:T"
        r"(?:(?P<hours>\d+)H)?"
        r"(?:(?P<minutes>\d+)M)?"
        r"(?:(?P<seconds>\d+(?:\.\d+)?)S)?"
        r")?$"
    )

    def __init__(self, value=None, *, months=0, seconds=0):
        if value is None:
            self.months = int(months)
            self.seconds = seconds
        elif isinstance(value, Duration):
            self.months = value.months
            self.seconds = value.seconds
        elif isinstance(value, datetime.timedelta):
            self.months = 0
            self.seconds = value.total_seconds()
        elif isinstance(value, (int,)) and not isinstance(value, bool):
            self.months = 0
            self.seconds = value * 3600
        elif isinstance(value, str):
            d = Duration._parse(value)
            self.months = d.months
            self.seconds = d.seconds
        else:
            raise ValueError(f"Cannot create Duration from {value!r} of type {type(value)}")

        if self.seconds == int(self.seconds):
            self.seconds = int(self.seconds)

    @classmethod
    def _parse(cls, text):
        text = text.strip()
        m = cls._PATTERN.fullmatch(text)
        if not m or text in ("P", "PT"):
            raise ValueError(f"Invalid ISO 8601 duration: {text!r}")

        g = m.groupdict()
        sign = -1 if g["sign"] == "-" else 1

        def _n(key):
            v = g[key]
            return float(v) if v is not None else 0

        months = _n("years") * 12 + _n("months")
        seconds = (
            (_n("weeks") * 7 + _n("days")) * _SECONDS_PER_DAY + _n("hours") * 3600 + _n("minutes") * 60 + _n("seconds")
        )
        return cls(months=sign * int(months), seconds=sign * seconds)

    @classmethod
    def from_any(cls, value):
        """Return a :class:`Duration` from ``value``, or None if ``value`` is None."""
        if value is None:
            return None
        if isinstance(value, Duration):
            return value
        return cls(value)

    def iso(self):
        """Return the ISO 8601 string representation of the duration."""
        months = abs(self.months)
        seconds = abs(self.seconds)
        sign = "-" if (self.months < 0 or self.seconds < 0) else ""

        years, months = divmod(months, 12)

        days, rem = divmod(seconds, _SECONDS_PER_DAY)
        days = int(days)

        date_part = ""
        if years:
            date_part += f"{years}Y"
        if months:
            date_part += f"{months}M"
        if days:
            date_part += f"{days}D"

        # express the sub-day remainder as whole hours when possible, otherwise as
        # seconds (matching the convention used in the design document, e.g. "PT900S")
        time_part = ""
        if rem:
            if rem % 3600 == 0:
                time_part = f"{int(rem // 3600)}H"
            else:
                if rem == int(rem):
                    rem = int(rem)
                time_part = f"{rem}S"

        if not date_part and not time_part:
            return "PT0S"

        out = "P" + date_part
        if time_part:
            out += "T" + time_part
        return sign + out

    def to_timedelta(self):
        """Return the duration as a :class:`datetime.timedelta`.

        Calendar components (years, months) have no fixed length and are converted
        using average values (1 month = 30.436875 days, 1 year = 365.2425 days).
        """
        days = self.months * _AVG_DAYS_PER_MONTH
        return datetime.timedelta(days=days, seconds=self.seconds)

    @property
    def nominal_seconds(self):
        """Approximate total length in seconds, for ordering purposes."""
        return self.months * _AVG_DAYS_PER_MONTH * _SECONDS_PER_DAY + self.seconds

    def _range_seconds(self):
        """Return the (min, max) possible length in seconds, accounting for calendar fuzz."""
        if self.months == 0:
            return (self.seconds, self.seconds)
        if self.months % 12 == 0:
            years = self.months // 12
            lo = _YEAR_MIN_DAYS * years
            hi = _YEAR_MAX_DAYS * years
        else:
            lo = _MONTH_MIN_DAYS * self.months
            hi = _MONTH_MAX_DAYS * self.months
        return (lo * _SECONDS_PER_DAY + self.seconds, hi * _SECONDS_PER_DAY + self.seconds)

    def matches(self, other):
        """Return True if this duration may be equal to ``other``, allowing calendar fuzz.

        A month spans 28-31 days and a year spans 360-366 days, so ``"P1M"`` matches
        any of ``"P28D"`` .. ``"P31D"`` and ``"P1Y"`` matches any of ``"P360D"`` .. ``"P366D"``.
        """
        other = Duration.from_any(other)
        if other is None:
            return False
        a_lo, a_hi = self._range_seconds()
        b_lo, b_hi = other._range_seconds()
        return a_lo <= b_hi and b_lo <= a_hi

    def __eq__(self, other):
        if not isinstance(other, Duration):
            try:
                other = Duration.from_any(other)
            except Exception:
                return NotImplemented
        if other is None:
            return False
        return self.months == other.months and self.seconds == other.seconds

    def __hash__(self):
        return hash((self.months, self.seconds))

    def __lt__(self, other):
        return self.nominal_seconds < Duration(other).nominal_seconds

    def __le__(self, other):
        return self.nominal_seconds <= Duration(other).nominal_seconds

    def __gt__(self, other):
        return self.nominal_seconds > Duration(other).nominal_seconds

    def __ge__(self, other):
        return self.nominal_seconds >= Duration(other).nominal_seconds

    def __repr__(self):
        return f'Duration("{self.iso()}")'

    def __str__(self):
        return self.iso()


class Interval:
    """A numeric interval ``(a, b)``, ``[a, b]``, ``[a, b)`` or ``(a, b]``.

    ``a`` can be ``-inf`` (None) and ``b`` can be ``+inf`` (None).

    Parameters
    ----------
    lower, upper : float or None
        The interval endpoints. None means unbounded.
    closed_lower, closed_upper : bool
        Whether the respective endpoint is included in the interval.
    """

    def __init__(self, lower=None, upper=None, closed_lower=True, closed_upper=False):
        self.lower = None if lower is None else float(lower)
        self.upper = None if upper is None else float(upper)
        self.closed_lower = bool(closed_lower)
        self.closed_upper = bool(closed_upper)

    def endpoints(self):
        """Return the (lower, upper) endpoints as a tuple."""
        return (self.lower, self.upper)

    def closed(self):
        """Return the (closed_lower, closed_upper) flags as a tuple."""
        return (self.closed_lower, self.closed_upper)

    @classmethod
    def from_any(cls, value):
        """Create an :class:`Interval` from a dict, tuple/list or Interval."""
        if value is None:
            return None
        if isinstance(value, Interval):
            return value
        if isinstance(value, dict):
            return cls(
                lower=value.get("lower", value.get("a")),
                upper=value.get("upper", value.get("b")),
                closed_lower=value.get("closed_lower", True),
                closed_upper=value.get("closed_upper", False),
            )
        if isinstance(value, (tuple, list)):
            lower = value[0] if len(value) > 0 else None
            upper = value[1] if len(value) > 1 else None
            return cls(lower=lower, upper=upper)
        raise ValueError(f"Cannot create Interval from {value!r}")

    def to_dict(self):
        return {
            "lower": self.lower,
            "upper": self.upper,
            "closed_lower": self.closed_lower,
            "closed_upper": self.closed_upper,
        }

    def __eq__(self, other):
        if not isinstance(other, Interval):
            return NotImplemented
        return (
            self.lower == other.lower
            and self.upper == other.upper
            and self.closed_lower == other.closed_lower
            and self.closed_upper == other.closed_upper
        )

    def __repr__(self):
        left = "[" if self.closed_lower else "("
        right = "]" if self.closed_upper else ")"
        lo = "-inf" if self.lower is None else self.lower
        hi = "+inf" if self.upper is None else self.upper
        return f"Interval({left}{lo}, {hi}{right})"


# ---------------------------------------------------------------------------
# Processing steps
# ---------------------------------------------------------------------------

# the full set of attribute accessors exposed by a step / the component
STEP_ATTRS = (
    "axis",
    "method",
    "method_parameter",
    "sample_size",
    "window_length",
    "window_axis",
    "window_anchor",
    "sampling_frequency",
    "threshold_interval",
    "threshold_interval_endpoints",
    "threshold_interval_units",
)

# attributes whose values are durations
_DURATION_ATTRS = ("window_length", "sampling_frequency")

_DURATION_FMT = {str: "iso", "str": "iso"}


def _format_duration(d, type=str):
    if d is None:
        return None
    if type in (str, "str"):
        return d.iso()
    if type in (datetime.timedelta, "timedelta"):
        return d.to_timedelta()
    if type in (Duration, False, None, "duration"):
        return d
    raise ValueError(f"Unsupported type={type!r} for a duration accessor")


class ProcessingStep(metaclass=ABCMeta):
    """Abstract base class for a single processing step.

    Each concrete step exposes one accessor per attribute; inapplicable attributes
    return None. Durations are returned as ISO 8601 strings by default; pass
    ``type=datetime.timedelta`` to get a :class:`datetime.timedelta` or
    ``type=Duration`` for a :class:`Duration` object.
    """

    KIND = None
    # the attributes supported by this step (subset of STEP_ATTRS)
    ATTRS = ()

    # expose the kind constants for convenience (e.g. ProcessingStep.TIME_AGGREGATION)
    REDUCTION = Kind.REDUCTION
    TIME_AGGREGATION = Kind.TIME_AGGREGATION
    LAGGED_FORECASTS_AGGREGATION = Kind.LAGGED_FORECASTS_AGGREGATION
    PROBABILITY = Kind.PROBABILITY

    _ALIASES = {"ensemble_size": "sample_size"}

    def __init__(self, **kwargs):
        attrs = {}
        for k_in, v in kwargs.items():
            k = self._ALIASES.get(k_in, k_in)
            if k not in self.ATTRS:
                raise ValueError(
                    f"Unknown or inapplicable attribute {k_in!r} for {type(self).__name__}. Allowed: {self.ATTRS}"
                )
            if v is None:
                continue
            attrs[k] = self._coerce(k, v)
        self._attrs = attrs

    @staticmethod
    def _coerce(key, value):
        if key in _DURATION_ATTRS:
            return Duration.from_any(value)
        if key == "threshold_interval":
            return Interval.from_any(value)
        if key == "sample_size":
            return int(value)
        if key == "method_parameter":
            return float(value)
        return value

    def kind(self):
        """Return the kind of the processing step."""
        return self.KIND

    def axis(self) -> Optional[str]:
        """Return the axis the step operates on, or None."""
        return self._attrs.get("axis")

    def method(self) -> Optional[str]:
        """Return the statistical method, or None."""
        return self._attrs.get("method")

    def method_parameter(self) -> Optional[float]:
        """Return the method parameter (e.g. the quantile), or None."""
        return self._attrs.get("method_parameter")

    def sample_size(self) -> Optional[int]:
        """Return the sample size, or None."""
        return self._attrs.get("sample_size")

    def window_length(self, type=str):
        """Return the aggregation window length, or None.

        Parameters
        ----------
        type : type
            The return type. ``str`` (default) returns an ISO 8601 string,
            ``datetime.timedelta`` returns a timedelta and :class:`Duration`
            returns a Duration object.
        """
        return _format_duration(self._attrs.get("window_length"), type)

    def window_axis(self) -> Optional[str]:
        """Return the axis of the aggregation window, or None.

        This is the ``axis`` of window-based steps (time aggregation) and None
        for steps that do not define an aggregation window.
        """
        if "window_length" in self._attrs:
            return self._attrs.get("axis")
        return None

    def window_anchor(self) -> Optional[str]:
        """Return the window anchor (``"left"`` or ``"right"``), or None."""
        return self._attrs.get("window_anchor")

    def sampling_frequency(self, type=str):
        """Return the sampling frequency of the window, or None.

        See :meth:`window_length` for the ``type`` argument.
        """
        return _format_duration(self._attrs.get("sampling_frequency"), type)

    def threshold_interval(self) -> Optional[tuple]:
        """Return the threshold interval endpoints ``(a, b)``, or None."""
        interval = self._attrs.get("threshold_interval")
        if interval is None:
            return None
        return interval.endpoints()

    def threshold_interval_endpoints(self) -> Optional[tuple]:
        """Return whether the threshold interval endpoints are closed ``(bool, bool)``, or None."""
        interval = self._attrs.get("threshold_interval")
        if interval is None:
            return None
        return interval.closed()

    def threshold_interval_units(self) -> Optional[str]:
        """Return the units of the threshold interval, or None."""
        return self._attrs.get("threshold_interval_units")

    def get(self, key, default=None):
        """Return the value of the attribute ``key`` (equivalent to ``step.<key>()``)."""
        key = self._ALIASES.get(key, key)
        if key == "kind":
            return self.kind()
        if key in STEP_ATTRS:
            return getattr(self, key)()
        return default

    def set(self, **kwargs):
        """Return a new processing step with the given attributes updated."""
        attrs = dict(self._attrs)
        for k_in, v in kwargs.items():
            k = self._ALIASES.get(k_in, k_in)
            if k not in self.ATTRS:
                raise ValueError(f"Unknown or inapplicable attribute {k_in!r} for {type(self).__name__}")
            if v is None:
                attrs.pop(k, None)
            else:
                attrs[k] = self._coerce(k, v)
        new = type(self).__new__(type(self))
        new._attrs = attrs
        return new

    def to_dict(self):
        """Return the step as a format-neutral dict."""
        d = {"kind": self.KIND}
        for k in self.ATTRS:
            if k not in self._attrs:
                continue
            v = self._attrs[k]
            if isinstance(v, Duration):
                v = v.iso()
            elif isinstance(v, Interval):
                v = v.to_dict()
            d[k] = v
        return d

    @classmethod
    def from_dict(cls, d):
        """Create a processing step from a dict (dispatching on its ``kind``)."""
        d = dict(d)
        kind = d.pop("kind", None)
        if kind is None:
            raise ValueError(f"Processing step dict is missing the 'kind' key: {d}")
        step_cls = _STEP_CLASSES.get(kind)
        if step_cls is None:
            raise ValueError(f"Unknown processing step kind: {kind!r}")
        return step_cls(**d)

    def __eq__(self, other):
        if not isinstance(other, ProcessingStep):
            return NotImplemented
        return self.KIND == other.KIND and self.to_dict() == other.to_dict()

    def __repr__(self):
        args = ", ".join(f"{k}={self._attrs[k]!r}" for k in self.ATTRS if k in self._attrs)
        return f"{type(self).__name__}({args})"


class ReductionStep(ProcessingStep):
    """A statistical reduction over a sample along an axis, collapsing that axis.

    The ``method`` is applied to a sample of size ``sample_size`` along ``axis``.
    """

    KIND = Kind.REDUCTION
    ATTRS = ("axis", "method", "method_parameter", "sample_size")


class TimeAggregationStep(ProcessingStep):
    """A statistical aggregation over a time window.

    The ``method`` is applied to a time window which has the axis defined by ``axis``
    (``forecast_reference_time`` or ``forecast_period``), has length ``window_length``,
    is anchored according to ``window_anchor`` and is discretised by sampling with
    ``sampling_frequency``.
    """

    KIND = Kind.TIME_AGGREGATION
    ATTRS = ("axis", "method", "method_parameter", "window_length", "window_anchor", "sampling_frequency")


class LaggedForecastsAggregationStep(ProcessingStep):
    """An aggregation over lagged forecasts (see the design document)."""

    KIND = Kind.LAGGED_FORECASTS_AGGREGATION
    ATTRS = ("method", "method_parameter", "window_length", "sampling_frequency")


class EnsembleProbabilityStep(ProcessingStep):
    """A probability that a field value falls into ``threshold_interval``.

    The probability is computed based on an ensemble of size ``sample_size``.
    The interval endpoints are interpreted in units given by ``threshold_interval_units``.
    """

    KIND = Kind.PROBABILITY
    ATTRS = ("threshold_interval", "threshold_interval_units", "sample_size")


_STEP_CLASSES = {
    Kind.REDUCTION: ReductionStep,
    Kind.TIME_AGGREGATION: TimeAggregationStep,
    Kind.LAGGED_FORECASTS_AGGREGATION: LaggedForecastsAggregationStep,
    Kind.PROBABILITY: EnsembleProbabilityStep,
}


class _EmptyProcessingStep(ProcessingStep):
    """A processing step whose accessors all return None.

    Returned when indexing a :class:`Processing` component past its end, so that
    e.g. ``p[999].method()`` is always safe.
    """

    KIND = None
    ATTRS = STEP_ATTRS

    def __init__(self):
        self._attrs = {}

    def kind(self):
        return None

    def to_dict(self):
        return {}


EMPTY_STEP = _EmptyProcessingStep()


# parse "<attr>[<index>]" style keys
_INDEXED_KEY = re.compile(r"^(?P<attr>[A-Za-z_][A-Za-z0-9_]*)\[(?P<index>-?\d+)\]$")


def _parse_indexed_key(key):
    """Return (attr, index) if ``key`` is of the form ``"<attr>[i]"`` else (key, None)."""
    m = _INDEXED_KEY.fullmatch(key)
    if m:
        return m.group("attr"), int(m.group("index"))
    return key, None


# ---------------------------------------------------------------------------
# Processing component
# ---------------------------------------------------------------------------


class ProcessingBase(SimpleFieldComponent):
    """Base class for the processing component of a field."""

    _KEYS = ("kind",) + STEP_ATTRS
    _ALIASES = {"ensemble_size": "sample_size"}


class EmptyProcessing(ProcessingBase):
    """An empty processing component (no processing steps)."""

    def steps(self):
        return ()

    def __len__(self):
        return 0

    def __iter__(self):
        return iter(())

    def __getitem__(self, index):
        if isinstance(index, slice):
            return self
        return EMPTY_STEP

    def __add__(self, other):
        return Processing.from_any(other)

    def __contains__(self, name):
        attr, _ = _parse_indexed_key(name)
        return self._ALIASES.get(attr, attr) in self._KEYS

    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        return self._get_single(key, default=default, astype=astype, raise_on_missing=raise_on_missing)

    def _get_single(self, key, default=None, astype=None, raise_on_missing=False):
        attr, index = _parse_indexed_key(key)
        attr = self._ALIASES.get(attr, attr)
        if attr in self._KEYS:
            if index is not None:
                return None
            return tuple()
        if raise_on_missing:
            raise KeyError(f"Key {key} not found in processing component")
        return default

    @classmethod
    def from_dict(cls, d):
        return cls()

    def to_dict(self):
        return dict()

    def set(self, *args, **kwargs):
        # setting on an empty component builds a new Processing
        return Processing([]).set(*args, **kwargs)

    def __eq__(self, other):
        return isinstance(other, (EmptyProcessing,)) or (isinstance(other, Processing) and len(other) == 0)

    def __repr__(self):
        return "Processing([])"

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        pass


class Processing(ProcessingBase):
    """The processing component of a field: an immutable sequence of processing steps.

    The steps appear in the reversed order of their application (outermost first).

    The component behaves like an immutable sequence::

        len(p)            # number of processing steps
        for ps in p: ...  # iterate over the ProcessingStep objects
        p[i]              # the i-th ProcessingStep
        p[i:j]            # a slice, itself a Processing
        p + other         # concatenation, resulting in a new Processing

    Indexing past the end returns an empty processing step whose accessors all
    return None, rather than raising an exception, so ``p[999].method()`` is safe.

    The component also offers propagated accessors (:meth:`kind`, :meth:`method`,
    ...) that return a tuple with one value per processing step (None where the
    attribute is not applicable).
    """

    def __init__(self, steps=None):
        if steps is None:
            steps = ()
        self._steps = tuple(self._as_step(s) for s in steps)

    @staticmethod
    def _as_step(s):
        if isinstance(s, ProcessingStep):
            return s
        if isinstance(s, dict):
            return ProcessingStep.from_dict(s)
        raise ValueError(f"Cannot create a processing step from {s!r}")

    def steps(self):
        """Return the processing steps as a tuple."""
        return self._steps

    # -- sequence protocol --------------------------------------------------

    def __len__(self):
        return len(self._steps)

    def __iter__(self):
        return iter(self._steps)

    def __getitem__(self, index):
        if isinstance(index, slice):
            return Processing(self._steps[index])
        if -len(self._steps) <= index < len(self._steps):
            return self._steps[index]
        return EMPTY_STEP

    def __add__(self, other):
        other = Processing.from_any(other)
        return Processing(self._steps + other._steps)

    def __eq__(self, other):
        if isinstance(other, EmptyProcessing):
            return len(self._steps) == 0
        if not isinstance(other, Processing):
            return NotImplemented
        return self._steps == other._steps

    def __repr__(self):
        return f"Processing({list(self._steps)!r})"

    # -- propagated accessors ----------------------------------------------

    def _propagate(self, name, *args, **kwargs):
        return tuple(getattr(step, name)(*args, **kwargs) for step in self._steps)

    def kind(self):
        """Return a tuple with the kind of each processing step."""
        return self._propagate("kind")

    def axis(self):
        """Return a tuple with the axis of each processing step (None where not applicable)."""
        return self._propagate("axis")

    def method(self):
        """Return a tuple with the method of each processing step."""
        return self._propagate("method")

    def method_parameter(self):
        """Return a tuple with the method parameter of each processing step."""
        return self._propagate("method_parameter")

    def sample_size(self):
        """Return a tuple with the sample size of each processing step."""
        return self._propagate("sample_size")

    def window_length(self, type=str):
        """Return a tuple with the window length of each processing step."""
        return self._propagate("window_length", type=type)

    def window_axis(self):
        """Return a tuple with the window axis of each processing step."""
        return self._propagate("window_axis")

    def window_anchor(self):
        """Return a tuple with the window anchor of each processing step."""
        return self._propagate("window_anchor")

    def sampling_frequency(self, type=str):
        """Return a tuple with the sampling frequency of each processing step."""
        return self._propagate("sampling_frequency", type=type)

    def threshold_interval(self):
        """Return a tuple with the threshold interval of each processing step."""
        return self._propagate("threshold_interval")

    def threshold_interval_endpoints(self):
        """Return a tuple with the threshold interval endpoints flags of each processing step."""
        return self._propagate("threshold_interval_endpoints")

    def threshold_interval_units(self):
        """Return a tuple with the threshold interval units of each processing step."""
        return self._propagate("threshold_interval_units")

    # -- keyed access -------------------------------------------------------

    def __contains__(self, name):
        attr, _ = _parse_indexed_key(name)
        return self._ALIASES.get(attr, attr) in self._KEYS

    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        """Return the value for ``key``.

        A plain key (e.g. ``"method"``) returns the propagated tuple; an indexed
        key (e.g. ``"method[0]"``) returns a single step's value, which is exactly
        ``p[i].get("method")``.
        """
        return self._get_single(key, default=default, astype=astype, raise_on_missing=raise_on_missing)

    def _get_single(self, key, default=None, astype=None, raise_on_missing=False):
        attr, index = _parse_indexed_key(key)
        attr = self._ALIASES.get(attr, attr)

        if attr not in self._KEYS:
            if raise_on_missing:
                raise KeyError(f"Key {key} not found in processing component")
            return default

        if index is not None:
            v = self[index].get(attr)
        else:
            v = getattr(self, attr)()

        if astype is not None and v is not None and callable(astype):
            try:
                return astype(v)
            except Exception:
                return default
        return v

    def set(self, *args, **kwargs):
        """Return a new processing component with the given updates applied.

        - ``p.set({"method[0]": "mean"})`` tweaks one attribute of one step.
        - ``p.set([{...}, {...}])`` replaces the whole chain.
        """
        updates = {}
        for a in args:
            if a is None:
                continue
            if isinstance(a, (list, tuple)):
                # replace the whole chain
                return Processing(a)
            if isinstance(a, Processing):
                return a
            if isinstance(a, dict):
                updates.update(a)
                continue
            raise ValueError(f"Cannot use arg={a!r} to set the processing component")
        updates.update(kwargs)

        steps = list(self._steps)
        # group updates by step index
        per_step = {}
        for k, v in updates.items():
            attr, index = _parse_indexed_key(k)
            if index is None:
                raise KeyError(
                    f"Processing.set requires an indexed key like 'method[0]', got {k!r}. "
                    f"To replace the whole chain pass a list of step dicts."
                )
            per_step.setdefault(index, {})[attr] = v

        for index, step_updates in per_step.items():
            if not (-len(steps) <= index < len(steps)):
                raise IndexError(f"Processing step index {index} out of range (len={len(steps)})")
            steps[index] = steps[index].set(**step_updates)

        return Processing(steps)

    # -- serialisation ------------------------------------------------------

    def to_dict(self):
        """Return the component as ``{"items": [ {...}, ... ]}``."""
        return {"items": [step.to_dict() for step in self._steps]}

    @classmethod
    def from_dict(cls, d):
        """Create a :class:`Processing` from a dict or a list of step dicts."""
        return cls.from_any(d)

    @classmethod
    def from_any(cls, value):
        """Create a :class:`Processing` from a Processing, a list of steps/dicts or a dict."""
        if value is None:
            return cls([])
        if isinstance(value, Processing):
            return value
        if isinstance(value, EmptyProcessing):
            return cls([])
        if isinstance(value, ProcessingStep):
            return cls([value])
        if isinstance(value, dict):
            items = value.get("items", value.get("processing_steps"))
            if items is None:
                # a dict that is itself a single step
                if "kind" in value:
                    return cls([ProcessingStep.from_dict(value)])
                items = []
            return cls(items)
        if isinstance(value, (list, tuple)):
            return cls(value)
        raise ValueError(f"Cannot create Processing from {value!r}")

    def __getstate__(self):
        return {"steps": self._steps}

    def __setstate__(self, state):
        self._steps = tuple(state.get("steps", ()))


# ---------------------------------------------------------------------------
# Field list selection support
# ---------------------------------------------------------------------------


def make_selection_matcher(attr, value):
    """Return a callable implementing field list selection for a processing key.

    The returned callable takes the value produced by the field for the selection
    key (a propagated tuple for a plain key, or a single value for an indexed key)
    and returns True if it matches ``value``.

    Chain-valued (plain) keys match if **any** step in the chain matches. Duration
    keys compare fuzzily about calendar components (see :meth:`Duration.matches`).
    A slice selects a closed interval (inclusive of both bounds).

    Parameters
    ----------
    attr : str
        The processing attribute name (already stripped of the ``"processing."``
        prefix and of any ``"[i]"`` index).
    value : Any
        The selection value: a single value, a list/tuple/set of values, or a slice.
    """
    is_duration = attr in _DURATION_ATTRS

    def _candidates(field_value):
        # a propagated tuple -> each item is a candidate; a scalar -> single candidate
        if isinstance(field_value, tuple):
            return list(field_value)
        return [field_value]

    if isinstance(value, slice):
        if is_duration:
            lo = Duration.from_any(value.start)
            hi = Duration.from_any(value.stop)

            def match(field_value):
                for c in _candidates(field_value):
                    if c is None:
                        continue
                    d = Duration.from_any(c)
                    if lo is not None and d < lo:
                        continue
                    if hi is not None and d > hi:
                        continue
                    return True
                return False

        else:
            lo = value.start
            hi = value.stop

            def match(field_value):
                for c in _candidates(field_value):
                    if c is None:
                        continue
                    if lo is not None and c < lo:
                        continue
                    if hi is not None and c > hi:
                        continue
                    return True
                return False

        return match

    # single value or list of values
    if isinstance(value, (list, tuple, set)):
        targets = list(value)
    else:
        targets = [value]

    if is_duration:
        targets = [Duration.from_any(t) for t in targets]

        def match(field_value):
            for c in _candidates(field_value):
                if c is None:
                    continue
                d = Duration.from_any(c)
                if any(d.matches(t) for t in targets if t is not None):
                    return True
            return False

    else:
        target_set = set()
        for t in targets:
            target_set.add(t)
            target_set.add(str(t))

        def match(field_value):
            for c in _candidates(field_value):
                if c is None:
                    continue
                if c in target_set or str(c) in target_set:
                    return True
            return False

    return match
