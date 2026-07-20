# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.field.component.processing import (
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
                }
            ]
        }


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


COLLECTOR = GribProcessingContextCollector()


class GribProcessing(GribFieldComponentHandler):
    BUILDER = GribProcessingBuilder
    COLLECTOR = COLLECTOR
