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
from earthkit.data.utils.dates import to_timedelta

from .collector import GribContextCollector
from .core import GribFieldComponentHandler

ZERO_TIMEDELTA = to_timedelta(0)


class GribTimeBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.handler.time import TimeFieldComponentHandler

        d = GribTimeBuilder._build_dict(handle)
        r = TimeFieldComponentHandler.from_dict(d)
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

        base = _datetime("dataDate", "dataTime")

        end = _get("endStep")
        if end is None:
            end = _get("step")

        if end is None:
            end = ZERO_TIMEDELTA
        else:
            end = to_timedelta(end)

        r = dict(
            base_datetime=base,
            step=end,
        )

        fc_month = None
        indexing = None
        if handle.is_defined("forecastMonth"):
            fc_month = _get("forecastMonth")
            if fc_month is not None:
                indexing = _datetime("indexingDate", "indexingTime")
                r["forecast_month"] = fc_month
                r["indexing_datetime"] = indexing

        return r


class GribTimeContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(handler, context):
        component = handler.component
        r = {}

        date, time = datetime_to_grib(component.base_datetime())
        step = step_to_grib(component.step())
        r["date"] = date
        r["time"] = time
        r["step"] = step

        if component.forecast_month is not None:
            r["forecastMonth"] = component.forecast_month
            if component.indexing_datetime is not None:
                idate, itime = datetime_to_grib(component.indexing_datetime)
                r["indexingDate"] = idate
                r["indexingTime"] = itime

        context.update(r)


COLLECTOR = GribTimeContextCollector()


class GribTime(GribFieldComponentHandler):
    BUILDER = GribTimeBuilder
    COLLECTOR = COLLECTOR
