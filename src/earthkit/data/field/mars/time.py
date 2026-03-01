# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.utils.dates import datetime_from_grib


class MarsTimeBuilder:
    @staticmethod
    def build(request, build_empty=False):
        from earthkit.data.field.component.time import create_time
        from earthkit.data.field.handler.time import TimeFieldComponentHandler

        d = MarsTimeBuilder._build_dict(request)
        if not d and not build_empty:
            return None

        component = create_time(d)
        handler = TimeFieldComponentHandler.from_component(component)
        return handler

    @staticmethod
    def _build_dict(request):
        base_date = request.get("date", None)
        base_time = request.get("time", None)

        step = request.get("step", 0)

        hdate = request.get("hdate", None)
        if hdate is not None:
            base_date = hdate

        base_datetime = datetime_from_grib(base_date, base_time)

        return dict(
            base_datetime=base_datetime,
            step=step,
        )
