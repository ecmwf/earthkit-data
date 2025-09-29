# (C) Copyright 2024 Anemoi contributors.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import datetime
import logging
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple

from numpy.typing import NDArray

from earthkit.data import Field
from earthkit.data.core.fieldlist_ori import math
from earthkit.data.decorators import thread_safe_cached_property

from .coordinates import extract_single_value
from .coordinates import is_scalar

# from .metadata import XArrayMetadata

# from earthkit.data.new_field.parameter import Parameter
# from earthkit.data.new_field.parameter import Time

LOG = logging.getLogger(__name__)


class EmptyFieldList:
    """A class to represent an empty list of fields."""

    def __len__(self) -> int:
        """Return the length of the field list."""
        return 0

    def __getitem__(self, i: int) -> Any:
        """Raise an IndexError when trying to access an item.

        Returns
        -------
        Any
            This method does not return anything as it raises an IndexError.

        Raises
        ------
        IndexError
            Always raised to indicate that the list is empty.

        Args
        ----
        i : int
            Index of the item to access.
        """
        raise IndexError(i)

    def __repr__(self) -> str:
        """Return a string representation of the EmptyFieldList."""
        return "EmptyFieldList()"


class XArrayField(Field):
    """A class to represent a field in an XArray dataset."""

    def __init__(self, owner: Any, selection: Any) -> None:
        """Create a new XArrayField object.

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
        self.selection = selection

        # Copy the metadata from the owner
        self._md = owner._metadata.copy()

        for coord_name, coord_value in self.selection.coords.items():
            if is_scalar(coord_value):
                # Extract the single value from the scalar dimension
                # and store it in the metadata
                coordinate = owner.by_name[coord_name]
                self._md[coord_name] = coordinate.normalise(extract_single_value(coord_value))

        # print(values.ndim, values.shape, selection.dims)
        # By now, the only dimensions should be latitude and longitude
        self._shape = tuple(list(self.selection.shape)[-2:])
        if math.prod(self._shape) != math.prod(self.selection.shape):
            print(self.selection.ndim, self.selection.shape)
            print(self.selection)
            raise ValueError("Invalid shape for selection")

    @property
    def shape(self) -> Tuple[int, int]:
        """Return the shape of the field."""
        return self._shape

    def to_numpy(
        self, flatten: bool = False, dtype: Optional[type] = None, index: Optional[int] = None
    ) -> NDArray[Any]:
        """Convert the selection to a numpy array.

        Returns
        -------
        NDArray[Any]
            The selection converted to a numpy array.

        Args
        ----
        flatten : bool, optional
            Whether to flatten the array, by default False.
        dtype : Optional[type], optional
            Data type of the array, by default None.
        index : Optional[int], optional
            Index to select a specific element, by default None.
        """
        if index is not None:
            values = self.selection[index]
        else:
            values = self.selection

        assert dtype is None

        if flatten:
            return values.values.flatten()

        return values  # .reshape(self.shape)

    @thread_safe_cached_property
    def _metadata(self):
        """Return the metadata of the field."""
        pass
        # return XArrayMetadata(self)

    def grid_points(self) -> Any:
        """Return the grid points of the field."""
        return self.owner.grid_points()

    def to_latlon(self, flatten: bool = True) -> Dict[str, Any]:
        """Convert the selection to latitude and longitude coordinates.

        Returns
        -------
        Dict[str, Any]
            The latitude and longitude coordinates.

        Args
        ----
        flatten : bool, optional
            Whether to flatten the coordinates, by default True.
        """
        assert flatten
        return dict(lat=self.latitudes, lon=self.longitudes)

    @property
    def resolution(self) -> Optional[Any]:
        """Return the resolution of the field."""
        return None

    @property
    def grid_mapping(self) -> Any:
        """Return the grid mapping of the field."""
        return self.owner.grid_mapping

    @property
    def latitudes(self) -> Any:
        """Return the latitudes of the field."""
        return self.owner.latitudes

    @property
    def longitudes(self) -> Any:
        """Return the longitudes of the field."""
        return self.owner.longitudes

    @property
    def forecast_reference_time(self) -> datetime.datetime:
        """Return the forecast reference time of the field."""
        date, time = self.metadata("date", "time")
        assert len(time) == 4, time
        assert len(date) == 8, date
        yyyymmdd = int(date)
        time = int(time) // 100
        return datetime.datetime(yyyymmdd // 10000, yyyymmdd // 100 % 100, yyyymmdd % 100, time)

    def __repr__(self) -> str:
        """Return a string representation of the field."""
        return repr(self._metadata)

    def _values(self, dtype: Optional[type] = None) -> Any:
        """Return the values of the selection.

        Returns
        -------
        Any
            The values of the selection.

        Args
        ----
        dtype : Optional[type], optional
            Data type of the values, by default None.
        """
        # we don't use .values as this will download the data
        return self.selection
