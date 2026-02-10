# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .component.parameter import BaseParameter
from .component.parameter import create_parameter
from .core import SimpleFieldComponentHandler


class ParameterFieldComponentHandler(SimpleFieldComponentHandler):
    """Parameter component of a field."""

    PART_CLS = BaseParameter
    PART_MAKER = create_parameter
    NAME = "parameter"

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.parameter import COLLECTOR

        COLLECTOR.collect(self, context)
