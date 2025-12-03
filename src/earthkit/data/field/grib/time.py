# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.utils.dates import datetime_from_grib
from earthkit.data.utils.dates import datetime_to_grib
from earthkit.data.utils.dates import step_to_grib
from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.dates import to_timedelta

from ..spec.time_span import TimeSpanMethod
from .collector import GribContextCollector
from .core import GribFieldMember

ZERO_TIMEDELTA = to_timedelta(0)

_GRIB_TO_METHOD = {
    "accum": TimeSpanMethod.ACCUMULATED,
    "avg": TimeSpanMethod.AVERAGE,
    "instant": TimeSpanMethod.INSTANT,
    "max": TimeSpanMethod.MAX,
}

_METHOD_TO_GRIB = {v: k for k, v in _GRIB_TO_METHOD.items()}


class GribTimeBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.time import TimeFieldMember

        d = GribTimeBuilder._build_dict(handle)
        r = TimeFieldMember.from_dict(d)
        # r._set_private_data("handle", handle)
        return r

    @staticmethod
    def _build_dict(handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        def _datetime(date_key, time_key):
            date = _get(date_key, None)
            if date is not None:
                time = _get(time_key, None)
                if time is not None:
                    return datetime_from_grib(date, time)
            return None

        hdate = _get("hdate")
        if hdate is not None:
            time = _get("dataTime")
            base = datetime_from_grib(hdate, time)
        else:
            base = _datetime("dataDate", "dataTime")

        end = None
        # time_span = ZERO_TIMEDELTA

        end = _get("endStep")
        if end is None:
            end = _get("step")

        if end is None:
            end = ZERO_TIMEDELTA
        else:
            end = to_timedelta(end)
            # start = _get("startStep")
            # if start is not None:
            #     start = to_timedelta(start)
            #     time_span = end - start

        # indexing = _datetime("indexingDate", "indexingTime")
        # reference = _datetime("referenceDate", "referenceTime")

        # time_span_method = _get("stepType", "instant").lower()
        # time_span_method = _GRIB_TO_METHOD.get(time_span_method, TimeSpanMethod.INSTANT)
        # time_span = TimeSpan(time_span, time_span_method)

        return dict(
            base_datetime=to_datetime(base),
            step=end,
            # time_span=time_span,
            # indexing_datetime=indexing,
            # reference_datetime=reference,
        )


class GribTimeContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(spec, context):
        r = {}

        date, time = datetime_to_grib(spec.base_datetime)
        step = step_to_grib(spec.step)
        r["date"] = date
        r["time"] = time
        r["step"] = step

        # if spec.time_span.value != ZERO_TIMEDELTA:
        #     start = spec.step - spec.time_span.value
        #     start = step_to_grib(start)
        #     end = step
        #     r["stepRange"] = step_range_to_grib(start, end)
        # else:
        #     r["stepRange"] = str(step)

        # r["stepType"] = _METHOD_TO_GRIB[spec.time_span.method]
        context.update(r)


COLLECTOR = GribTimeContextCollector()


class GribTime(GribFieldMember):
    BUILDER = GribTimeBuilder
    COLLECTOR = COLLECTOR
