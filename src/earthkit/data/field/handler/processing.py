# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.field.component.processing import Processing

from .core import SimpleFieldComponentHandler


class ProcessingFieldComponentHandler(SimpleFieldComponentHandler):
    """Handler for the processing component of a field."""

    COMPONENT_CLS = Processing
    NAME = "processing"

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.processing import COLLECTOR

        COLLECTOR.collect(self, context)

    @classmethod
    def from_component(cls, component: Processing) -> "ProcessingFieldComponentHandler":
        return ProcessingFieldComponentHandler(component)

    @classmethod
    def create_empty(cls) -> "ProcessingFieldComponentHandler":
        return EMPTY_PROCESSING_HANDLER


EMPTY_PROCESSING_HANDLER = ProcessingFieldComponentHandler(Processing(()))
