# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.field.component.processing import Axis, Kind, Method, WindowAnchor
from earthkit.data.field.grib.time import ZERO_TIMEDELTA
from earthkit.data.utils.dates import step_to_grib, to_timedelta

from .collector import GribContextCollector
from .core import GribFieldComponentHandler

# mapping between the GRIB stepType and the processing step method
_GRIB_TO_METHOD = {
    "accum": Method.SUM,
    "avg": Method.MEAN,
    "max": Method.MAXIMUM,
    "min": Method.MINIMUM,
}

_METHOD_TO_GRIB = {v: k for k, v in _GRIB_TO_METHOD.items()}

# GRIB stepTypes that denote an instantaneous (non-processed) field
_INSTANT = "instant"


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
        def _get(key, default=None):
            return handle.get(key, default=default)

        grib_step_type = str(_get("stepType", _INSTANT)).lower()
        method = _GRIB_TO_METHOD.get(grib_step_type)

        # instantaneous field: no processing step
        if method is None:
            return []

        # determine the length of the aggregation window from the step range
        end = _get("endStep")
        if end is None:
            end = _get("step")

        window = ZERO_TIMEDELTA
        if end is not None:
            end = to_timedelta(end)
            start = _get("startStep")
            if start is not None:
                start = to_timedelta(start)
                window = end - start
            else:
                window = end

        return [
            {
                "kind": Kind.TIME_AGGREGATION,
                "axis": Axis.FORECAST_PERIOD,
                "method": method,
                "window_length": window,
                "window_anchor": WindowAnchor.RIGHT,
                "sampling_frequency": ZERO_TIMEDELTA,
            }
        ]


class GribProcessingContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(handler, context):
        from earthkit.data.field.component.processing import Kind as _Kind

        component = handler.component

        # find the outermost time aggregation step (if any)
        agg = None
        for step in component:
            if step.kind() == _Kind.TIME_AGGREGATION:
                agg = step
                break

        if agg is None:
            context["stepType"] = _INSTANT
            return

        context["stepType"] = _METHOD_TO_GRIB.get(agg.method(), _INSTANT)
        window = agg.window_length(type="timedelta")
        if window is not None:
            context["stepRange"] = step_to_grib(window)


COLLECTOR = GribProcessingContextCollector()


class GribProcessing(GribFieldComponentHandler):
    BUILDER = GribProcessingBuilder
    COLLECTOR = COLLECTOR
