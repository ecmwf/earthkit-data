# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from typing import Union

from .spec import Aliases
from .spec import SimpleSpec
from .spec import normalise_set_kwargs
from .spec import spec_aliases

PRESSURE_LEVEL = ("pl", "hPa", False)
MODEL_LEVEL = ("ml", "", False)
THETA_LEVEL = ("pt", "K", False)
PV_LEVEL = ("pv", "10-9 K m2 kg-1 s-1", False)
HEIGHT_ASL_LEVEL = ("h_asl", "m", False)
HEIGHT_AGL_LEVEL = ("h_agl", "m", False)
SURFACE_LEVEL = ("sfc", "", False)
DEPTH_BGL_LEVEL = ("d_bgl", "m", False)
GENERAL_LEVEL = ("general", "", False)
MEAN_SEA_LEVEL = ("mean_sea", "", False)
UNKNOWN_LEVEL = ("unknown", "", False)


class LevelType:
    def __init__(self, name: str, units: str, layer: bool) -> None:
        self.name = name
        self.units = units
        self.layer = layer


LEVEL_TYPES = {
    item[0]: LevelType(*item)
    for item in [
        PRESSURE_LEVEL,
        MODEL_LEVEL,
        THETA_LEVEL,
        PV_LEVEL,
        HEIGHT_ASL_LEVEL,
        HEIGHT_AGL_LEVEL,
        SURFACE_LEVEL,
        DEPTH_BGL_LEVEL,
        GENERAL_LEVEL,
        MEAN_SEA_LEVEL,
        UNKNOWN_LEVEL,
    ]
}

UNKNOWN_LEVEL_TYPE = LEVEL_TYPES["unknown"]


@spec_aliases
class Vertical(SimpleSpec):
    """A specification of a vertical level or layer."""

    KEYS = (
        "level",
        "level_type",
        "level_units",
    )

    ALIASES = Aliases({"level": ("levelist")})

    def __init__(self, level: str = None, level_type: str = None) -> None:
        self._level = level

        if isinstance(level_type, LevelType):
            self._level_type = level_type
        else:
            self._level_type = LEVEL_TYPES.get(level_type, UNKNOWN_LEVEL_TYPE)

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

    @classmethod
    def from_grib(cls, handle) -> "Vertical":
        """Create a Vertical instance from a GRIB handle.

        Parameters
        ----------
        handle
            GRIB handle object.

        Returns
        -------
        Vertical
            The created Vertical instance.
        """
        from .grib.vertical import from_grib

        r = cls(**from_grib(handle))
        setattr(r, "_handle", handle)
        return r

    @classmethod
    def from_xarray(cls, owner, selection) -> "Vertical":
        """Create a Vertical instance from an xarray dataset.

        Parameters
        ----------
        handle
            GRIB handle object.

        Returns
        -------
        Vertical
            The created Vertical instance.
        """
        from .xarray.vertical import from_xarray

        r = cls(**from_xarray(owner, selection))
        return r

    def _to_grib(self, altered: bool = True) -> dict:
        """Convert the object to a GRIB dictionary.

        Parameters
        ----------
        altered : bool, optional
            Whether to alter the GRIB dictionary, by default True.

        Returns
        -------
        dict
            GRIB dictionary representation.
        """
        from .grib.vertical import to_grib

        return to_grib(self, altered=altered)

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
        spec = Vertical(**kwargs)
        return spec
