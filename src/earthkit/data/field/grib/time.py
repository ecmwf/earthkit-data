# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime as dt_module

from earthkit.data.utils.dates import datetime_from_grib, datetime_to_grib, step_to_grib, to_timedelta

from .collector import GribContextCollector
from .core import GribFieldComponentHandler

ZERO_TIMEDELTA = to_timedelta(0)

# Reference leap year for DOY <-> month/day conversions in daily climatology
_CLIMATOLOGY_REFERENCE_YEAR = 2000


def _day_of_year_from_month_day(month, day):
    """Convert month and day to day of year using a reference leap year."""
    ref_date = dt_module.date(_CLIMATOLOGY_REFERENCE_YEAR, int(month), int(day))
    return ref_date.timetuple().tm_yday


def _month_day_from_day_of_year(doy):
    """Convert day of year to (month, day) using a reference leap year."""
    ref_date = dt_module.date(_CLIMATOLOGY_REFERENCE_YEAR, 1, 1) + dt_module.timedelta(days=int(doy) - 1)
    return ref_date.month, ref_date.day


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

        data_date = _get("dataDate", None)

        # Daily climatology: dataDate is encoded as 100*month + day (e.g. 101 = Jan 1, 1231 = Dec 31)
        if data_date is not None and int(data_date) < 10000:
            month = int(data_date) // 100
            day = int(data_date) % 100
            doy = _day_of_year_from_month_day(month, day)
            return dict(day_of_year=doy)

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
        from earthkit.data.field.component.time import DailyClimatologyTime

        component = handler.component

        if isinstance(component, DailyClimatologyTime):
            # Convert DOY back to month/day encoded as 100*month + day for GRIB
            doy = component.day_of_year()
            if doy is not None:
                month, day = _month_day_from_day_of_year(doy)
                r = {}
                r["date"] = month * 100 + day
                r["time"] = 0
                r["step"] = 0
                context.update(r)
            return

        r = {}

        date, time = datetime_to_grib(component.base_datetime())
        step = step_to_grib(component.step())
        r["date"] = date
        r["time"] = time
        r["step"] = step

        if component.forecast_month() is not None:
            r["forecastMonth"] = component.forecast_month()
            if component.indexing_datetime() is not None:
                idate, itime = datetime_to_grib(component.indexing_datetime())
                r["indexingDate"] = idate
                r["indexingTime"] = itime

        context.update(r)


COLLECTOR = GribTimeContextCollector()


class GribTime(GribFieldComponentHandler):
    BUILDER = GribTimeBuilder
    COLLECTOR = COLLECTOR
