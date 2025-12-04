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
from .core import GribFieldMember

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
        from earthkit.data.field.proc import ProcFieldMember

        d = GribProcBuilder._build_dict(handle)
        print("GribProcBuilder.build:", d)
        spec = ProcFieldMember.from_dict(d)
        # spec._set_private_data("handle", handle)
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
        r = {
            "perturbationNumber": spec.member,
        }
        context.update(r)


COLLECTOR = GribProcContextCollector()


class GribProc(GribFieldMember):
    BUILDER = GribProcBuilder
    COLLECTOR = COLLECTOR
