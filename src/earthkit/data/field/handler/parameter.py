# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.field.component.parameter import BaseParameter
from earthkit.data.field.component.parameter import EmptyParameter
from earthkit.data.field.component.parameter import create_parameter

from .core import SimpleFieldComponentHandler


class ParameterFieldComponentHandler(SimpleFieldComponentHandler):
    """Parameter component of a field."""

    COMPONENT_CLS = BaseParameter
    COMPONENT_MAKER = create_parameter
    NAME = "parameter"

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.parameter import COLLECTOR

        COLLECTOR.collect(self, context)

    @classmethod
    def create_empty(cls) -> "ParameterFieldComponentHandler":
        return EMPTY_PARAMETER_HANDLER


EMPTY_PARAMETER_HANDLER = ParameterFieldComponentHandler(EmptyParameter())
