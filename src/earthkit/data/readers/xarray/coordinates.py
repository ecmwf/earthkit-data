# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Coordinate wrapper classes used by the xarray readers.

The geography coordinates (latitude, longitude, x, y, point, scalar,
unsupported), together with the :class:`~.coordinates.Coordinate` base they
all derive from and the ``is_scalar`` / ``extract_single_value`` helpers, come
from :mod:`earthkit.geo.grids.xarray` and are re-exported here. This module
only adds the non-geography coordinates earthkit-data uses to build field
metadata (time, date, step, level and ensemble).
"""

from __future__ import annotations

import datetime
import logging
from typing import Any, Optional

import numpy as np
from earthkit.geo.grids.xarray import (
    Coordinate,
    LatitudeCoordinate,
    LongitudeCoordinate,
    PointCoordinate,
    ScalarCoordinate,
    UnsupportedCoordinate,
    XCoordinate,
    YCoordinate,
    extract_single_value,
    is_scalar,
)

LOG = logging.getLogger(__name__)

__all__ = [
    "Coordinate",
    "DateCoordinate",
    "EnsembleCoordinate",
    "LatitudeCoordinate",
    "LevelCoordinate",
    "LongitudeCoordinate",
    "PointCoordinate",
    "ScalarCoordinate",
    "StepCoordinate",
    "TimeCoordinate",
    "UnsupportedCoordinate",
    "XCoordinate",
    "YCoordinate",
    "extract_single_value",
    "is_scalar",
]


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
        # ``levtype`` is kept in ``kwargs`` by the base class, so that
        # ``reduced()`` passes it back to the constructor
        super().__init__(variable, levtype=levtype)
        self.levtype = levtype

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
