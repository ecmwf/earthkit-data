# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from __future__ import annotations

import datetime
import logging
from typing import Any
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

import numpy as np
import xarray as xr

from earthkit.data.utils.dates import to_datetime

LOG = logging.getLogger(__name__)


def is_scalar(variable: Any) -> bool:
    """Check if the variable is scalar.

    Parameters
    ----------
    variable : Any
        The variable to check.

    Returns
    -------
    bool
        True if the variable is scalar, False otherwise.
    """
    shape = variable.shape
    if shape == (1,):
        return True
    if len(shape) == 0:
        return True
    return False


def extract_single_value(variable: Any) -> Any:
    """Extract a single value from the variable.

    Parameters
    ----------
    variable : Any
        The variable to extract the value from.

    Returns
    -------
    Any
        The extracted single value.
    """
    shape = variable.shape
    if np.issubdtype(variable.values.dtype, np.datetime64):
        if len(shape) == 0:
            return to_datetime(variable.values)  # Convert to python datetime
        if shape == (1,):
            return to_datetime(variable.values[0])
        assert False, (shape, variable.values[:2])

    if np.issubdtype(variable.values.dtype, np.timedelta64):
        if len(shape) == 0:
            # Convert to python timedelta64
            return datetime.timedelta(seconds=variable.values.astype("timedelta64[s]").astype(int).item())
        assert False, (shape, variable.values)

    if shape == (1,):
        return variable.values[0]

    if len(shape) == 0:
        return variable.values.item()

    assert False, (shape, variable.values)


class Coordinate:
    """Base class for coordinates."""

    is_grid = False
    is_dim = True
    is_lat = False
    is_lon = False
    is_time = False
    is_step = False
    is_date = False
    is_member = False
    is_x = False
    is_y = False

    def __init__(self, variable: xr.DataArray) -> None:
        """Initialize the coordinate.

        Parameters
        ----------
        variable : Any
            The variable representing the coordinate.
        """
        self.variable = variable
        self.scalar = is_scalar(variable)
        self.kwargs: Dict[str, Any] = {}  # Used when creating a new coordinate (reduced method)

    def __len__(self) -> int:
        """Get the length of the coordinate.

        Returns
        -------
        int
            The length of the coordinate.
        """
        return 1 if self.scalar else len(self.variable)

    def __repr__(self) -> str:
        """Get the string representation of the coordinate.

        Returns
        -------
        str
            The string representation of the coordinate.
        """
        return "%s[name=%s,values=%s,shape=%s]" % (
            self.__class__.__name__,
            self.variable.name,
            self.variable.values if self.scalar else len(self),
            self.variable.shape,
        )

    def reduced(self, i: int) -> Coordinate:
        """Create a new coordinate with a single value.

        Parameters
        ----------
        i : int
            The index of the value to select.

        Returns
        -------
        Coordinate
            A new coordinate with the selected value.
        """
        return self.__class__(
            self.variable.isel({self.variable.dims[0]: i}),
            **self.kwargs,
        )

    def index(self, value: Union[Any, list, tuple]) -> Optional[Union[int, list]]:
        """Return the index of the value in the coordinate.

        Parameters
        ----------
        value : Union[Any, list, tuple]
            The value to search for.

        Returns
        -------
        Optional[Union[int, list]]
            The index or indices of the value in the coordinate, or None if not found.
        """
        if isinstance(value, (list, tuple)):
            if len(value) == 1:
                return self._index_single(value)
            else:
                return self._index_multiple(value)
        return self._index_single(value)

    def _index_single(self, value: Any) -> Optional[int]:
        """Return the index of a single value in the coordinate.

        Parameters
        ----------
        value : Any
            The value to search for.

        Returns
        -------
        Optional[int]
            The index of the value in the coordinate, or None if not found.
        """
        values = self.variable.values

        # Check if dimension is 0D
        if not isinstance(values, (list, np.ndarray)):
            values = [values]

        # Assume the array is sorted
        index = np.searchsorted(values, value)

        if index < len(values) and values[index] == value:
            return index

        # If not found, we need to check if the value is in the array

        index = np.where(values == value)[0]
        if len(index) > 0:
            return index[0]

        return None

    def _index_multiple(self, value: list) -> Optional[list]:
        """Return the indices of multiple values in the coordinate.

        Parameters
        ----------
        value : list
            The values to search for.

        Returns
        -------
        Optional[list]
            The indices of the values in the coordinate, or None if not found.
        """
        values = self.variable.values

        # Check if dimension is 0D
        if not isinstance(values, (list, np.ndarray)):
            values = [values]

        # Assume the array is sorted

        index = np.searchsorted(values, value)
        index = index[index < len(values)]

        if np.all(values[index] == value):
            return index

        # If not found, we need to check if the value is in the array

        index = np.where(np.isin(values, value))[0]

        # We could also return incomplete matches
        if len(index) == len(value):
            return index

        return None

    @property
    def name(self) -> str:
        """Get the name of the coordinate."""
        return self.variable.name

    def normalise(self, value: Any) -> Any:
        """Normalize the value for the coordinate.

        Parameters
        ----------
        value : Any
            The value to normalize.

        Returns
        -------
        Any
            The normalized value.
        """
        # Subclasses to format values that will be added to the field metadata
        return value

    @property
    def single_value(self) -> Any:
        """Get the single value of the coordinate."""
        return extract_single_value(self.variable)


class TimeCoordinate(Coordinate):
    """Coordinate class for time."""

    is_time = True
    mars_names = ("valid_datetime",)

    def index(self, time: datetime.datetime) -> Optional[int]:
        """Return the index of the time in the coordinate.

        Parameters
        ----------
        time : datetime.datetime
            The time to search for.

        Returns
        -------
        Optional[int]
            The index of the time in the coordinate, or None if not found.
        """
        return super().index(np.datetime64(time))


class DateCoordinate(Coordinate):
    """Coordinate class for date."""

    is_date = True
    mars_names = ("date",)

    def index(self, date: datetime.datetime) -> Optional[int]:
        """Return the index of the date in the coordinate.

        Parameters
        ----------
        date : datetime.datetime
            The date to search for.

        Returns
        -------
        Optional[int]
            The index of the date in the coordinate, or None if not found.
        """
        return super().index(np.datetime64(date))


class StepCoordinate(Coordinate):
    """Coordinate class for step."""

    is_step = True
    mars_names = ("step",)


class LevelCoordinate(Coordinate):
    """Coordinate class for level.

    Parameters
    ----------
    variable : Any
        The variable representing the coordinate.
    levtype : str
        The type of level.
    """

    mars_names = ("level", "levelist")

    def __init__(self, variable: Any, levtype: str) -> None:
        """Initialize the level coordinate.

        Parameters
        ----------
        variable : Any
            The variable representing the coordinate.
        levtype : str
            The type of level.
        """
        super().__init__(variable)
        self.levtype = levtype
        # kwargs is used when creating a new coordinate (reduced method)
        self.kwargs = {"levtype": levtype}

    def normalise(self, value: Any) -> Any:
        """Normalize the value for the level coordinate.

        Parameters
        ----------
        value : Any
            The value to normalize.

        Returns
        -------
        Any
            The normalized value.
        """
        # Some netcdf have pressue levels in float
        if int(value) == value:
            return int(value)
        return value


class EnsembleCoordinate(Coordinate):
    """Coordinate class for ensemble."""

    is_member = True
    mars_names = ("number",)

    def normalise(self, value: Any) -> Any:
        """Normalize the value for the ensemble coordinate.

        Parameters
        ----------
        value : Any
            The value to normalize.

        Returns
        -------
        Any
            The normalized value.
        """
        if int(value) == value:
            return int(value)
        return value


class LongitudeCoordinate(Coordinate):
    """Coordinate class for longitude."""

    is_grid = True
    is_lon = True
    mars_names = ("longitude",)


class LatitudeCoordinate(Coordinate):
    """Coordinate class for latitude."""

    is_grid = True
    is_lat = True
    mars_names = ("latitude",)


class XCoordinate(Coordinate):
    """Coordinate class for X."""

    is_grid = True
    is_x = True
    mars_names = ("x",)


class YCoordinate(Coordinate):
    """Coordinate class for Y."""

    is_grid = True
    is_y = True
    mars_names = ("y",)


class ScalarCoordinate(Coordinate):
    """Coordinate class for scalar."""

    is_grid = False

    @property
    def mars_names(self) -> Tuple[str, ...]:
        """Get the MARS names for the coordinate."""
        return (self.variable.name,)


class UnsupportedCoordinate(Coordinate):
    """Coordinate class for unsupported coordinates."""

    @property
    def mars_names(self) -> tuple:
        """Get the MARS names for the coordinate."""
        return (self.variable.name,)
