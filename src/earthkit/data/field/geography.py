# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .core import SpecFieldPart
from .core import wrap_spec_methods
from .spec.geography import Geography


@wrap_spec_methods(
    keys=[
        "latitudes",
        "longitudes",
        "shape",
        "grid_spec",
        "grid_type",
        "bounding_box",
        "distinct_latitudes",
        "distinct_longitudes",
        "x",
        "y",
        "projection",
        "unique_grid_id",
    ]
)
class GeographyFieldPart(SpecFieldPart):
    """Geography part of a field."""

    SPEC_CLS = Geography
    NAME = "geography"

    def get_grib_context(self, context) -> dict:
        pass
