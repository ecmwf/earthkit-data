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
from typing import Any, Dict, Optional, Tuple, Union

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
    is_point = False

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
        if np.all(index < len(values)) and np.all(values[index] == value):
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
            The value to normalise.

        Returns
        -------
        Any
            The normalised value.
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


class HybridLevels:
    """Decoded CF ``atmosphere_hybrid_sigma_pressure_coordinate`` of a dataset.

    The coordinate is decoded once per dataset and shared by all the fields (and all the
    reduced copies of the level coordinate) that use it. For a field only the level lookup
    (:meth:`level_number`) is needed.

    Parameters
    ----------
    name : str
        Name of the level coordinate.
    values : list
        The values of the level coordinate in the order of the dataset.
    level_numbers : list of int or None
        The model level number of each coordinate value, or None when they are not known.
    coefficients : tuple or None
        The ``(A, B)`` half level coefficients of the whole model, or None when they cannot be
        rebuilt. The same arrays are shared by all the fields.
    """

    def __init__(
        self,
        name: str,
        values: list,
        level_numbers: Optional[list],
        coefficients: Optional[Tuple[Any, Any]],
    ) -> None:
        self.name = name
        self.level_numbers = level_numbers
        self.coefficients = coefficients
        self._index: Dict[Any, int] = {}
        for i, v in enumerate(values):
            self._index.setdefault(v, i)

    def __repr__(self) -> str:
        return "%s[name=%s,level_numbers=%s,coefficients=%s]" % (
            self.__class__.__name__,
            self.name,
            self.level_numbers is not None,
            self.coefficients is not None,
        )

    def level_number(self, value: Any) -> Optional[int]:
        """Return the model level number of a coordinate value.

        Parameters
        ----------
        value : Any
            A value of the level coordinate (exact match).

        Returns
        -------
        int or None
            The model level number, or None when it is not known.
        """
        if self.level_numbers is None:
            return None
        i = self._index.get(value)
        if i is None:
            return None
        return self.level_numbers[i]

    @classmethod
    def from_dataset(cls, ds: xr.Dataset, name: str) -> Optional["HybridLevels"]:
        """Decode the level coordinate ``name`` of ``ds``.

        Returns
        -------
        HybridLevels or None
            None when the coordinate cannot be decoded. A decoding error is logged as a warning, it
            never fails the read.
        """
        try:
            from earthkit.data.field.cf import decode_parametric_vertical

            model = decode_parametric_vertical(ds, name)

            level_numbers = model.level_numbers()
            if level_numbers is not None:
                level_numbers = [int(x) for x in level_numbers]

            coefficients = None
            try:
                A, B = model.to_level_parameters().coefficients()
                # The arrays are shared by all the fields. Copy them once (they may be views
                # of arrays owned by the model) and make them read-only, so that changing the
                # coefficients of one field cannot silently change those of all the others.
                A = np.array(A, dtype=np.float64)
                B = np.array(B, dtype=np.float64)
                A.setflags(write=False)
                B.setflags(write=False)
                coefficients = (A, B)
            except ValueError as e:
                LOG.debug("Hybrid coordinate %s: no half level coefficients: %s", name, e)

            return cls(name, ds[name].values.tolist(), level_numbers, coefficients)
        except Exception as e:
            LOG.warning("Cannot decode the hybrid level coordinate %s: %s", name, e)
            return None


def decode_hybrid_levels(ds: xr.Dataset, coordinates: list, cache: Dict[str, Optional[HybridLevels]]) -> None:
    """Attach the decoded hybrid levels to the level coordinates that carry ``formula_terms``.

    Parameters
    ----------
    ds : xr.Dataset
        The dataset.
    coordinates : list
        The coordinates of a variable.
    cache : dict
        The decoded coordinates (or None for those that could not be decoded) by name. It makes
        sure that a coordinate is decoded once per dataset.
    """
    from earthkit.data.field.cf.parametric_vertical import get_cf_attribute

    for c in coordinates:
        if not isinstance(c, LevelCoordinate) or c.levtype != "ml" or c.hybrid is not None:
            continue

        name = c.name
        if name not in cache:
            hybrid = None
            if c.variable.ndim == 1 and get_cf_attribute(c.variable, "formula_terms") is not None:
                hybrid = HybridLevels.from_dataset(ds, name)
            cache[name] = hybrid

        if cache[name] is not None:
            c.set_hybrid(cache[name])


class LevelCoordinate(Coordinate):
    """Coordinate class for level.

    Parameters
    ----------
    variable : Any
        The variable representing the coordinate.
    levtype : str
        The type of level.
    hybrid : HybridLevels, optional
        The decoded CF hybrid sigma pressure coordinate. Only available for hybrid levels
        with ``formula_terms``.
    """

    mars_names = ("level", "levelist")

    def __init__(self, variable: Any, levtype: str, hybrid: Optional[HybridLevels] = None) -> None:
        """Initialize the level coordinate.

        Parameters
        ----------
        variable : Any
            The variable representing the coordinate.
        levtype : str
            The type of level.
        hybrid : HybridLevels, optional
            The decoded CF hybrid sigma pressure coordinate.
        """
        super().__init__(variable)
        self.levtype = levtype
        self.hybrid = None
        # kwargs is used when creating a new coordinate (reduced method)
        self.kwargs = {"levtype": levtype}
        if hybrid is not None:
            self.set_hybrid(hybrid)

    def set_hybrid(self, hybrid: HybridLevels) -> None:
        """Set the decoded hybrid levels. They are kept by the coordinates created by ``reduced``."""
        self.hybrid = hybrid
        self.kwargs["hybrid"] = hybrid

    def normalise(self, value: Any) -> Any:
        """Normalize the value for the level coordinate.

        Parameters
        ----------
        value : Any
            The value to normalise.

        Returns
        -------
        Any
            The normalised value.
        """
        # Some netcdf have pressure levels in float
        try:
            if (v := int(value)) == value:
                return v
        except Exception as e:
            raise ValueError(f"Cannot normalise value {value} for level coordinate {self.name}. {e}") from e

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
            The value to normalise.

        Returns
        -------
        Any
            The normalised value.
        """
        if int(value) == value:
            return int(value)
        return value


class PointCoordinate(Coordinate):
    """Coordinate class for point data."""

    is_point = True
    mars_names = ("point",)


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
