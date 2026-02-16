# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import math
from typing import Any

from earthkit.data.field.component.geography import BaseGeography
from earthkit.data.field.geography import GeographyFieldComponentHandler


class XArrayGeography(BaseGeography):
    def __init__(self, owner, selection):
        self.owner = owner
        self.selection = selection
        # By now, the only dimensions should be latitude and longitude
        self._shape = tuple(list(self.selection.shape)[-2:])
        if math.prod(self._shape) != math.prod(self.selection.shape):
            # print(self.selection.ndim, self.selection.shape)
            # print(self.selection)
            raise ValueError("Invalid shape for selection")

    def latitudes(self, dtype=None):
        return self.owner.grid.latitudes.reshape(self.shape())

    def longitudes(self, dtype=None):
        return self.owner.grid.longitudes.reshape(self.shape())

    def distinct_latitudes(self, dtype=None):
        r"""Return the distinct latitudes."""
        pass

    def distinct_longitudes(self, dtype=None):
        r"""Return the distinct longitudes."""
        pass

    def x(self, dtype=None):
        r"""array-like: Return the x coordinates in the original CRS."""
        pass

    def y(self, dtype=None):
        r"""array-like: Return the y coordinates in the original CRS."""
        pass

    def shape(self):
        return self._shape

    def projection(self):
        pass

    def bounding_box(self):
        return self.owner.grid.bbox

    def unique_grid_id(self):
        r"""str: Return the unique id of the grid."""
        pass

    def grid_spec(self):
        r"""Return the grid specification."""
        pass

    def grid_type(self):
        r"""Return the grid specification."""
        pass

    def area(self):
        r"""Return the area of the grid."""
        pass

    def grid(self):
        r"""Return the area of the grid."""
        pass

    @classmethod
    def from_dict(d):
        raise NotImplementedError("XArrayGeography.form_dict() is not implemented")

    def to_dict(self):
        return dict()

    def __getstate__(self):
        pass

    def __setstate__(self, state):
        pass


class XArrayGeographyHandler(GeographyFieldComponentHandler):
    def __init__(self, owner: Any, selection: Any) -> None:
        part = XArrayGeography(owner, selection)
        super().__init__(part)
