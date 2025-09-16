# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod
from typing import Union

from .level_type import LevelTypes
from .spec import Aliases
from .spec import SimpleSpec
from .spec import normalise_set_kwargs
from .spec import spec_aliases

# POSITIVE_UP = "up"
# POSITIVE_DOWN = "down"


# class LevelType:
#     def __init__(
#         self, name: str, standard_name: str, long_name: str, units: str, layer: bool, positive: str
#     ) -> None:
#         self.name = name
#         self.standard_name = standard_name
#         self.long_name = long_name
#         self.units = units
#         self.layer = layer
#         self.positive = positive

#     def __eq__(self, other):
#         return self.name == other.name


# _1 = {
#         "name": "pl",
#         "standard_name": "air_pressure",
#         "long_name": "pressure",
#         "units": "hPa",
#         "layer": False,
#         "positive": POSITIVE_DOWN,
#     }

# PRESSURE_LAYER = {
#     "name": "p_layer",
#     "standard_name": "air_pressure",
#     "long_name": "pressure",
#     "units": "hPa",
#     "layer": True,
#     "positive": POSITIVE_DOWN,
# }
# MODEL_LEVEL = {
#     "name": "ml",
#     "standard_name": "atmosphere_hybrid_sigma_pressure_coordinate",
#     "long_name": "hybrid level",
#     "units": "1",
#     "layer": False,
#     "positive": POSITIVE_DOWN,
# }
# THETA_LEVEL = {
#     "name": "pt",
#     "standard_name": "air_potential temperature",
#     "long_name": "air_potential temperature",
#     "units": "K",
#     "layer": False,
#     "positive": POSITIVE_UP,
# }
# PV_LEVEL = {
#     "name": "pv",
#     "standard_name": "ertel_potential vorticity",
#     "long_name": "potential vorticity",
#     "units": "10-9 K m2 kg-1 s-1",
#     "layer": False,
#     "positive": POSITIVE_DOWN,
# }
# HEIGHT_ASL_LEVEL = {
#     "name": "h_asl",
#     "standard_name": "height_above_sea_level",
#     "long_name": "height above mean sea level",
#     "units": "m",
#     "layer": False,
#     "positive": POSITIVE_UP,
# }
# HEIGHT_AGL_LEVEL = {
#     "name": "h_agl",
#     "standard_name": "height",
#     "long_name": "height above the surface",
#     "units": "m",
#     "layer": False,
#     "positive": POSITIVE_UP,
# }
# SURFACE_LEVEL = {
#     "name": "sfc",
#     "standard_name": "surface",
#     "long_name": "surface",
#     "units": "",
#     "layer": False,
# }
# DEPTH_BGL_LEVEL = {
#     "name": "d_bgl",
#     "standard_name": "depth",
#     "long_name": "soil depth",
#     "units": "m",
#     "layer": False,
#     "positive": POSITIVE_DOWN,
# }
# GENERAL_LEVEL = {
#     "name": "general",
#     "standard_name": "general",
#     "long_name": "general",
#     "units": "1",
#     "layer": False,
#     "positive": POSITIVE_DOWN,
# }
# MEAN_SEA_LEVEL = {
#     "name": "mean_sea",
#     "standard_name": "mean_sea",
#     "long_name": "mean sea level",
#     "units": "",
#     "layer": False,
#     "positive": POSITIVE_DOWN,
# }
# SNOW_LAYER = {
#     "name": "snow",
#     "standard_name": "unknown",
#     "long_name": "snow layer",
#     "units": "1",
#     "layer": False,
#     "positive": POSITIVE_DOWN,
# }
# UNKNOWN_LEVEL = {
#     "name": "unknown",
#     "standard_name": "unknown",
#     "long_name": "unknown",
#     "units": "",
#     "layer": False,
#     "positive": POSITIVE_DOWN,
# }


# class LevelType:
#     def __init__(
#         self, name: str, standard_name: str, long_name: str, units: str, layer: bool, positive: str
#     ) -> None:
#         self.name = name
#         self.units = units
#         self.layer = layer
#         self.positive = positive


# LEVEL_TYPES = {
#     item[0]: LevelType(*item)
#     for item in [
#         PRESSURE_LEVEL,
#         MODEL_LEVEL,
#         THETA_LEVEL,
#         PV_LEVEL,
#         HEIGHT_ASL_LEVEL,
#         HEIGHT_AGL_LEVEL,
#         SURFACE_LEVEL,
#         DEPTH_BGL_LEVEL,
#         GENERAL_LEVEL,
#         MEAN_SEA_LEVEL,
#         UNKNOWN_LEVEL,
#     ]
# }

# UNKNOWN_LEVEL_TYPE = LEVEL_TYPES["unknown"]

# class LevelTypes:
#     PRESSURE  =


@spec_aliases
class Vertical(SimpleSpec):
    """A specification of a vertical level or layer."""

    KEYS = (
        "level",
        "level_type",
        "level_units",
    )

    ALIASES = Aliases({"level": ("levelist")})

    @property
    @abstractmethod
    def level(self) -> Union[int, float]:
        """Return the level."""
        pass

    @property
    @abstractmethod
    def level_type(self) -> str:
        """str: Return the level type."""
        pass

    @property
    @abstractmethod
    def level_units(self) -> str:
        """str: Return the level units."""
        pass


class SimpleVertical(Vertical):
    """A specification of a vertical level or layer."""

    KEYS = (
        "level",
        "level_type",
        "level_units",
    )

    ALIASES = Aliases({"level": ("levelist")})

    def __init__(self, level: str = None, level_type: str = None) -> None:
        self._level = level
        self._level_type = LevelTypes.get(level_type)

    @property
    def level(self) -> Union[int, float]:
        """Return the level."""
        return self._level

    @property
    def level_type(self) -> str:
        """str: Return the level type."""
        return self._level_type.name

    @property
    def level_units(self) -> str:
        """str: Return the level units."""
        return self._level_type.units

    @classmethod
    def from_dict(cls, d: dict) -> "Vertical":
        """Create a Vertical object from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing vertical coordinate data.

        Returns
        -------
        Vertical
            The created Vertical instance.
        """
        if not isinstance(d, dict):
            raise TypeError("d must be a dictionary")
        d = normalise_set_kwargs(cls, add_spec_keys=False, **d)
        return cls(**d)

    # @classmethod
    # def from_xarray(cls, owner, selection) -> "Vertical":
    #     """Create a Vertical instance from an xarray dataset.

    #     Parameters
    #     ----------
    #     handle
    #         GRIB handle object.

    #     Returns
    #     -------
    #     Vertical
    #         The created Vertical instance.
    #     """
    #     from .xarray.vertical import from_xarray

    #     r = cls(**from_xarray(owner, selection))
    #     return r

    def get_grib_context(self, context) -> dict:
        from .grib.vertical import COLLECTOR

        COLLECTOR.collect(self, context)

    def to_dict(self) -> dict:
        """Convert the object to a dictionary.

        Returns
        -------
        dict
            Dictionary representation of the object.
        """
        return {"level": self.level, "level_type": self.level_type, "units": self.level_units}

    def set(self, *args: dict, **kwargs) -> "Vertical":
        """
        Create a new Vertical instance with updated data.

        Parameters
        ----------
        *args : dict
            Positional arguments.
        **kwargs
            Keyword arguments.

        Returns
        -------
        Vertical
            The created Vertical instance.
        """
        kwargs = normalise_set_kwargs(self, *args, **kwargs)
        kwargs.pop("level_units", None)
        spec = SimpleVertical(**kwargs)
        return spec

    def namespace(self, owner, name, result):
        if name is None or name == "vertical" or (isinstance(name, (list, tuple)) and "vertical" in name):
            result["vertical"] = self.to_dict()

    def check(self, owner):
        pass

    def __getstate__(self):
        state = {}
        state["level"] = self._level
        state["level_type"] = self._level_type.name
        return state

    def __setstate__(self, state):
        self.__init__(
            level=state["level"],
            level_type=state["level_type"],
        )
