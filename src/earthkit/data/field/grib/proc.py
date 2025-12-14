# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.field.grib.time import ZERO_TIMEDELTA
from earthkit.data.field.spec.time_span import TimeMethods
from earthkit.data.utils.dates import to_timedelta

from .collector import GribContextCollector
from .core import GribFieldPart

_GRIB_TO_METHOD = {
    "accum": TimeMethods.ACCUMULATED,
    "avg": TimeMethods.AVERAGE,
    "instant": TimeMethods.INSTANT,
    "max": TimeMethods.MAX,
}

_METHOD_TO_GRIB = {v: k for k, v in _GRIB_TO_METHOD.items()}


class GribProcBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.proc import ProcFieldPart

        d = GribProcBuilder._build_dict(handle)
        spec = ProcFieldPart.from_dict(d)
        return spec

    @staticmethod
    def _build_dict(handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        time_span_method = _get("stepType", "instant").lower()
        time_span_method = _GRIB_TO_METHOD.get(time_span_method, TimeMethods.INSTANT)

        time_span = ZERO_TIMEDELTA
        if time_span_method != TimeMethods.INSTANT:
            end = _get("endStep")
            if end is None:
                end = _get("step")

            if end is None:
                end = ZERO_TIMEDELTA
            else:
                end = to_timedelta(end)
                start = _get("startStep")
                if start is not None:
                    start = to_timedelta(start)
                    time_span = end - start

        return {
            "time": {
                "value": time_span,
                "method": time_span_method,
            }
        }


class GribProcContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(spec, context):
        from earthkit.data.field.proc import TimeProcItem

        time_item = None
        for item in spec.items:
            if isinstance(item, TimeProcItem):
                time_item = item
                break
        if time_item is not None:
            method = _METHOD_TO_GRIB.get(time_item.method, "instant")
            context["stepType"] = method
            if time_item.method != TimeMethods.INSTANT:
                context["stepRange"] = time_item.value


COLLECTOR = GribProcContextCollector()


class GribProc(GribFieldPart):
    BUILDER = GribProcBuilder
    COLLECTOR = COLLECTOR
