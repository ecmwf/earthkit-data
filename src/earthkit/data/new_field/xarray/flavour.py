# (C) Copyright 2024 Anemoi contributors.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import json
import logging
import os
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Dict
from typing import Hashable
from typing import Optional
from typing import Tuple

import xarray as xr
import yaml
from anemoi.utils.config import DotDict

from .coordinates import Coordinate
from .coordinates import DateCoordinate
from .coordinates import EnsembleCoordinate
from .coordinates import LatitudeCoordinate
from .coordinates import LevelCoordinate
from .coordinates import LongitudeCoordinate
from .coordinates import ScalarCoordinate
from .coordinates import StepCoordinate
from .coordinates import TimeCoordinate
from .coordinates import UnsupportedCoordinate
from .coordinates import XCoordinate
from .coordinates import YCoordinate
from .coordinates import is_scalar
from .grid import Grid
from .grid import MeshedGrid
from .grid import MeshProjectionGrid
from .grid import UnstructuredGrid
from .grid import UnstructuredProjectionGrid

# CoordinateAttributes = namedtuple("CoordinateAttributes", ["axis", "name", "long_name", "standard_name", "units"])


try:
    import tomllib  # Only available since 3.11
except ImportError:
    import tomli as tomllib


LOG = logging.getLogger(__name__)


class DotDict(dict):
    """A dictionary that allows access to its keys as attributes.

    >>> d = DotDict({"a": 1, "b": {"c": 2}})
    >>> d.a
    1
    >>> d.b.c
    2
    >>> d.b = 3
    >>> d.b
    3

    The class is recursive, so nested dictionaries are also DotDicts.

    The DotDict class has the same constructor as the dict class.

    >>> d = DotDict(a=1, b=2)
    """

    def __init__(self, *args, **kwargs):
        """Initialize a DotDict instance.

        Parameters
        ----------
        *args : tuple
            Positional arguments for the dict constructor.
        **kwargs : dict
            Keyword arguments for the dict constructor.
        """
        super().__init__(*args, **kwargs)

        for k, v in self.items():
            if isinstance(v, dict):
                self[k] = DotDict(v)

            if isinstance(v, list):
                self[k] = [DotDict(i) if isinstance(i, dict) else i for i in v]

            if isinstance(v, tuple):
                self[k] = [DotDict(i) if isinstance(i, dict) else i for i in v]

    @classmethod
    def from_file(cls, path: str) -> DotDict:
        """Create a DotDict from a file.

        Parameters
        ----------
        path : str
            The path to the file.

        Returns
        -------
        DotDict
            The created DotDict.
        """
        _, ext = os.path.splitext(path)
        if ext == ".yaml" or ext == ".yml":
            return cls.from_yaml_file(path)
        elif ext == ".json":
            return cls.from_json_file(path)
        elif ext == ".toml":
            return cls.from_toml_file(path)
        else:
            raise ValueError(f"Unknown file extension {ext}")

    @classmethod
    def from_yaml_file(cls, path: str) -> DotDict:
        """Create a DotDict from a YAML file.

        Parameters
        ----------
        path : str
            The path to the YAML file.

        Returns
        -------
        DotDict
            The created DotDict.
        """
        with open(path, "r") as file:
            data = yaml.safe_load(file)

        return cls(data)

    @classmethod
    def from_json_file(cls, path: str) -> DotDict:
        """Create a DotDict from a JSON file.

        Parameters
        ----------
        path : str
            The path to the JSON file.

        Returns
        -------
        DotDict
            The created DotDict.
        """
        with open(path, "r") as file:
            data = json.load(file)

        return cls(data)

    @classmethod
    def from_toml_file(cls, path: str) -> DotDict:
        """Create a DotDict from a TOML file.

        Parameters
        ----------
        path : str
            The path to the TOML file.

        Returns
        -------
        DotDict
            The created DotDict.
        """
        with open(path, "r") as file:
            data = tomllib.load(file)
        return cls(data)

    def __getattr__(self, attr: str) -> Any:
        """Get an attribute.

        Parameters
        ----------
        attr : str
            The attribute name.

        Returns
        -------
        Any
            The attribute value.
        """
        try:
            return self[attr]
        except KeyError:
            raise AttributeError(attr)

    def __setattr__(self, attr: str, value: Any) -> None:
        """Set an attribute.

        Parameters
        ----------
        attr : str
            The attribute name.
        value : Any
            The attribute value.
        """
        if isinstance(value, dict):
            value = DotDict(value)
        self[attr] = value

    def __repr__(self) -> str:
        """Return a string representation of the DotDict.

        Returns
        -------
        str
            The string representation.
        """
        return f"DotDict({super().__repr__()})"


class CoordinateAttributes(DotDict):
    pass


class CoordinateGuesser(ABC):
    """Class to guess the type of coordinates in a dataset."""

    def __init__(self, ds: xr.Dataset) -> None:
        """Initializes the CoordinateGuesser.

        Parameters
        ----------
        ds : xr.Dataset
            The dataset to guess coordinates from.
        """
        self.ds = ds
        self._coordinate_cache: Dict[Hashable, Coordinate] = {}
        self._grid_cache: Dict[Hashable, Grid] = {}

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

    def guess(self, c: xr.DataArray, coord: Hashable) -> Coordinate:
        """Guesses the type of a coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to guess.
        coord : Hashable
            The name of the coordinate.

        Returns
        -------
        Coordinate
            The guessed coordinate type.
        """
        if coord not in self._coordinate_cache:
            self._coordinate_cache[coord] = self._guess(c, coord)
        return self._coordinate_cache[coord]

    def _guess(self, coordinate: xr.DataArray, coord: Hashable) -> Coordinate:
        """Internal method to guess the type of a coordinate.

        Parameters
        ----------
        coordinate : xr.DataArray
            The coordinate to guess.
        coord : Hashable
            The name of the coordinate.

        Returns
        -------
        Coordinate
            The guessed coordinate type.
        """
        name = coordinate.name
        standard_name = getattr(coordinate, "standard_name", "").lower()
        axis = getattr(coordinate, "axis", "")
        long_name = getattr(coordinate, "long_name", "").lower()
        units = getattr(coordinate, "units", "")

        attributes = CoordinateAttributes(
            axis=axis,
            name=name,
            long_name=long_name,
            standard_name=standard_name,
            units=units,
        )

        d: Optional[Coordinate] = None

        d = self._is_longitude(coordinate, attributes)
        if d is not None:
            return d

        d = self._is_latitude(coordinate, attributes)
        if d is not None:
            return d

        d = self._is_x(coordinate, attributes)
        if d is not None:
            return d

        d = self._is_y(coordinate, attributes)
        if d is not None:
            return d

        d = self._is_time(coordinate, attributes)
        if d is not None:
            return d

        d = self._is_step(coordinate, attributes)
        if d is not None:
            return d

        d = self._is_date(coordinate, attributes)
        if d is not None:
            return d

        d = self._is_level(coordinate, attributes)
        if d is not None:
            return d

        d = self._is_number(coordinate, attributes)
        if d is not None:
            return d

        if coordinate.shape in ((1,), tuple()):
            return ScalarCoordinate(coordinate)

        LOG.warning(
            f"Coordinate {coord} not supported\n{axis=}, {name=},"
            f" {long_name=}, {standard_name=}, units\n\n{coordinate}\n\n{type(coordinate.values)} {coordinate.shape}"
        )

        return UnsupportedCoordinate(coordinate)

    def grid(self, coordinates: Any, variable: Any) -> Any:
        """Determines the grid type for the given coordinates and variable.

        Parameters
        ----------
        coordinates : Any
            The coordinates to determine the grid from.
        variable : Any
            The variable to determine the grid from.

        Returns
        -------
        Any
            The determined grid type.
        """
        lat = [c for c in coordinates if c.is_lat]
        lon = [c for c in coordinates if c.is_lon]

        if len(lat) == 1 and len(lon) == 1:
            return self._lat_lon_provided(lat, lon, variable)

        x = [c for c in coordinates if c.is_x]
        y = [c for c in coordinates if c.is_y]

        if len(x) == 1 and len(y) == 1:
            return self._x_y_provided(x, y, variable)

        raise NotImplementedError(f"Cannot establish grid {coordinates}")

    def _check_dims(self, variable: Any, x_or_lon: Any, y_or_lat: Any) -> Tuple[Any, bool]:
        """Checks the dimensions of the variable against the coordinates.

        Parameters
        ----------
        variable : Any
            The variable to check.
        x_or_lon : Any
            The x or longitude coordinate.
        y_or_lat : Any
            The y or latitude coordinate.

        Returns
        -------
        Tuple[Any, bool]
            The checked dimensions and a flag indicating if the grid is unstructured.
        """
        x_dims = set(x_or_lon.variable.dims)
        y_dims = set(y_or_lat.variable.dims)
        variable_dims = set(variable.dims)

        if not (x_dims <= variable_dims) or not (y_dims <= variable_dims):
            raise ValueError(
                f"Dimensions do not match {variable.name}{variable.dims} !="
                f" {x_or_lon.name}{x_or_lon.variable.dims} and {y_or_lat.name}{y_or_lat.variable.dims}"
            )

        variable_dims = tuple(v for v in variable.dims if v in (x_dims | y_dims))
        if x_dims == y_dims:
            # It's unstructured
            return variable_dims, True

        if len(x_dims) == 1 and len(y_dims) == 1:
            # It's a mesh
            return variable_dims, False

        raise ValueError(
            f"Cannot establish grid for {variable.name}{variable.dims},"
            f" {x_or_lon.name}{x_or_lon.variable.dims},"
            f" {y_or_lat.name}{y_or_lat.variable.dims}"
        )

    def _lat_lon_provided(self, lat: Any, lon: Any, variable: Any) -> Any:
        """Determines the grid type when latitude and longitude are provided.

        Parameters
        ----------
        lat : Any
            The latitude coordinate.
        lon : Any
            The longitude coordinate.
        variable : Any
            The variable to determine the grid from.

        Returns
        -------
        Any
            The determined grid type.
        """
        lat = lat[0]
        lon = lon[0]

        dim_vars, unstructured = self._check_dims(variable, lon, lat)

        if (lat.name, lon.name, dim_vars) in self._grid_cache:
            return self._grid_cache[(lat.name, lon.name, dim_vars)]

        grid: Grid = UnstructuredGrid(lat, lon, dim_vars) if unstructured else MeshedGrid(lat, lon, dim_vars)

        self._grid_cache[(lat.name, lon.name, dim_vars)] = grid

        return grid

    def _x_y_provided(self, x: Any, y: Any, variable: Any) -> Any:
        """Determines the grid type when x and y coordinates are provided.

        Parameters
        ----------
        x : Any
            The x coordinate.
        y : Any
            The y coordinate.
        variable : Any
            The variable to determine the grid from.

        Returns
        -------
        Any
            The determined grid type.
        """
        x = x[0]
        y = y[0]

        dim_vars, unstructured = self._check_dims(variable, x, y)

        if (x.name, y.name, dim_vars) in self._grid_cache:
            return self._grid_cache[(x.name, y.name, dim_vars)]

        grid_mapping = variable.attrs.get("grid_mapping", None)
        if grid_mapping is not None:
            print(f"grid_mapping: {grid_mapping}")
            print(self.ds[grid_mapping])

        if grid_mapping is None:
            LOG.warning(f"No 'grid_mapping' attribute provided for '{variable.name}'")
            LOG.warning("Trying to guess...")

            PROBE = {
                "prime_meridian_name",
                "reference_ellipsoid_name",
                "crs_wkt",
                "horizontal_datum_name",
                "semi_major_axis",
                "spatial_ref",
                "inverse_flattening",
                "semi_minor_axis",
                "geographic_crs_name",
                "GeoTransform",
                "grid_mapping_name",
                "longitude_of_prime_meridian",
            }
            candidate = None
            for v in self.ds.variables:
                var = self.ds[v]
                if not is_scalar(var):
                    continue

                if PROBE.intersection(var.attrs.keys()):
                    if candidate:
                        raise ValueError(f"Multiple candidates for 'grid_mapping': {candidate} and {v}")
                    candidate = v

            if candidate:
                LOG.warning(f"Using '{candidate}' as 'grid_mapping'")
                grid_mapping = candidate
            else:
                LOG.warning("Could not fine a candidate for 'grid_mapping'")

        if grid_mapping is None:
            if "crs" in self.ds[variable].attrs:
                grid_mapping = self.ds[variable].attrs["crs"]
                LOG.warning(f"Using CRS {grid_mapping} from variable '{variable.name}' attributes")

        if grid_mapping is None:
            if "crs" in self.ds.attrs:
                grid_mapping = self.ds.attrs["crs"]
                LOG.warning(f"Using CRS {grid_mapping} from global attributes")

        grid: Optional[Grid] = None
        if grid_mapping is not None:

            grid_mapping = dict(self.ds[grid_mapping].attrs)

            if unstructured:
                grid = UnstructuredProjectionGrid(x, y, grid_mapping)
            else:
                grid = MeshProjectionGrid(x, y, grid_mapping)

        if grid is not None:
            self._grid_cache[(x.name, y.name, dim_vars)] = grid
            return grid

        LOG.error("Could not fine a candidate for 'grid_mapping'")
        raise NotImplementedError(f"Unstructured grid {x.name} {y.name}")

    @abstractmethod
    def _is_longitude(
        self, c: xr.DataArray, attributes: CoordinateAttributes
    ) -> Optional[LongitudeCoordinate]:
        """Checks if the coordinate is a longitude.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[LongitudeCoordinate]
            The LongitudeCoordinate if matched, else None.
        """
        pass

    @abstractmethod
    def _is_latitude(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[LatitudeCoordinate]:
        """Checks if the coordinate is a latitude.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[LatitudeCoordinate]
            The LatitudeCoordinate if matched, else None.
        """
        pass

    @abstractmethod
    def _is_x(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[XCoordinate]:
        """Checks if the coordinate is an x coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[XCoordinate]
            The XCoordinate if matched, else None.
        """
        pass

    @abstractmethod
    def _is_y(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[YCoordinate]:
        """Checks if the coordinate is a y coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[YCoordinate]
            The YCoordinate if matched, else None.
        """
        pass

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


class DefaultCoordinateGuesser(CoordinateGuesser):
    """Default implementation of CoordinateGuesser."""

    def __init__(self, ds: xr.Dataset) -> None:
        """Initializes the DefaultCoordinateGuesser.

        Parameters
        ----------
        ds : xr.Dataset
            The dataset to guess coordinates from.
        """
        super().__init__(ds)

    def _is_longitude(
        self, c: xr.DataArray, attributes: CoordinateAttributes
    ) -> Optional[LongitudeCoordinate]:
        """Checks if the coordinate is a longitude.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[LongitudeCoordinate]
            The LongitudeCoordinate if matched, else None.
        """

        # https://cfconventions.org/Data/cf-conventions/cf-conventions-1.12/cf-conventions.html#longitude-coordinate

        if attributes.standard_name == "longitude":
            return LongitudeCoordinate(c)

        if attributes.long_name == "longitude" and attributes.units == "degrees_east":
            return LongitudeCoordinate(c)

        if attributes.name == "longitude":  # WeatherBench
            return LongitudeCoordinate(c)

        return None

    def _is_latitude(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[LatitudeCoordinate]:
        """Checks if the coordinate is a latitude.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[LatitudeCoordinate]
            The LatitudeCoordinate if matched, else None.
        """

        # https://cfconventions.org/Data/cf-conventions/cf-conventions-1.12/cf-conventions.html#latitude-coordinate

        if attributes.standard_name == "latitude":
            return LatitudeCoordinate(c)

        if attributes.long_name == "latitude" and attributes.units == "degrees_north":
            return LatitudeCoordinate(c)

        if attributes.name == "latitude":  # WeatherBench
            return LatitudeCoordinate(c)

        return None

    def _is_x(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[XCoordinate]:
        """Checks if the coordinate is an x coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[XCoordinate]
            The XCoordinate if matched, else None.
        """
        if attributes.standard_name in ["projection_x_coordinate", "grid_longitude"]:
            return XCoordinate(c)

        if attributes.name == "x":
            return XCoordinate(c)

        return None

    def _is_y(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[YCoordinate]:
        """Checks if the coordinate is a y coordinate.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[YCoordinate]
            The YCoordinate if matched, else None.
        """
        if attributes.standard_name in ["projection_y_coordinate", "grid_latitude"]:
            return YCoordinate(c)

        if attributes.name == "y":
            return YCoordinate(c)

        return None

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

        if attributes.long_name == "height" and attributes.units == "m":
            return LevelCoordinate(c, "height")

        if attributes.standard_name == "air_pressure" and attributes.units == "hPa":
            return LevelCoordinate(c, "pl")

        if attributes.name == "level":
            return LevelCoordinate(c, "pl")

        if attributes.name == "vertical" and attributes.units == "hPa":
            return LevelCoordinate(c, "pl")

        if attributes.standard_name == "depth":
            return LevelCoordinate(c, "depth")

        if attributes.name == "vertical" and attributes.units == "hPa":
            return LevelCoordinate(c, "pl")

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


class FlavourCoordinateGuesser(CoordinateGuesser):
    """Implementation of CoordinateGuesser that uses a flavour for guessing."""

    def __init__(self, ds: xr.Dataset, flavour: Dict[str, Any]) -> None:
        """Initializes the FlavourCoordinateGuesser.

        Parameters
        ----------
        ds : xr.Dataset
            The dataset to guess coordinates from.
        flavour : Dict[str, Any]
            The flavour to use for guessing.
        """
        super().__init__(ds)
        self.flavour = flavour

    def _match(self, c: xr.DataArray, key: str, attributes: CoordinateAttributes) -> Optional[Dict[str, Any]]:
        """Matches the coordinate against the flavour rules.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to match.
        key : str
            The key to match in the flavour rules.
        attributes : CoordinateAttributes
            The values to match against.

        Returns
        -------
        Optional[Dict[str, Any]]
            The matched rule if any, else None.
        """
        if key not in self.flavour["rules"]:
            return None

        rules = self.flavour["rules"][key]

        if not isinstance(rules, list):
            rules = [rules]

        for rule in rules:
            ok = True
            for k, v in rule.items():
                if isinstance(v, str) and attributes.get(k) != v:
                    ok = False
            if ok:
                return rule

        return None

    def _is_longitude(
        self, c: xr.DataArray, attributes: CoordinateAttributes
    ) -> Optional[LongitudeCoordinate]:
        """Checks if the coordinate is a longitude using the flavour rules.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[LongitudeCoordinate]
            The LongitudeCoordinate if matched, else None.
        """
        if self._match(c, "longitude", attributes):
            return LongitudeCoordinate(c)

        return None

    def _is_latitude(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[LatitudeCoordinate]:
        """Checks if the coordinate is a latitude using the flavour rules.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[LatitudeCoordinate]
            The LatitudeCoordinate if matched, else None.
        """
        if self._match(c, "latitude", attributes):
            return LatitudeCoordinate(c)

        return None

    def _is_x(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[XCoordinate]:
        """Checks if the coordinate is an x coordinate using the flavour rules.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[XCoordinate]
            The XCoordinate if matched, else None.
        """
        if self._match(c, "x", attributes):
            return XCoordinate(c)

        return None

    def _is_y(self, c: xr.DataArray, attributes: CoordinateAttributes) -> Optional[YCoordinate]:
        """Checks if the coordinate is a y coordinate using the flavour rules.

        Parameters
        ----------
        c : xr.DataArray
            The coordinate to check.
        attributes : CoordinateAttributes
            The attributes of the coordinate.

        Returns
        -------
        Optional[YCoordinate]
            The YCoordinate if matched, else None.
        """
        if self._match(c, "y", attributes):
            return YCoordinate(c)

        return None

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
            # assert False, rule
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
