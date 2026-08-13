# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.field.component.time_span import TimeMethods
from earthkit.data.field.grib.time import ZERO_TIMEDELTA
from earthkit.data.utils.dates import step_to_grib, to_timedelta

from .collector import GribEncoderCollector, GribIndexerCollector, GribIndexerFieldKeysCollector, MultiCollector
from .core import GribFieldComponentHandler

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
        from earthkit.data.field.component.proc import Proc
        from earthkit.data.field.handler.proc import ProcFieldComponentHandler

        d = GribProcBuilder._build_dict(handle)
        component = Proc.from_dict(d)
        handler = ProcFieldComponentHandler.from_component(component)
        return handler

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


class GribProcEncoderCollector(GribEncoderCollector):
    @staticmethod
    def _collect(handler, context):
        from earthkit.data.field.component.proc import TimeProcItem

        component = handler.component

        time_item = None
        for item in component.items():
            if isinstance(item, TimeProcItem):
                time_item = item
                break
        if time_item is not None:
            method = _METHOD_TO_GRIB.get(time_item.method, "instant")
            context["stepType"] = method
            if time_item.method != TimeMethods.INSTANT:
                context["stepRange"] = step_to_grib(time_item.value)

    # @staticmethod
    # def collect_for_indexer(handler, context):
    #     keys = GribProcContextCollector.indexer_keys(handler)
    #     GribContextCollector._collect_keys(keys, handler, context)

    # @staticmethod
    # def indexer_keys(handler):
    #     return ["stepType", "stepRange"]

    # @staticmethod
    # @property
    # def all_indexer_keys():
    #     return ["stepType", "stepRange"]


class GribProcIndexerFieldKeysCollector(GribIndexerFieldKeysCollector):
    @staticmethod
    def _collect(handler, context):
        component = handler.component
        d = component.to_dict()
        for k, v in d.items():
            if v is not None:
                context[f"proc.{k}"] = v


class GribProcIndexerCollector(GribIndexerCollector):
    @staticmethod
    def _collect(handle, context):
        keys = GribProcIndexerCollector.indexer_keys()
        GribIndexerCollector._collect_keys(keys, handle, context)

    @staticmethod
    def indexer_keys():
        return ["stepType", "stepRange"]


COLLECTOR = MultiCollector(encoder=GribProcEncoderCollector(), indexer=GribProcIndexerFieldKeysCollector())
PROC_INDEXER_COLLECTOR = GribProcIndexerCollector()


class GribProc(GribFieldComponentHandler):
    BUILDER = GribProcBuilder
    COLLECTOR = COLLECTOR
