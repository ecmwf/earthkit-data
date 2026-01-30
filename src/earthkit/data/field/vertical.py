# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .core import SpecFieldPart
from .spec.vertical import Vertical


# @wrap_spec_methods(keys=["level", "layer", "cf", "abbreviation", "units", "positive", "type"])
class VerticalFieldPart(SpecFieldPart):
    """Vertical part of a field."""

    SPEC_CLS = Vertical
    NAME = "vertical"
    NAMESPACE_KEYS = ("level", "level_type", "units")

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.vertical import COLLECTOR

        COLLECTOR.collect(self, context)
