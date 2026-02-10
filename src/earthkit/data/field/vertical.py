# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .component.vertical import BaseVertical
from .component.vertical import create_vertical
from .core import SimpleFieldComponentHandler


class VerticalFieldComponentHandler(SimpleFieldComponentHandler):
    """Vertical component handler of a field."""

    PART_CLS = BaseVertical
    PART_MAKER = create_vertical
    NAME = "vertical"

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.vertical import COLLECTOR

        COLLECTOR.collect(self, context)
