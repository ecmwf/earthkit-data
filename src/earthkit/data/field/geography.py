# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .core import SimpleFieldPartHandler
from .part.geography import BaseGeography


# @wrap_spec_methods(
#     keys=[
#         "latitudes",
#         "longitudes",
#         "shape",
#         "grid_spec",
#         "grid_type",
#         "bounding_box",
#         "distinct_latitudes",
#         "distinct_longitudes",
#         "x",
#         "y",
#         "projection",
#         "unique_grid_id",
#     ]
# )
class GeographyFieldPartHandler(SimpleFieldPartHandler):
    """Geography part of a field."""

    PART_CLS = BaseGeography
    NAME = "geography"

    def get_grib_context(self, context) -> dict:
        pass
