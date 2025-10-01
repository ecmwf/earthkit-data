# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

# from collections import namedtuple
from typing import Union

from .spec import SimpleSpec
from .spec import normalise_set_kwargs
from .spec import spec_aliases

# Vertical = namedtuple("Vertical", "level layer name long_name abbreviation units positive")


@spec_aliases
class Vertical(SimpleSpec):
    """A specification of a vertical level or layer."""

    KEYS = (
        "level",
        "layer",
        "name",
        "abbreviation",
        "units",
        "positive",
    )

    KEY_PREFIX = "vertical_"
    PREFIXED_KEYS = all
    DIRECT_KEYS = ("level", "layer")
    # PREFIXED_KEYS = Aliases(
    # {
    #     "level": ("level_value",),
    #     "layer": ("level_layer",),
    #     "name": ("level_name",),
    #     "units": ("level_units",),
    #     "positive": ("level_positive",),
    #     "abbreviation": ("level_abbreviation",),
    # })

    # SUB_KEYS = {"type": [("name", "level_name"), ("units", "level_units")]}

    @property
    @abstractmethod
    def level(self) -> Union[int, float]:
        """Return the level."""
        pass

    @property
    @abstractmethod
    def level_values(self) -> str:
        """str: Return the level type."""
        pass

    @property
    @abstractmethod
    def level_layer(self) -> str:
        """str: Return the level layer."""
        pass

    @property
    @abstractmethod
    def level_name(self) -> str:
        """str: Return the level type."""
        pass

    @property
    @abstractmethod
    def level_abbreviation(self) -> str:
        """str: Return the level type."""
        pass

    @property
    @abstractmethod
    def level_units(self) -> str:
        """str: Return the level type."""
        pass

    @property
    @abstractmethod
    def level_positive(self) -> bool:
        """str: Return the level units."""
        pass


# class Vertical:
#     def __init__(
#         self, level: Union[int, float], layer: Optional[tuple[float, float]], level_type: LevelType
#     ) -> None:
#         self._level = level
#         self._layer = layer
#         self._type = level_type

#     @property
#     def level(self) -> Union[int, float]:
#         """Return the level."""
#         return self._level

#     @property
#     def name(self) -> str:
#         """str: Return the level type."""
#         return self._type.name

#     @property
#     def long_name(self) -> str:
#         """str: Return the level type."""
#         return self._type.long_name

#     @property
#     def positive(self) -> bool:
#         """str: Return the level type."""
#         return self._type.positive

#     @property
#     def units(self) -> str:
#         """str: Return the level type units."""
#         return self._type.units

#     @property
#     def layer(self) -> Optional[tuple[float, float]]:
#         """str: Return the layer."""
#         return

#     # def __repr__(self):
#     #     return f"LevelInfo({self.value},{self.type.value.units},{self.type.name})"

#     # def ls(self):
#     #     return f"{self._level} {self._type.value.units} ({self._type.value.name})"

# class SimpleVerticalCore(VerticalSpec):
#     """A specification of a vertical level or layer."""

#     def __init__(self, level=None, layer=None, level_type=None) -> None:
#         self._level = level
#         self._layer = layer
#         self._level_type = level_type
#         assert level_type in LevelType


#     @property
#     @abstractmethod
#     def _data(self):
#         """Return the level layer."""
#         pass

#     @property
#     def level(self) -> Union[int, float]:
#         """Return the level."""
#         return Level(self._level, self._level_type)

#         @property
#         def level_value(self) -> str:
#         """str: Return the level type."""
#         return self._level

#     @property
#     def level_type(self) -> str:
#         """str: Return the level type."""
#         return self._level_type

#     @property
#     def level_type_name(self) -> str:
#         """str: Return the level type."""
#         return self._level_type.value.name

#     @property
#     def level_type_units(self) -> str:
#         """str: Return the level type."""
#         return self._level_type.value.units

#     @property
#     def level_units(self) -> str:
#         """str: Return the level units."""
#         return self._level_type.value.units

#     @classmethod
#     def from_dict(cls, d: dict) -> "Vertical":
#         """Create a Vertical object from a dictionary.

#         Parameters
#         ----------
#         d : dict
#             Dictionary containing vertical coordinate data.

#         Returns
#         -------
#         Vertical
#             The created Vertical instance.
#         """
#         if not isinstance(d, dict):
#             raise TypeError("d must be a dictionary")
#         d = normalise_set_kwargs(cls, add_spec_keys=False, **d)
#         return cls(**d)

#     # @classmethod
#     # def from_xarray(cls, owner, selection) -> "Vertical":
#     #     """Create a Vertical instance from an xarray dataset.

#     #     Parameters
#     #     ----------
#     #     handle
#     #         GRIB handle object.

#     #     Returns
#     #     -------
#     #     Vertical
#     #         The created Vertical instance.
#     #     """
#     #     from .xarray.vertical import from_xarray

#     #     r = cls(**from_xarray(owner, selection))
#     #     return r

#     def get_grib_context(self, context) -> dict:
#         from .grib.vertical import COLLECTOR

#         COLLECTOR.collect(self, context)

#     def to_dict(self) -> dict:
#         """Convert the object to a dictionary.

#         Returns
#         -------
#         dict
#             Dictionary representation of the object.
#         """
#         return {"level": self.level, "level_type": self.level_type, "units": self.level_units}

#     def set(self, *args: dict, **kwargs) -> "Vertical":
#         """
#         Create a new Vertical instance with updated data.

#         Parameters
#         ----------
#         *args : dict
#             Positional arguments.
#         **kwargs
#             Keyword arguments.

#         Returns
#         -------
#         Vertical
#             The created Vertical instance.
#         """
#         kwargs = normalise_set_kwargs(self, *args, **kwargs)
#         kwargs.pop("level_units", None)
#         kwargs.pop("level", None)
#         kwargs.pop("level_type_name", None)
#         kwargs.pop("level_type_units", None)
#         spec = SimpleVertical(**kwargs)
#         return spec

#     def namespace(self, owner, name, result):
#         if name is None or name == "vertical" or (isinstance(name, (list, tuple)) and "vertical" in name):
#             result["vertical"] = self.to_dict()

#     def check(self, owner):
#         print("checking vertical CORE")
#         pass

#     def __getstate__(self):
#         state = {}
#         state["level"] = self._level
#         state["level_type"] = self._level_type.name
#         return state

#     def __setstate__(self, state):
#         self.__init__(
#             level=state["level"],
#             level_type=state["level_type"],
#         )


class SimpleVertical(Vertical):
    """A specification of a vertical level or layer."""

    def __init__(self, level=None, layer=None, level_type=None) -> None:
        self._level = level
        self._layer = layer
        self._type = level_type
        # assert level_type in LevelType

    @property
    def level_value(self) -> Union[int, float]:
        """Return the level."""
        return self._level

    @property
    def level_name(self) -> str:
        """str: Return the level type."""
        return self._type

    @property
    def level_type_name(self) -> str:
        """str: Return the level type."""
        return self._level_type.value.name

    @property
    def level_type_units(self) -> str:
        """str: Return the level type."""
        return self._level_type.value.units

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
        kwargs.pop("level", None)
        kwargs.pop("level_type_name", None)
        kwargs.pop("level_type_units", None)
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
