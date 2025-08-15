# (C) Copyright 2024 Anemoi contributors.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging
from functools import cached_property
from typing import Any

from earthkit.data.core.fieldlist import math
from earthkit.data.new_field.data import FieldData
from earthkit.data.new_field.geography import Geography
from earthkit.data.new_field.parameter import Parameter
from earthkit.data.new_field.time import FieldTime
from earthkit.data.new_field.vertical import Vertical

from .coordinates import extract_single_value
from .coordinates import is_scalar

# from .coordinates import extract_single_value
# from .coordinates import is_scalar
# from .metadata import XArrayMetadata


# from earthkit.data.new_field.parameter import Time

LOG = logging.getLogger(__name__)


class XArrayData(FieldData):
    def __init__(self, owner, selection: Any) -> None:
        self.owner = owner
        self.selection = selection

    def get_values(self, dtype=None):
        """Get the values stored in the field as an array."""

        values = self.selection.values
        if dtype is not None:
            values = values.astype(dtype, copy=False)
        return values


class XArrayParameter(Parameter):
    """A class to represent a parameter in an xarray dataset."""

    def __init__(self, owner: Any) -> None:
        """Create a new XArrayParameter object.

        Parameters
        ----------
        owner : Variable
            The variable that owns this field.
        selection : XArrayDataArray
            A 2D sub-selection of the variable's underlying array.
            This is actually a nD object, but the first dimensions are always 1.
            The other two dimensions are latitude and longitude.
        """
        self.owner = owner

        # Copy the metadata from the owner
        # self._md = owner._metadata.copy()

    @property
    def name(self):
        return self.owner.name

    @property
    def units(self):
        return self.owner.variable.attrs.get("units", None)


class XArrayTime(FieldTime):
    def __init__(self, owner: Any, selection: Any) -> None:
        self.owner = owner
        self.selection = selection

    @cached_property
    def spec(self):
        """Return the time specification."""
        _coords = {}
        for coord_name, coord_value in self.selection.coords.items():
            if is_scalar(coord_value):
                # Extract the single value from the scalar dimension
                # and store it in the metadata
                coordinate = self.owner.by_name[coord_name]
                _coords[coord_name] = coordinate.normalise(extract_single_value(coord_value))

        return self.owner.time.spec(_coords)


class XArrayVertical(Vertical):
    """A class to represent a vertical coordinate in an xarray dataset."""

    def __init__(self, owner: Any, selection: Any) -> None:
        """Create a new XArrayVertical object.

        Parameters
        ----------
        owner : Variable
            The variable that owns this field.
        selection : XArrayDataArray
            A 2D sub-selection of the variable's underlying array.
            This is actually a nD object, but the first dimensions are always 1.
            The other two dimensions are latitude and longitude.
        """
        from earthkit.data.new_field.xarray.coordinates import LevelCoordinate

        self.owner = owner
        self.selection = selection
        self.coord = None
        for c in owner.coordinates:
            if isinstance(c, LevelCoordinate):
                self.coord = c

    @property
    def level(self) -> str:
        """Return the level of the vertical coordinate."""
        if self.coord is None:
            return None
        name = self.coord.name

        v = self.selection[name].values
        if len(v.shape) == 0:
            return v.item()
        else:
            return v[0]

    @property
    def level_type(self) -> str:
        """Return the type of the vertical coordinate."""
        if self.coord is None:
            return None
        return self.coord.levtype


class XArrayGeography(Geography):
    def __init__(self, owner, selection):
        self.owner = owner
        self.selection = selection
        # By now, the only dimensions should be latitude and longitude
        self._shape = tuple(list(self.selection.shape)[-2:])
        if math.prod(self._shape) != math.prod(self.selection.shape):
            print(self.selection.ndim, self.selection.shape)
            print(self.selection)
            raise ValueError("Invalid shape for selection")

    @property
    def latitudes(self):
        return self.owner.grid.latitudes

    @property
    def longitudes(self):
        return self.owner.grid.longitudes

    @property
    def shape(self):
        return self._shape

    @property
    def projection(self):
        pass
