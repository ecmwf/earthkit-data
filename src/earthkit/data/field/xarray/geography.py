# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import math

from earthkit.data.specs.geography import SimpleGeography


class XArrayGeography(SimpleGeography):
    def __init__(self, owner, selection):
        self.owner = owner
        self.selection = selection
        # By now, the only dimensions should be latitude and longitude
        self._shape = tuple(list(self.selection.shape)[-2:])
        if math.prod(self._shape) != math.prod(self.selection.shape):
            # print(self.selection.ndim, self.selection.shape)
            # print(self.selection)
            raise ValueError("Invalid shape for selection")

    @property
    def latitudes(self):
        return self.owner.grid.latitudes.reshape(self.shape)

    @property
    def longitudes(self):
        return self.owner.grid.longitudes

    @property
    def distinct_latitudes(self):
        r"""Return the distinct latitudes."""
        pass

    @property
    def distinct_longitudes(self):
        r"""Return the distinct longitudes."""
        pass

    @property
    def x(self):
        r"""array-like: Return the x coordinates in the original CRS."""
        pass

    @property
    def y(self):
        r"""array-like: Return the y coordinates in the original CRS."""
        pass

    @property
    def shape(self):
        return self._shape

    @property
    def projection(self):
        pass

    @property
    def bounding_box(self):
        """:obj:`BoundingBox <data.utils.bbox.BoundingBox>`: Return the bounding box."""
        pass

    @property
    def unique_grid_id(self):
        r"""str: Return the unique id of the grid."""
        pass

    @property
    def grid_spec(self):
        r"""Return the grid specification."""
        pass

    @property
    def grid_type(self):
        r"""Return the grid specification."""
        pass
