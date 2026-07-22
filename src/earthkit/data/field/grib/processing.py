# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.field.component.processing import (
    IncrementingType,
    Processing,
    ProcessingMethod,
    TimeProcessingItem,
)
from earthkit.data.field.grib.time import ZERO_TIMEDELTA
from earthkit.data.utils.dates import to_timedelta

from .collector import GribContextCollector
from .core import GribFieldComponentHandler

_GRIB_TO_METHOD = {
    "accum": ProcessingMethod.SUM,
    "avg": ProcessingMethod.MEAN,
    "instant": ProcessingMethod.POINT,
    "max": ProcessingMethod.MAXIMUM,
}

_METHOD_TO_GRIB = {v: k for k, v in _GRIB_TO_METHOD.items()}

# GRIB typeOfTimeInterval mapping
# 1 = successive times have same forecast period, different reference times
# 2 = successive times have same reference time, different forecast periods
_GRIB_TYPE_OF_TIME_INTERVAL_TO_INCREMENTING = {
    1: IncrementingType.FORECAST_REFERENCE_TIME,
    2: IncrementingType.FORECAST_PERIOD,
}

_INCREMENTING_TO_GRIB_TYPE_OF_TIME_INTERVAL = {v: k for k, v in _GRIB_TYPE_OF_TIME_INTERVAL_TO_INCREMENTING.items()}


class GribProcessingBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.handler.processing import ProcessingFieldComponentHandler

        d = GribProcessingBuilder._build_dict(handle)
        component = Processing.from_dict(d)
        handler = ProcessingFieldComponentHandler.from_component(component)
        return handler

    @staticmethod
    def _build_dict(handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        time_span_method = _get("stepType", "instant").lower()
        proc_method = _GRIB_TO_METHOD.get(time_span_method, ProcessingMethod.POINT)

        window_length = None
        if proc_method != ProcessingMethod.POINT:
            end = _get("endStep")
            if end is None:
                end = _get("step")

            if end is None:
                window_length = None
            else:
                end = to_timedelta(end)
                start = _get("startStep")
                if start is not None:
                    start = to_timedelta(start)
                    td = end - start
                    if td != ZERO_TIMEDELTA:
                        from earthkit.data.field.component.duration import Duration

                        window_length = Duration.from_timedelta(td).to_iso_string()

        return {
            "items": [
                {
                    "kind": "time_processing",
                    "method": proc_method.value,
                    "window_length": window_length,
                    "incrementing": _get_incrementing(handle, proc_method),
                }
            ]
        }


def _get_incrementing(handle, proc_method):
    """Determine the incrementing type from GRIB typeOfTimeInterval.

    Returns the string value of the IncrementingType enum, or None for
    point (instantaneous) fields.
    """
    if proc_method == ProcessingMethod.POINT:
        return None

    type_of_time_interval = handle.get("typeOfTimeInterval", default=None)
    if type_of_time_interval is not None:
        inc = _GRIB_TYPE_OF_TIME_INTERVAL_TO_INCREMENTING.get(type_of_time_interval)
        if inc is not None:
            return inc.value

    # Default: forecast_period (typeOfTimeInterval=2 semantics)
    return IncrementingType.FORECAST_PERIOD.value


class GribProcessingContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(handler, context):
        component = handler.component

        time_item = None
        for item in component.items():
            if isinstance(item, TimeProcessingItem):
                time_item = item
                break
        if time_item is not None:
            method = _METHOD_TO_GRIB.get(time_item.method, "instant")
            context["stepType"] = method
            if time_item.method != ProcessingMethod.POINT:
                if time_item.window_length is not None:
                    context["stepRange"] = time_item.window_length.to_timedelta()
                if time_item.incrementing is not None:
                    grib_type = _INCREMENTING_TO_GRIB_TYPE_OF_TIME_INTERVAL.get(time_item.incrementing)
                    if grib_type is not None:
                        context["typeOfTimeInterval"] = grib_type


COLLECTOR = GribProcessingContextCollector()


class GribProcessing(GribFieldComponentHandler):
    BUILDER = GribProcessingBuilder
    COLLECTOR = COLLECTOR
