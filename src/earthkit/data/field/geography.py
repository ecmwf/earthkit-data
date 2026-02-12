# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .component.geography import BaseGeography
from .component.geography import EmptyGeography
from .component.geography import create_geography_from_dict
from .core import SimpleFieldComponentHandler


class GeographyFieldComponentHandler(SimpleFieldComponentHandler):
    """Geography component of a field."""

    COMPONENT_CLS = BaseGeography
    COMPONENT_MAKER = create_geography_from_dict
    NAME = "geography"

    def get_grib_context(self, context) -> dict:
        pass

    @classmethod
    def create_empty(cls) -> "GeographyFieldComponentHandler":
        return EMPTY_GEOGRAPHY_HANDLER


EMPTY_GEOGRAPHY_HANDLER = GeographyFieldComponentHandler(EmptyGeography())
