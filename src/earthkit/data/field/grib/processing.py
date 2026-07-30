# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""GRIB-to-Processing component mapping.

Builds a :class:`~earthkit.data.field.component.processing.Processing` component
from GRIB2 keys following PDT 4.8 (time statistics) and PDT 4.2/4.3/4.4
(ensemble derived forecasts).

The mapping uses:

- ``derivedForecast`` (Code Table 4.7) + ``numberOfForecastsInEnsemble``
  → :class:`EnsembleProcessingItem` (prepended at head of item tuple)
- ``typeOfStatisticalProcessing`` (Code Table 4.10),
  ``typeOfTimeIncrement`` (Code Table 4.11),
  ``indicatorOfUnitForTimeRange`` + ``lengthOfTimeRange``,
  ``indicatorOfUnitForTimeIncrement`` + ``timeIncrement``
  → chain of :class:`TimeProcessingItem` (outer to inner in the tuple)
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
    0: ProcessingMethod.MEAN,
    1: ProcessingMethod.SUM,
    2: ProcessingMethod.MAXIMUM,
    3: ProcessingMethod.MINIMUM,
    6: ProcessingMethod.STANDARD_DEVIATION,
    7: ProcessingMethod.VARIANCE,
    11: ProcessingMethod.SUM,
    13: ProcessingMethod.MEDIAN,
}

# ---------------------------------------------------------------------------
# Code Table 4.7: derivedForecast → ProcessingMethod (ensemble statistics)
# ---------------------------------------------------------------------------
_GRIB_DERIVED_FORECAST_TO_METHOD = {
    0: ProcessingMethod.MEAN,
    1: ProcessingMethod.MEAN,
    2: ProcessingMethod.STANDARD_DEVIATION,
    3: ProcessingMethod.STANDARD_DEVIATION,
    6: ProcessingMethod.MEAN,
    8: ProcessingMethod.MINIMUM,
    9: ProcessingMethod.MAXIMUM,
    10: ProcessingMethod.VARIANCE,
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
    0: "minutes",
    1: "hours",
    2: "days",
    3: "months",
    4: "years",
    5: "years",
    6: "years",
    7: "years",
    10: "hours",
    11: "hours",
    12: "hours",
    13: "seconds",
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
    """Convert GRIB time unit indicator + length to an ISO 8601 duration string."""
    if unit_indicator is None or length is None or length == 0:
        return None
    if unit_indicator == 255:
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
    if isinstance(value, str):
        return [value]
    if isinstance(value, (list, tuple)):
        return list(value)
    if hasattr(value, "__iter__") and hasattr(value, "__len__"):
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

        Returns
        -------
        Processing
        """
        items = []

        # ------------------------------------------------------------------
        # Step 1: Check for ensemble derived forecast (Code Table 4.7)
        # Ensemble item is prepended at the head (outermost operation).
        # ------------------------------------------------------------------
        ensemble_item = GribProcessingBuilder._build_ensemble_item(handle)
        if ensemble_item is not None:
            items.append(ensemble_item)

        # ------------------------------------------------------------------
        # Step 2: Build TimeProcessingItem list from PDT 4.8 keys
        # ------------------------------------------------------------------
        time_items = GribProcessingBuilder._build_time_items(handle)
        if time_items:
            items.extend(time_items)

        if items:
            return Processing(tuple(items))

        # ------------------------------------------------------------------
        # Fallback: legacy stepType-based detection
        # ------------------------------------------------------------------
        return GribProcessingBuilder._build_legacy(handle)

    @staticmethod
    def _build_time_items(handle):
        """Build a list of TimeProcessingItems from GRIB2 PDT 4.8 repeated keys.

        Returns
        -------
        list of TimeProcessingItem or empty list
        """

        def _get(key, default=None):
            return handle.get(key, default=default)

        stat_proc = _get("typeOfStatisticalProcessing")
        if stat_proc is None:
            return []

        stat_proc_list = _ensure_list(stat_proc)
        type_of_time_inc_list = _ensure_list(_get("typeOfTimeIncrement"))
        unit_for_range_list = _ensure_list(_get("indicatorOfUnitForTimeRange"))
        length_of_range_list = _ensure_list(_get("lengthOfTimeRange"))
        unit_for_inc_list = _ensure_list(_get("indicatorOfUnitForTimeIncrement"))
        time_inc_list = _ensure_list(_get("timeIncrement"))

        n = len(stat_proc_list)

        def _safe_get(lst, idx):
            if idx >= len(lst):
                return None
            return lst[idx]

        items = []
        for i in range(n):
            sp = stat_proc_list[i]
            method = _GRIB_STAT_PROCESS_TO_METHOD.get(sp)
            if method is None:
                continue

            type_inc = _safe_get(type_of_time_inc_list, i)
            incrementing = None
            if type_inc is not None:
                inc_enum = _GRIB_TYPE_OF_TIME_INCREMENT_TO_INCREMENTING.get(type_inc)
                if inc_enum is not None:
                    incrementing = inc_enum.value
                else:
                    incrementing = IncrementingType.FORECAST_PERIOD.value

            window_length = _grib_time_unit_to_duration(
                _safe_get(unit_for_range_list, i), _safe_get(length_of_range_list, i)
            )
            sampling_frequency = _grib_time_unit_to_duration(
                _safe_get(unit_for_inc_list, i), _safe_get(time_inc_list, i)
            )

            item = TimeProcessingItem(
                method=method,
                window_length=window_length,
                sampling_frequency=sampling_frequency,
                incrementing=incrementing,
            )
            items.append(item)

        return items

    @staticmethod
    def _build_ensemble_item(handle):
        """Build an EnsembleProcessingItem from derivedForecast key.

        Returns
        -------
        EnsembleProcessingItem or None
        """

        def _get(key, default=None):
            return handle.get(key, default=default)

        derived_forecast = _get("derivedForecast")
        if derived_forecast is None:
            return None

        if isinstance(derived_forecast, (list, tuple)):
            derived_forecast = derived_forecast[0]

        method = _GRIB_DERIVED_FORECAST_TO_METHOD.get(derived_forecast)
        if method is None:
            return None

        ensemble_size = _get("numberOfForecastsInEnsemble", 0)
        if ensemble_size is None:
            ensemble_size = 0

        return EnsembleProcessingItem(method=method, ensemble_size=int(ensemble_size))

    @staticmethod
    def _build_legacy(handle):
        """Fallback: build from stepType (GRIB1 or simple GRIB2 without PDT 4.8).

        Returns
        -------
        Processing
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

        incrementing = None
        if proc_method != ProcessingMethod.POINT:
            type_of_time_interval = _get("typeOfTimeInterval")
            if type_of_time_interval is not None:
                inc = _GRIB_TYPE_OF_TIME_INCREMENT_TO_INCREMENTING.get(type_of_time_interval)
                if inc is not None:
                    incrementing = inc.value
            if incrementing is None:
                incrementing = IncrementingType.FORECAST_PERIOD.value

        item = TimeProcessingItem(
            method=proc_method,
            window_length=window_length,
            incrementing=incrementing,
        )
        return Processing((item,))


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
            for code, m in _GRIB_DERIVED_FORECAST_TO_METHOD.items():
                if m == ensemble_item.method():
                    context["derivedForecast"] = code
                    break
            context["numberOfForecastsInEnsemble"] = ensemble_item.ensemble_size()


COLLECTOR = GribProcessingContextCollector()


class GribProcessing(GribFieldComponentHandler):
    BUILDER = GribProcessingBuilder
    COLLECTOR = COLLECTOR
