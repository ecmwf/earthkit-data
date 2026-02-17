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


def _array_convert(v, flatten=False, dtype=None):
    if flatten:
        from earthkit.data.utils.array import flatten

        v = flatten(v)

    if dtype is not None:
        from earthkit.utils.array import array_namespace
        from earthkit.utils.array.convert import convert_dtype

        target_xp = array_namespace(v)
        target_dtype = convert_dtype(dtype, target_xp)
        if target_dtype is not None:
            v = target_xp.astype(v, target_dtype, copy=False)

    return v


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
        lat, _ = self.owner.grid.latlon
        return lat.reshape(self.shape())

    def longitudes(self, dtype=None):
        _, lon = self.owner.grid.latlon
        return lon.reshape(self.shape())

    def distinct_latitudes(self, dtype=None):
        r"""Return the distinct latitudes."""
        pass

    def distinct_longitudes(self, dtype=None):
        r"""Return the distinct longitudes."""
        pass

    def x(self, dtype=None):
        r"""array-like: Return the x coordinates in the original CRS."""
        x, _ = self.owner.grid.xy
        return x.reshape(self.shape())

    def y(self, dtype=None):
        r"""array-like: Return the y coordinates in the original CRS."""
        _, y = self.owner.grid.xy
        return y.reshape(self.shape())

    def shape(self):
        return self._shape

    def projection(self):
        return self.owner.grid.projection

    def bounding_box(self):
        return self.owner.grid.bbox

    def unique_grid_id(self):
        r"""str: Return the unique id of the grid."""
        return f"{self.shape()}"

    def grid_spec(self):
        r"""Return the grid specification."""
        pass

    def grid_type(self):
        r"""Return the grid specification."""
        pass

    def area(self):
        r"""Return the area of the grid."""
        return self.bounding_box().as_tuple()

    def grid(self):
        r"""Return the area of the grid."""
        pass

    @classmethod
    def from_dict(d):
        raise NotImplementedError("XArrayGeography.form_dict() is not implemented")

    def latlon(self, flatten=False, dtype=None):
        lat, lon = self.owner.grid.latlon
        lat = lat.reshape(self.shape())
        lon = lon.reshape(self.shape())
        lat = _array_convert(lat, flatten=flatten, dtype=dtype)
        lon = _array_convert(lon, flatten=flatten, dtype=dtype)

        return lat, lon

    def points(self, flatten=False, dtype=None):
        x, y = self.owner.grid.xy
        if x is not None and y is not None:
            x = x.reshape(self.shape())
            y = y.reshape(self.shape())
            x = _array_convert(x, flatten=flatten, dtype=dtype)
            y = _array_convert(y, flatten=flatten, dtype=dtype)
            return x, y
        else:
            raise ValueError("XArrayGeography: points not available")

    def to_dict(self):
        return dict()

    def __getstate__(self):
        pass

    def __setstate__(self, state):
        pass


# class MeshedXarrayLatLonGeography(XArrayGeography):
#     def __init__(self, owner, selection):
#         super().__init__(owner, selection)

#     def _latlon(self, dtype=None, flatten=False):
#         """Get the grid points for the meshed grid."""

#         if self.variable_dims == (self.lon.variable.name, self.lat.variable.name):
#             lat, lon = np.meshgrid(
#                 self.lat.variable.values,
#                 self.lon.variable.values,
#             )
#         elif self.variable_dims == (self.lat.variable.name, self.lon.variable.name):
#             lon, lat = np.meshgrid(
#                 self.lon.variable.values,
#                 self.lat.variable.values,
#             )

#         else:
#             raise NotImplementedError(
#                 f"MeshedGrid.grid_points: unrecognized variable_dims {self.variable_dims}"
#             )

#         return lat.flatten(), lon.flatten()


# lat = self.latitudes(dtype=dtype)
#         lon = self.longitudes(dtype=dtype)

#         if flatten:
#             lat = lat.flatten()
#             lon = lon.flatten()

#         return lat, lon


class XArrayGeographyHandler(GeographyFieldComponentHandler):
    def __init__(self, owner: Any, selection: Any) -> None:
        part = XArrayGeography(owner, selection)
        super().__init__(part)
