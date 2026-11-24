# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Coordinate guessing for the xarray readers.

The geography part of the classification (point, longitude, latitude, x and y
coordinates, the scalar and unsupported fallbacks) and the inference of the
grid a variable lives on are done by :mod:`earthkit.geo.grids.xarray`. This
module extends it with what only earthkit-data needs: the non-geography
coordinates its field metadata is built from (time, step, date, level and
ensemble), their classification from a flavour's ``rules``, and the
earthkit-data interface of the grids (see :mod:`~.grid_adapter`).
"""

import logging
from abc import abstractmethod
from typing import Any, Dict, Optional

import xarray as xr
from earthkit.geo.grids.xarray import CoordinateAttributes
from earthkit.geo.grids.xarray import CoordinateGuesser as GeoCoordinateGuesser
from earthkit.geo.grids.xarray import DefaultCoordinateGuesser as GeoDefaultCoordinateGuesser
from earthkit.geo.grids.xarray import RulesCoordinateGuesser as GeoRulesCoordinateGuesser

from .coordinates import (
    Coordinate,
    DateCoordinate,
    EnsembleCoordinate,
    LevelCoordinate,
    StepCoordinate,
    TimeCoordinate,
)
from .grid_adapter import XarrayGrid

LOG = logging.getLogger(__name__)

__all__ = [
    "CoordinateAttributes",
    "CoordinateGuesser",
    "DefaultCoordinateGuesser",
    "FlavourCoordinateGuesser",
]


class CoordinateGuesser(GeoCoordinateGuesser):
    """Class to guess the type of coordinates in a dataset.

    Extends earthkit-geo's guesser with the non-geography coordinates: they
    are classified by :meth:`_guess_non_geo`, which earthkit-geo calls once
    its geography matchers have declined a coordinate, before the scalar and
    unsupported fallbacks.
    """

    @classmethod
    def from_flavour(cls, ds: xr.Dataset, flavour: Optional[Dict[str, Any]]) -> "CoordinateGuesser":
        """Creates a CoordinateGuesser from a flavour.

        Parameters
        ----------
        ds : xr.Dataset
            The dataset to guess coordinates from.
        flavour : Optional[Dict[str, Any]]
            The flavour to use for guessing.

        Returns
        -------
        CoordinateGuesser
            The created CoordinateGuesser.
        """
        if flavour is None:
            return DefaultCoordinateGuesser(ds)
        else:
            return FlavourCoordinateGuesser(ds, flavour)

    def grid(self, coordinates: Any, variable: Any) -> XarrayGrid:
        """Determines the grid type for the given coordinates and variable.

        The grid is the one earthkit-geo derives for the coordinates, seen
        through the earthkit-data interface (see :class:`~.grid_adapter.XarrayGrid`).

        Parameters
        ----------
        coordinates : Any
            The coordinates to determine the grid from.
        variable : Any
            The variable to determine the grid from.

        Returns
        -------
        XarrayGrid
            The determined grid.
        """
        grid = super().grid(coordinates, variable)
        return XarrayGrid(latlon_grid=grid.latlon_grid, xy_grid=grid.xy_grid)

    def _guess_non_geo(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[Coordinate]:
        """Classify a coordinate that carries no geography.

        Called by earthkit-geo once its geography matchers have declined the
        coordinate; the matchers are tried in the order the classifications
        were checked in before they were moved to earthkit-geo.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to classify.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[Coordinate]
            The classified coordinate, or None when no matcher recognised it,
            which leaves it to the scalar and unsupported fallbacks.
        """
        for matcher in (self._is_time, self._is_step, self._is_date, self._is_level, self._is_number):
            d = matcher(c, attributes)
            if d is not None:
                return d

        return None

    @abstractmethod
    def _is_time(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[TimeCoordinate]:
        """Checks if the coordinate is a time coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[TimeCoordinate]
            The TimeCoordinate if matched, else None.
        """
        pass

    @abstractmethod
    def _is_date(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[DateCoordinate]:
        """Checks if the coordinate is a date coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[DateCoordinate]
            The DateCoordinate if matched, else None.
        """
        pass

    @abstractmethod
    def _is_step(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[StepCoordinate]:
        """Checks if the coordinate is a step coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[StepCoordinate]
            The StepCoordinate if matched, else None.
        """
        pass

    @abstractmethod
    def _is_level(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[LevelCoordinate]:
        """Checks if the coordinate is a level coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[LevelCoordinate]
            The LevelCoordinate if matched, else None.
        """
        pass

    @abstractmethod
    def _is_number(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[EnsembleCoordinate]:
        """Checks if the coordinate is an ensemble coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[EnsembleCoordinate]
            The EnsembleCoordinate if matched, else None.
        """
        pass


class DefaultCoordinateGuesser(GeoDefaultCoordinateGuesser, CoordinateGuesser):
    """Implementation of CoordinateGuesser using the CF-convention heuristics.

    The geography coordinates are classified by earthkit-geo's default
    guesser; the non-geography ones are classified here.
    """

    def _is_time(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[TimeCoordinate]:
        """Checks if the coordinate is a time coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[TimeCoordinate]
            The TimeCoordinate if matched, else None.
        """
        if attributes.standard_name == "time":
            return TimeCoordinate(c)

        if attributes.name == "time" and attributes.standard_name != "forecast_reference_time":
            return TimeCoordinate(c)

        return None

    def _is_date(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[DateCoordinate]:
        """Checks if the coordinate is a date coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[DateCoordinate]
            The DateCoordinate if matched, else None.
        """
        if attributes.standard_name == "forecast_reference_time":
            return DateCoordinate(c)

        if attributes.name == "forecast_reference_time":
            return DateCoordinate(c)

        return None

    def _is_step(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[StepCoordinate]:
        """Checks if the coordinate is a step coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[StepCoordinate]
            The StepCoordinate if matched, else None.
        """
        if attributes.standard_name == "forecast_period":
            return StepCoordinate(c)

        if attributes.long_name == "time elapsed since the start of the forecast":
            return StepCoordinate(c)

        if attributes.name == "prediction_timedelta":  # WeatherBench
            return StepCoordinate(c)

        return None

    def _is_level(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[LevelCoordinate]:
        """Checks if the coordinate is a level coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[LevelCoordinate]
            The LevelCoordinate if matched, else None.
        """
        if attributes.standard_name == "atmosphere_hybrid_sigma_pressure_coordinate":
            return LevelCoordinate(c, "ml")

        if attributes.standard_name == "model_level_number":
            return LevelCoordinate(c, "ml")

        if attributes.long_name == "height" and attributes.units == "m":
            return LevelCoordinate(c, "height")

        if attributes.standard_name == "air_pressure" and attributes.units == "hPa":
            return LevelCoordinate(c, "pl")

        if attributes.long_name == "pressure" and attributes.units in ["hPa", "Pa"]:
            return LevelCoordinate(c, "pl")

        if attributes.name in ("level", "levelist"):
            # In the ECMWF MARS archive levelist is used for the list of levels in a field, while
            # levtype define the level type, its default value is "pl". Here we assume the dataset
            # uses the MARS vocabulary and check for the "levtype" attribute to determine the
            # level type. If not specified, we default to "pl".
            # TODO: justify that level can be treated in the same way as levelist
            levtype = c.attrs.get("levtype", "pl")
            return LevelCoordinate(c, levtype)

        if attributes.name == "vertical" and attributes.units == "hPa":
            return LevelCoordinate(c, "pl")

        if attributes.standard_name == "depth":
            return LevelCoordinate(c, "depth")

        if attributes.name == "vertical" and attributes.units == "hPa":
            return LevelCoordinate(c, "pl")

        if attributes.name == "surface":
            return LevelCoordinate(c, "sfc")

        return None

    def _is_number(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[EnsembleCoordinate]:
        """Checks if the coordinate is an ensemble coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[EnsembleCoordinate]
            The EnsembleCoordinate if matched, else None.
        """
        if attributes.name in ("realization", "number"):
            return EnsembleCoordinate(c)

        return None


class FlavourCoordinateGuesser(GeoRulesCoordinateGuesser, CoordinateGuesser):
    """Implementation of CoordinateGuesser that uses a flavour for guessing.

    The geography rules are matched by earthkit-geo's rules guesser; the
    non-geography ones (``time``, ``step``, ``date``, ``level``, ``number``)
    and the flavour's ``levtype`` are handled here, with the same rule format.
    """

    def __init__(self, ds: xr.Dataset, flavour: Dict[str, Any]) -> None:
        """Initializes the FlavourCoordinateGuesser.

        Parameters
        ----------
        ds : xr.Dataset
            The dataset to guess coordinates from.
        flavour : Dict[str, Any]
            The flavour to use for guessing.
        """
        super().__init__(ds, flavour["rules"])
        self.flavour = flavour

    def _is_time(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[TimeCoordinate]:
        """Checks if the coordinate is a time coordinate using the flavour rules.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[TimeCoordinate]
            The TimeCoordinate if matched, else None.
        """
        if self._match(c, "time", attributes):
            return TimeCoordinate(c)

        return None

    def _is_step(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[StepCoordinate]:
        """Checks if the coordinate is a step coordinate using the flavour rules.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[StepCoordinate]
            The StepCoordinate if matched, else None.
        """
        if self._match(c, "step", attributes):
            return StepCoordinate(c)

        return None

    def _is_date(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[DateCoordinate]:
        """Checks if the coordinate is a date coordinate using the flavour rules.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[DateCoordinate]
            The DateCoordinate if matched, else None.
        """
        if self._match(c, "date", attributes):
            return DateCoordinate(c)

        return None

    def _is_level(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[LevelCoordinate]:
        """Checks if the coordinate is a level coordinate using the flavour rules.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[LevelCoordinate]
            The LevelCoordinate if matched, else None.
        """
        rule = self._match(c, "level", attributes)
        if rule:
            return LevelCoordinate(
                c,
                self._levtype(c, attributes),
            )

        return None

    def _levtype(self, c: xr.DataArray, attributes: CoordinateAttributes) -> str:
        """Determines the level type for the coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        str
            The level type.
        """
        if "levtype" in self.flavour:
            return self.flavour["levtype"]

        raise NotImplementedError(f"levtype for {c=}")

    def _is_number(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[EnsembleCoordinate]:
        """Checks if the coordinate is an ensemble coordinate using the flavour rules.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[EnsembleCoordinate]
            The EnsembleCoordinate if matched, else None.
        """
        if self._match(c, "number", attributes):
            return EnsembleCoordinate(c)

        return None
