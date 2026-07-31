# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.field.component.time import EmptyTime, TimeBase, create_time

from .core import SimpleFieldComponentHandler


class TimeFieldComponentHandler(SimpleFieldComponentHandler):
    """Time component of a field."""

    COMPONENT_CLS = TimeBase
    COMPONENT_MAKER = create_time
    NAME = "time"

    def get_grib_context(self, context) -> None:
        from earthkit.data.field.grib.time import COLLECTOR

        COLLECTOR.collect(self, context)

    @classmethod
    def from_component(cls, component: TimeBase) -> "TimeFieldComponentHandler":
        return TimeFieldComponentHandler(component)

    @classmethod
    def create_empty(cls) -> "TimeFieldComponentHandler":
        return EMPTY_TIME_HANDLER

    def _serialise(self):
        return {f"{self.NAME}.{k}": v for k, v in self.component.to_dict().items() if v is not None}


EMPTY_TIME_HANDLER = TimeFieldComponentHandler(EmptyTime())
