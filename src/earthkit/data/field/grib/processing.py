# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Build the :class:`Processing` component of a field from a GRIB message.

For GRIB2 statistically-processed products the mapping is:

* the ECMWF ``stattype`` key (if set) has the form ``<duration><stat>[_<duration><stat>]*``
  (e.g. ``"daav"`` = daily average, ``"damx_daav"`` = daily max of daily average); each
  ``<duration><stat>`` segment defines the method and window length of an **outer**
  time aggregation step;
* the ``stepType`` and ``timespan`` keys define the **inner** (first applied) time
  aggregation step;
* ``typeOfTimeIncrement`` (a scalar or, for several time ranges, an array) defines the
  time axis of each step (forecast reference time, forecast period or lagged forecasts).

The coded statistical-processing arrays of the GRIB2 Product Definition Template
(``typeOfStatisticalProcessing``, ``lengthOfTimeRange``, ``timeIncrement`` and their unit
indicators) are listed in the same order (outermost first) and are used to derive the
time axis, the sampling frequency and as a fallback for the method and window length.

GRIB1 messages (and GRIB2 messages that are not statistically processed) fall back to a
single step derived from ``stepType`` and the step range.
"""

from earthkit.data.field.component.processing import (
    Axis,
    Duration,
    Kind,
    LaggedForecastsAggregationStep,
    Method,
    ReductionStep,
    TimeAggregationStep,
    WindowAnchor,
)
from earthkit.data.utils.dates import step_to_grib, to_timedelta

from .collector import GribContextCollector
from .core import GribFieldComponentHandler

# GRIB stepType -> method (also used by the GRIB1 / non-statistical fallback)
_STEPTYPE_TO_METHOD = {
    "accum": Method.SUM,
    "avg": Method.MEAN,
    "avgd": Method.MEAN,
    "ave": Method.MEAN,
    "max": Method.MAXIMUM,
    "min": Method.MINIMUM,
    "sum": Method.SUM,
    "stddev": Method.STANDARD_DEVIATION,
}

_METHOD_TO_STEPTYPE = {
    Method.SUM: "accum",
    Method.MEAN: "avg",
    Method.MAXIMUM: "max",
    Method.MINIMUM: "min",
    Method.STANDARD_DEVIATION: "stddev",
}

# GRIB2 typeOfStatisticalProcessing (code table 4.10) -> method
_STATPROC_TO_METHOD = {
    0: Method.MEAN,  # Average
    1: Method.SUM,  # Accumulation
    2: Method.MAXIMUM,  # Maximum
    3: Method.MINIMUM,  # Minimum
    6: Method.STANDARD_DEVIATION,  # Standard deviation
}

# ECMWF stattype statistic code -> method
_STATCODE_TO_METHOD = {
    "mx": Method.MAXIMUM,
    "mn": Method.MINIMUM,
    "av": Method.MEAN,
    "me": Method.MEAN,
    "su": Method.SUM,
    "ac": Method.SUM,
    "sd": Method.STANDARD_DEVIATION,
    "md": Method.MEDIAN,
}

# ECMWF stattype duration code -> ISO 8601 duration
_STATCODE_TO_DURATION = {
    "da": "P1D",
    "mo": "P1M",
    "yr": "P1Y",
    "we": "P7D",
    "se": "P3M",
    "ho": "PT1H",
}

# GRIB2 derivedForecast (code table 4.7) -> ensemble reduction method
_DERIVED_TO_METHOD = {
    0: Method.MEAN,  # unweighted mean of all members
    1: Method.MEAN,  # weighted mean of all members
    2: Method.STANDARD_DEVIATION,  # standard deviation w.r.t. cluster mean
    3: Method.STANDARD_DEVIATION,  # standard deviation w.r.t. cluster mean, normalized
    4: Method.STANDARD_DEVIATION,  # spread of all members
}

# GRIB2 typeOfTimeIncrement (code table 4.11) -> time axis
_TTI_TO_AXIS = {
    1: Axis.FORECAST_REFERENCE_TIME,  # same forecast time, start time incremented
    2: Axis.FORECAST_PERIOD,  # same start time, forecast time incremented
}
# typeOfTimeIncrement values denoting a lagged-forecasts aggregation
# (start time incremented, forecast time decremented, valid time constant)
_TTI_LAGGED = {3}

_AXIS_TO_ANCHOR = {
    Axis.FORECAST_REFERENCE_TIME: WindowAnchor.LEFT,
    Axis.FORECAST_PERIOD: WindowAnchor.RIGHT,
}

# GRIB2 indicator of unit of time range (code table 4.4) -> (months, seconds) factors
# for one unit. Calendar units (month, year, ...) are kept as months so they stay exact.
_UNIT_TO_DURATION = {
    0: (0, 60),  # minute
    1: (0, 3600),  # hour
    2: (0, 86400),  # day
    3: (1, 0),  # month
    4: (12, 0),  # year
    5: (120, 0),  # decade
    6: (360, 0),  # normal (30 years)
    7: (1200, 0),  # century
    10: (0, 3 * 3600),  # 3 hours
    11: (0, 6 * 3600),  # 6 hours
    12: (0, 12 * 3600),  # 12 hours
    13: (0, 1),  # second
}


def _as_list(value):
    """Normalise a GRIB key value (scalar, list or numpy array) to a list."""
    if value is None:
        return []
    if isinstance(value, (list, tuple)):
        return list(value)
    if hasattr(value, "tolist"):
        return list(value.tolist())
    return [value]


def _at(values, index, default=None):
    return values[index] if 0 <= index < len(values) else default


def _coded_duration(value, unit):
    """Build a :class:`Duration` from a coded (value, unit-indicator) pair."""
    if value is None or unit is None:
        return None
    factors = _UNIT_TO_DURATION.get(int(unit))
    if factors is None:
        return None
    months, seconds = factors
    value = int(value)
    return Duration(months=months * value, seconds=seconds * value)


def _parse_timespan(timespan):
    """Parse an ECMWF ``timespan`` value (e.g. ``"1h"``, ``"6h"``, ``"1d"``) to a Duration."""
    if timespan is None:
        return None
    text = str(timespan).strip().lower()
    if not text:
        return None
    unit = text[-1]
    try:
        n = int(text[:-1])
    except ValueError:
        return None
    if unit == "h":
        return Duration(seconds=n * 3600)
    if unit == "d":
        return Duration(seconds=n * 86400)
    if unit == "m":  # minutes
        return Duration(seconds=n * 60)
    if unit == "s":
        return Duration(seconds=n)
    return None


def _step_range_window(get):
    """Return the step-range span (endStep - startStep) as a Duration, or None."""
    end = get("endStep")
    if end is None:
        end = get("step")
    if end is None:
        return None
    end = to_timedelta(end)
    start = get("startStep")
    start = to_timedelta(start) if start is not None else to_timedelta(0)
    return Duration(end - start)


def _split_stattype(stattype):
    """Split a stattype string into (duration_code, stat_code) segments (outermost first)."""
    segments = []
    for seg in str(stattype).split("_"):
        seg = seg.strip()
        if len(seg) < 4:
            return None
        segments.append((seg[:2], seg[2:]))
    return segments or None


def _clean(value):
    """Return a GRIB string value, mapping missing/``"none"`` placeholders to None."""
    if value is None:
        return None
    text = str(value).strip()
    if not text or text.lower() == "none":
        return None
    return text


def _methods_windows_from_high_level(get, n):
    """Return the ordered [(method, window_length), ...] from stattype / stepType / timespan.

    ``n`` is the number of time ranges in the message. The result has one entry per range,
    outermost first. A multi-segment ``stattype`` (e.g. ``"a_b"``) contributes one step per
    segment (segment ``a`` is the outer, ``b`` the inner). When the stattype segments do not
    account for all the ranges, the remaining (innermost) range is taken from ``stepType``
    and ``timespan`` (or the step range when there is no stattype, i.e. a plain forecast).

    Returns None when the high-level keys do not describe the processing (so the caller
    falls back to the coded statistical-processing arrays).
    """
    result = []

    stattype = _clean(get("stattype"))
    timespan = _clean(get("timespan"))

    # outer steps from stattype (outermost first)
    if stattype:
        segments = _split_stattype(stattype)
        if segments is None:
            return None
        for dur, stat in segments:
            method = _STATCODE_TO_METHOD.get(stat)
            window = _STATCODE_TO_DURATION.get(dur)
            if method is None or window is None:
                return None
            result.append((method, Duration(window)))

    # innermost step from stepType + timespan, only if the stattype segments do not already
    # account for all the time ranges (otherwise stepType just echoes the innermost segment)
    if len(result) < n:
        step_type = str(get("stepType", "instant")).lower()
        method = _STEPTYPE_TO_METHOD.get(step_type)
        if method is not None:
            if timespan is not None:
                window = _parse_timespan(timespan)
            elif not stattype:
                window = _step_range_window(get)
            else:
                window = None
            result.append((method, window))

    return result or None


def _ensemble_step(get):
    """Build the outer ensemble reduction step from the GRIB2 ensemble keys, or None.

    An ensemble reduction is recorded only for derived forecasts (GRIB2 PDT 12), i.e. when
    ``derivedForecast`` is set - not for individual ensemble members (PDT 11). The method
    comes from ``derivedForecast`` and the sample size from ``numberOfForecastsInEnsemble``.
    """
    derived = get("derivedForecast")
    if derived is None:
        return None
    method = _DERIVED_TO_METHOD.get(int(derived))
    size = get("numberOfForecastsInEnsemble")
    size = int(size) if size is not None and int(size) > 0 else None
    return ReductionStep(axis=Axis.ENSEMBLE, method=method, sample_size=size)


def _make_step(tti, method, window, sampling):
    if tti is not None and int(tti) in _TTI_LAGGED:
        return LaggedForecastsAggregationStep(
            method=method,
            window_length=window,
            sampling_frequency=sampling,
        )
    axis = _TTI_TO_AXIS.get(int(tti)) if tti is not None else None
    return TimeAggregationStep(
        axis=axis,
        method=method,
        window_length=window,
        window_anchor=_AXIS_TO_ANCHOR.get(axis),
        sampling_frequency=sampling,
    )


class GribProcessingBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.component.processing import Processing
        from earthkit.data.field.handler.processing import ProcessingFieldComponentHandler

        steps = GribProcessingBuilder._build_steps(handle)
        component = Processing(steps)
        return ProcessingFieldComponentHandler.from_component(component)

    @staticmethod
    def _build_steps(handle):
        def get(key, default=None):
            # some keys (e.g. endStep on monthly statistics) can fail to decode
            try:
                return handle.get(key, default=default)
            except Exception:
                return default

        # GRIB1: a single step from stepType and the step range, no ensemble handling
        if get("edition") != 2:
            return GribProcessingBuilder._build_simple(get)

        stat_proc = _as_list(get("typeOfStatisticalProcessing"))
        if stat_proc:
            time_steps = GribProcessingBuilder._build_statistical(get, stat_proc)
        else:
            # not a statistically-processed GRIB2 product
            time_steps = GribProcessingBuilder._build_simple(get)

        # a derived forecast (GRIB2 PDT 12) adds an outermost ensemble reduction step
        steps = []
        ensemble = _ensemble_step(get)
        if ensemble is not None:
            steps.append(ensemble)
        steps.extend(time_steps)
        return steps

    @staticmethod
    def _build_statistical(get, stat_proc):
        n = len(stat_proc)
        tti = _as_list(get("typeOfTimeIncrement"))
        length = _as_list(get("lengthOfTimeRange"))
        length_unit = _as_list(get("indicatorOfUnitForTimeRange"))
        incr = _as_list(get("timeIncrement"))
        incr_unit = _as_list(get("indicatorOfUnitForTimeIncrement"))

        # method and window length per time range from the high-level keys; fall back to
        # the coded statistical-processing arrays if they do not line up with the ranges
        mw = _methods_windows_from_high_level(get, n)
        if mw is None or len(mw) != n:
            mw = [
                (_STATPROC_TO_METHOD.get(int(sp)), _coded_duration(_at(length, i), _at(length_unit, i)))
                for i, sp in enumerate(stat_proc)
            ]

        steps = []
        for i in range(n):
            method, window = mw[i]
            if method is None:
                method = _STATPROC_TO_METHOD.get(int(stat_proc[i]))
            if window is None:
                window = _coded_duration(_at(length, i), _at(length_unit, i))
            sampling = _coded_duration(_at(incr, i), _at(incr_unit, i))
            steps.append(_make_step(_at(tti, i), method, window, sampling))

        return steps

    @staticmethod
    def _build_simple(get):
        """Single step from stepType and the step range (GRIB1 / non-statistical GRIB2)."""
        step_type = str(get("stepType", "instant")).lower()
        method = _STEPTYPE_TO_METHOD.get(step_type)
        if method is None:
            return []  # instantaneous field: no processing step
        window = _step_range_window(get)
        sampling = _coded_duration(get("timeIncrement"), get("indicatorOfUnitForTimeIncrement"))
        return [
            TimeAggregationStep(
                axis=Axis.FORECAST_PERIOD,
                method=method,
                window_length=window,
                window_anchor=WindowAnchor.RIGHT,
                sampling_frequency=sampling,
            )
        ]


class GribProcessingContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(handler, context):
        component = handler.component

        # the inner (forecast period) time aggregation defines the GRIB step type/range;
        # fall back to the first time aggregation step if none operates on the period
        agg = None
        for step in component:
            if step.kind() == Kind.TIME_AGGREGATION:
                if step.axis() == Axis.FORECAST_PERIOD:
                    agg = step
                    break
                if agg is None:
                    agg = step

        if agg is None:
            context["stepType"] = "instant"
            return

        context["stepType"] = _METHOD_TO_STEPTYPE.get(agg.method(), "instant")
        window = agg.window_length(type="timedelta")
        if window is not None:
            context["stepRange"] = step_to_grib(window)


COLLECTOR = GribProcessingContextCollector()


class GribProcessing(GribFieldComponentHandler):
    BUILDER = GribProcessingBuilder
    COLLECTOR = COLLECTOR
