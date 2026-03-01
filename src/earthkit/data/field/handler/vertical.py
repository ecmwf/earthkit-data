# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.field.component.vertical import BaseVertical
from earthkit.data.field.component.vertical import EmptyVertical
from earthkit.data.field.component.vertical import create_vertical

from .core import SimpleFieldComponentHandler


class VerticalFieldComponentHandler(SimpleFieldComponentHandler):
    """Vertical component handler of a field."""

    COMPONENT_CLS = BaseVertical
    COMPONENT_MAKER = create_vertical
    NAME = "vertical"

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.vertical import COLLECTOR

        COLLECTOR.collect(self, context)

    @classmethod
    def create_empty(cls) -> "VerticalFieldComponentHandler":
        return EMPTY_VERTICAL_HANDLER


EMPTY_VERTICAL_HANDLER = VerticalFieldComponentHandler(EmptyVertical())
