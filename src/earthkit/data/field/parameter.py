# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .core import SimpleFieldPartHandler
from .part.parameter import BaseParameter
from .part.parameter import create_parameter


class ParameterFieldPartHandler(SimpleFieldPartHandler):
    """Parameter part of a field."""

    PART_CLS = BaseParameter
    PART_MAKER = create_parameter
    NAME = "parameter"
    NAMESPACE_KEYS = ("variable", "units")

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.parameter import COLLECTOR

        COLLECTOR.collect(self, context)
