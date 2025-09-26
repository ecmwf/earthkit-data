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

from .level_type import LevelType
from .spec import Aliases
from .spec import SimpleSpec
from .spec import normalise_set_kwargs
from .spec import spec_aliases


@spec_aliases
class Vertical(SimpleSpec):
    """A specification of a vertical level or layer."""

    KEYS = (
        "level",
        "level_value",
        "level_type",
        "level_type_name",
        "level_type_units",
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


class LevelInfo:
    def __init__(self, value, type):
        self.value = value
        self.type = type

    def __repr__(self):
        return f"LevelInfo({self.value},{self.type.value.units},{self.type.name})"

    def ls(self):
        return f"{self.value} {self.type.value.units} ({self.type.value.name})"


class SimpleVertical(Vertical):
    """A specification of a vertical level or layer."""

    def __init__(self, level=None, level_type=None) -> None:
        self._level = level
        self._level_type = level_type
        assert level_type in LevelType

    @property
    def level(self) -> Union[int, float]:
        """Return the level."""
        return LevelInfo(self._level, self._level_type)

    @property
    def level_value(self) -> str:
        """str: Return the level type."""
        return self._level

    @property
    def level_type(self) -> str:
        """str: Return the level type."""
        return self._level_type

    @property
    def level_units(self) -> str:
        """str: Return the level units."""
        return self._level_type.value.units

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
        print("checking vertical CORE")
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
