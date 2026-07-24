# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""GRIB-to-Processing component mapping.

Builds a processing chain from GRIB2 keys following PDT 4.8 (time statistics)
and PDT 4.2/4.3/4.4 (ensemble derived forecasts).

The mapping uses:
- ``derivedForecast`` (Code Table 4.7) + ``numberOfForecastsInEnsemble``
  → EnsembleProcessingItem (head of chain, outermost operation)
- ``typeOfStatisticalProcessing`` (Code Table 4.10),
  ``typeOfTimeIncrement`` (Code Table 4.11),
  ``indicatorOfUnitForTimeRange`` + ``lengthOfTimeRange``,
  ``indicatorOfUnitForTimeIncrement`` + ``timeIncrement``
  → chain of TimeProcessingItem's (outer to inner)
"""

from earthkit.data.field.component.duration import Duration
from earthkit.data.field.component.processing import (
    EnsembleProcessingItem,
    IncrementingType,
    Processing,
    ProcessingMethod,
    TimeProcessingItem,
)

from .collector import GribContextCollector
from .core import GribFieldComponentHandler

# ---------------------------------------------------------------------------
# Code Table 4.10: typeOfStatisticalProcessing → ProcessingMethod
# ---------------------------------------------------------------------------
_GRIB_STAT_PROCESS_TO_METHOD = {
    0: ProcessingMethod.MEAN,  # Average
    1: ProcessingMethod.SUM,  # Accumulation
    2: ProcessingMethod.MAXIMUM,  # Maximum
    3: ProcessingMethod.MINIMUM,  # Minimum
    # 4: Difference (end - start) — not mapped
    # 5: Root mean square — not mapped
    6: ProcessingMethod.STANDARD_DEVIATION,  # Standard deviation
    7: ProcessingMethod.VARIANCE,  # Covariance (temporal variance)
    # 8: Difference (start - end) — not mapped
    # 9: Ratio — not mapped
    # 10: Standardized anomaly — not mapped
    11: ProcessingMethod.SUM,  # Summation
    # 12: Return period — not mapped
    13: ProcessingMethod.MEDIAN,  # Median
}

# ---------------------------------------------------------------------------
# Code Table 4.7: derivedForecast → ProcessingMethod (ensemble statistics)
# ---------------------------------------------------------------------------
_GRIB_DERIVED_FORECAST_TO_METHOD = {
    0: ProcessingMethod.MEAN,  # Unweighted mean of all members
    1: ProcessingMethod.MEAN,  # Weighted mean of all members
    2: ProcessingMethod.STANDARD_DEVIATION,  # SD w.r.t. cluster mean
    3: ProcessingMethod.STANDARD_DEVIATION,  # SD w.r.t. cluster mean, normalized
    # 4: Spread of all members — not mapped to a simple method
    # 5: Large anomaly index — not mapped
    6: ProcessingMethod.MEAN,  # Unweighted mean of cluster members
    # 7: Interquartile range — not mapped
    8: ProcessingMethod.MINIMUM,  # Minimum of all ensemble members
    9: ProcessingMethod.MAXIMUM,  # Maximum of all ensemble members
    10: ProcessingMethod.VARIANCE,  # Variance of all ensemble members
}

# ---------------------------------------------------------------------------
# Code Table 4.11: typeOfTimeIncrement → IncrementingType
# ---------------------------------------------------------------------------
_GRIB_TYPE_OF_TIME_INCREMENT_TO_INCREMENTING = {
    1: IncrementingType.FORECAST_REFERENCE_TIME,
    2: IncrementingType.FORECAST_PERIOD,
}

_INCREMENTING_TO_GRIB_TYPE_OF_TIME_INCREMENT = {v: k for k, v in _GRIB_TYPE_OF_TIME_INCREMENT_TO_INCREMENTING.items()}

# ---------------------------------------------------------------------------
# Code Table 4.4: indicatorOfUnitOfTimeRange → Duration kwargs
# ---------------------------------------------------------------------------
_GRIB_TIME_UNIT_TO_DURATION_KWARGS = {
    0: "minutes",  # Minute
    1: "hours",  # Hour
    2: "days",  # Day
    3: "months",  # Month
    4: "years",  # Year
    5: "years",  # Decade (multiply by 10)
    6: "years",  # Normal (multiply by 30)
    7: "years",  # Century (multiply by 100)
    10: "hours",  # 3 hours (multiply by 3)
    11: "hours",  # 6 hours (multiply by 6)
    12: "hours",  # 12 hours (multiply by 12)
    13: "seconds",  # Second
}

_GRIB_TIME_UNIT_MULTIPLIER = {
    0: 1,
    1: 1,
    2: 1,
    3: 1,
    4: 1,
    5: 10,
    6: 30,
    7: 100,
    10: 3,
    11: 6,
    12: 12,
    13: 1,
}

# Legacy stepType-based mapping (fallback for GRIB1 or simple cases)
_GRIB_STEP_TYPE_TO_METHOD = {
    "accum": ProcessingMethod.SUM,
    "avg": ProcessingMethod.MEAN,
    "instant": ProcessingMethod.POINT,
    "max": ProcessingMethod.MAXIMUM,
    "min": ProcessingMethod.MINIMUM,
}

_METHOD_TO_GRIB_STEP_TYPE = {v: k for k, v in _GRIB_STEP_TYPE_TO_METHOD.items()}


def _grib_time_unit_to_duration(unit_indicator, length):
    """Convert GRIB time unit indicator + length to an ISO 8601 duration string.

    Parameters
    ----------
    unit_indicator : int
        GRIB Code Table 4.4 value.
    length : int
        Number of time units.

    Returns
    -------
    str or None
        ISO 8601 duration string, or None if the unit is unknown or length is 0/missing.
    """
    if unit_indicator is None or length is None or length == 0:
        return None
    if unit_indicator == 255:  # Missing
        return None

    kwarg_name = _GRIB_TIME_UNIT_TO_DURATION_KWARGS.get(unit_indicator)
    if kwarg_name is None:
        return None

    multiplier = _GRIB_TIME_UNIT_MULTIPLIER.get(unit_indicator, 1)
    value = length * multiplier

    d = Duration(**{kwarg_name: value})
    return d.to_iso_string()


def _ensure_list(value):
    """Ensure value is a list (GRIB keys may be scalar, list, tuple, or numpy array)."""
    if value is None:
        return []
    # Handle lists, tuples, numpy arrays and other array-like objects with __iter__ and __len__, except for strings
    if not isinstance(value, str) and hasattr(value, "__iter__") and hasattr(value, "__len__"):
        return list(value)
    return [value]


class GribProcessingBuilder:
    """Builds a Processing component from GRIB handle keys."""

    @staticmethod
    def build(handle):
        from earthkit.data.field.handler.processing import ProcessingFieldComponentHandler

        component = GribProcessingBuilder._build_component(handle)
        handler = ProcessingFieldComponentHandler.from_component(component)
        return handler

    @staticmethod
    def _build_component(handle):
        """Build a Processing component from GRIB handle.

        Strategy:
        1. Try GRIB2 PDT 4.8 keys (typeOfStatisticalProcessing, etc.)
           → builds a TimeProcessingItem chain (outer to inner) via recursion.
        2. Check derivedForecast → EnsembleProcessingItem pushed at the head.
        3. Fallback to legacy stepType-based detection.

        Returns
        -------
        Processing or EmptyProcessing
        """
        # ------------------------------------------------------------------
        # Step 1: Build TimeProcessingItem chain from PDT 4.8 keys
        # ------------------------------------------------------------------
        component = GribProcessingBuilder._build_time_chain(handle)

        # ------------------------------------------------------------------
        # Step 2: Check for ensemble derived forecast (Code Table 4.7)
        # ------------------------------------------------------------------
        ensemble_dict = GribProcessingBuilder._build_ensemble_dict(handle)
        if ensemble_dict is not None:
            if component is not None:
                # Push ensemble at head; time chain becomes its next
                component = component.push(ensemble_dict)
            else:
                component = Processing.from_dict(ensemble_dict)

        if component is not None:
            return component

        # ------------------------------------------------------------------
        # Fallback: legacy stepType-based detection
        # ------------------------------------------------------------------
        return GribProcessingBuilder._build_legacy(handle)

    @staticmethod
    def _build_time_chain(handle, index=0, lists=None):
        """Build TimeProcessingItem chain from GRIB2 PDT 4.8 repeated keys.

        Uses recursion: builds the innermost item first, then wraps each
        outer item using :meth:`Processing.push`.

        Parameters
        ----------
        handle : GRIB handle
        index : int
            Current index into the arrays (0 = outermost).
        lists : dict or None
            Pre-fetched arrays of GRIB keys. Built on first call.

        Returns
        -------
        Processing or None
            Processing component for the chain starting at ``index``,
            or None if no valid items found.
        """
        if lists is None:

            def _get(key, default=None):
                return handle.get(key, default=default)

            stat_proc = _get("typeOfStatisticalProcessing")
            if stat_proc is None:
                return None

            lists = {
                "stat_proc": _ensure_list(stat_proc),
                "type_inc": _ensure_list(_get("typeOfTimeIncrement")),
                "unit_range": _ensure_list(_get("indicatorOfUnitForTimeRange")),
                "len_range": _ensure_list(_get("lengthOfTimeRange")),
                "unit_inc": _ensure_list(_get("indicatorOfUnitForTimeIncrement")),
                "time_inc": _ensure_list(_get("timeIncrement")),
            }

        n = len(lists["stat_proc"])
        if index >= n:
            return None

        def _safe_get(key, idx):
            lst = lists[key]
            if idx >= len(lst):
                return None
            return lst[idx]

        # Recurse to build the inner (next) part of the chain first
        inner = GribProcessingBuilder._build_time_chain(handle, index + 1, lists)

        # Build the item dict for the current index
        sp = _safe_get("stat_proc", index)
        method = _GRIB_STAT_PROCESS_TO_METHOD.get(sp)
        if method is None:
            # Unknown statistical process code — skip this level, return inner
            return inner

        # typeOfTimeIncrement → incrementing
        type_inc = _safe_get("type_inc", index)
        incrementing = None
        if type_inc is not None:
            inc_enum = _GRIB_TYPE_OF_TIME_INCREMENT_TO_INCREMENTING.get(type_inc)
            if inc_enum is not None:
                incrementing = inc_enum.value
            else:
                incrementing = IncrementingType.FORECAST_PERIOD.value

        # window_length
        window_length = _grib_time_unit_to_duration(_safe_get("unit_range", index), _safe_get("len_range", index))

        # sampling_frequency
        sampling_frequency = _grib_time_unit_to_duration(_safe_get("unit_inc", index), _safe_get("time_inc", index))

        item_dict = {"kind": "time_processing", "method": method.value}
        if window_length is not None:
            item_dict["window_length"] = window_length
        if sampling_frequency is not None:
            item_dict["sampling_frequency"] = sampling_frequency
        if incrementing is not None:
            item_dict["incrementing"] = incrementing

        # Push current item at head of inner chain (or create new if inner is None)
        if inner is not None:
            return inner.push(item_dict)
        else:
            return Processing.from_dict(item_dict)

    @staticmethod
    def _build_ensemble_dict(handle):
        """Build EnsembleProcessingItem dict from derivedForecast key.

        Returns
        -------
        dict or None
        """

        def _get(key, default=None):
            return handle.get(key, default=default)

        derived_forecast = _get("derivedForecast")
        if derived_forecast is None:
            return None

        # derivedForecast is a Code Table 4.7 integer
        if isinstance(derived_forecast, (list, tuple)):
            derived_forecast = derived_forecast[0]

        method = _GRIB_DERIVED_FORECAST_TO_METHOD.get(derived_forecast)
        if method is None:
            # Unknown derived forecast code — cannot map
            return None

        ensemble_size = _get("numberOfForecastsInEnsemble", 0)
        if ensemble_size is None:
            ensemble_size = 0

        return {
            "kind": "ensemble_statistics",
            "method": method.value,
            "ensemble_size": int(ensemble_size),
        }

    @staticmethod
    def _build_legacy(handle):
        """Fallback: build from stepType (GRIB1 or simple GRIB2 without PDT 4.8).

        Returns
        -------
        dict or None
        """
        from earthkit.data.field.grib.time import ZERO_TIMEDELTA
        from earthkit.data.utils.dates import to_timedelta

        def _get(key, default=None):
            return handle.get(key, default=default)

        time_span_method = _get("stepType", "instant")
        if time_span_method is None:
            time_span_method = "instant"
        time_span_method = time_span_method.lower()

        proc_method = _GRIB_STEP_TYPE_TO_METHOD.get(time_span_method, ProcessingMethod.POINT)

        window_length = None
        if proc_method != ProcessingMethod.POINT:
            end = _get("endStep")
            if end is None:
                end = _get("step")

            if end is not None:
                end = to_timedelta(end)
                start = _get("startStep")
                if start is not None:
                    start = to_timedelta(start)
                    td = end - start
                    if td != ZERO_TIMEDELTA:
                        window_length = Duration.from_timedelta(td).to_iso_string()

        # For instantaneous fields, return a point processing item
        incrementing = None
        if proc_method != ProcessingMethod.POINT:
            type_of_time_interval = _get("typeOfTimeInterval")
            if type_of_time_interval is not None:
                inc = _GRIB_TYPE_OF_TIME_INCREMENT_TO_INCREMENTING.get(type_of_time_interval)
                if inc is not None:
                    incrementing = inc.value
            if incrementing is None:
                incrementing = IncrementingType.FORECAST_PERIOD.value

        d = {
            "kind": "time_processing",
            "method": proc_method.value,
        }
        if window_length is not None:
            d["window_length"] = window_length
        if incrementing is not None:
            d["incrementing"] = incrementing
        return Processing.from_dict(d)


class GribProcessingContextCollector(GribContextCollector):
    """Collects GRIB keys from a Processing component for encoding."""

    @staticmethod
    def collect_keys(handler, context):
        component = handler.component

        time_item = None
        ensemble_item = None
        for item in component:
            if isinstance(item, TimeProcessingItem) and time_item is None:
                time_item = item
            if isinstance(item, EnsembleProcessingItem) and ensemble_item is None:
                ensemble_item = item

        if time_item is not None:
            method = _METHOD_TO_GRIB_STEP_TYPE.get(time_item.method(), "instant")
            context["stepType"] = method
            if time_item.method() != ProcessingMethod.POINT:
                if time_item.window_length() is not None:
                    context["stepRange"] = time_item.window_length().to_timedelta()
                if time_item.incrementing() is not None:
                    grib_type = _INCREMENTING_TO_GRIB_TYPE_OF_TIME_INCREMENT.get(time_item.incrementing())
                    if grib_type is not None:
                        context["typeOfTimeIncrement"] = grib_type

        if ensemble_item is not None:
            # Reverse lookup for derivedForecast
            for code, m in _GRIB_DERIVED_FORECAST_TO_METHOD.items():
                if m == ensemble_item.method():
                    context["derivedForecast"] = code
                    break
            context["numberOfForecastsInEnsemble"] = ensemble_item.ensemble_size()


COLLECTOR = GribProcessingContextCollector()


class GribProcessing(GribFieldComponentHandler):
    BUILDER = GribProcessingBuilder
    COLLECTOR = COLLECTOR
