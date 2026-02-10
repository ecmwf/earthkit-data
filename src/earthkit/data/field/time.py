# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .component.time import BaseTime
from .component.time import create_time
from .core import SimpleFieldComponentHandler


class TimeFieldComponentHandler(SimpleFieldComponentHandler):
    """Time component of a field."""

    PART_CLS = BaseTime
    PART_MAKER = create_time
    NAME = "time"

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.time import COLLECTOR

        COLLECTOR.collect(self, context)
