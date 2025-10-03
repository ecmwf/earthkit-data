# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod
from typing import Optional
from typing import Union

from .level_type import LevelType
from .level_type import get_level_type
from .spec import Aliases
from .spec import SimpleSpec
from .spec import normalise_set_kwargs
from .spec import spec_aliases


class Vertical:
    def __init__(
        self,
        level: Union[int, float] = None,
        layer: Optional[tuple[float, float]] = None,
        type: Optional[Union[LevelType, str]] = None,
    ) -> None:
        self._level = level
        self._layer = layer
        self._type = get_level_type(type)

    @property
    def level(self) -> Union[int, float]:
        """Return the level."""
        return self._level

    @property
    def layer(self) -> Optional[tuple[float, float]]:
        """Return the layer."""
        return self._layer

    @property
    def cf(self):
        """Return the level type."""
        return self._type.cf

    @property
    def abbreviation(self):
        """Return the level type."""
        return self._type.abbreviation

    @property
    def units(self):
        """Return the level type."""
        return self._type.units

    @property
    def positive(self):
        """Return the level type."""
        return self._type.positive

    @property
    def type(self):
        """Return the level type."""
        return self._type.name

    def __print__(self):
        return f"{self.level} {self.units} ({self.abbreviation})"

    def __repr__(self):
        return f"{self.__class__.__name__}(level={self.level}, units={self.units}, type={self._type.name})"

    def __getstate__(self):
        state = {}
        state["level"] = self._level
        state["layer"] = self._layer
        state["type"] = self._type.name
        return state

    def __setstate__(self, state):
        self.__init__(level=state["level"], layer=state["layer"], type=state["type"])


@spec_aliases
class VerticalSpec(SimpleSpec):
    """A specification of a vertical level or layer."""

    KEYS = ("level", "layer", "cf", "abbreviation", "units", "positive", "type")
    SET_KEYS = ("level", "layer", "type")
    ALIASES = Aliases({"level": "levelist"})

    @property
    @abstractmethod
    def level(self) -> Union[int, float]:
        """Return the level."""
        pass

    @property
    @abstractmethod
    def layer(self) -> Optional[tuple[float, float]]:
        """str: Return the layer."""
        pass

    @property
    @abstractmethod
    def cf(self) -> dict:
        """str: Return the name of the level type."""
        pass

    @property
    @abstractmethod
    def abbreviation(self) -> str:
        """str: Return the abbreviation of the level type."""
        pass

    @property
    @abstractmethod
    def units(self) -> str:
        """str: Return the level units."""
        pass

    @property
    @abstractmethod
    def positive(self) -> str:
        """str: Return if the level values increase upwards."""
        pass

    @property
    @abstractmethod
    def type(self) -> str:
        """str: Return if the level values increase upwards."""
        pass


class SimpleVerticalSpec(VerticalSpec):
    """A specification of a vertical level or layer."""

    def __init__(self, data) -> None:
        assert isinstance(data, Vertical)
        self._data = data

    @property
    def data(self):
        """Return the level layer."""
        return self._data

    @property
    def level(self) -> Union[int, float]:
        return self._data.level

    @property
    def layer(self) -> str:
        return self._data.layer

    @property
    def cf(self) -> str:
        return self._data.cf

    @property
    def abbreviation(self) -> str:
        return self._data.abbreviation

    @property
    def units(self) -> str:
        return self._data.units

    @property
    def positive(self) -> bool:
        return self._data.positive

    @property
    def type(self) -> bool:
        return self._data.type

    @classmethod
    def from_dict(cls, d: dict) -> "SimpleVerticalSpec":
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
        # print("d=", d)
        d = normalise_set_kwargs(cls, add_spec_keys=False, **d)
        # print(" ->", d)
        data = Vertical(**d)
        return cls(data)

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

    def set(self, *args: dict, **kwargs):
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
        for k in kwargs:
            if k not in self.SET_KEYS:
                raise ValueError(f"Cannot set {k} in {self.__class__.__name__}")

        # kwargs.pop("level_units", None)
        # kwargs.pop("level", None)
        # kwargs.pop("level_type_name", None)
        # kwargs.pop("level_type_units", None)
        data = Vertical(**kwargs)
        spec = SimpleVerticalSpec(data)
        return spec

    def namespace(self, owner, name, result):
        if name is None or name == "vertical" or (isinstance(name, (list, tuple)) and "vertical" in name):
            result["vertical"] = self.to_dict()

    def check(self, owner):
        pass

    def __getstate__(self):
        state = {}
        state["data"] = self._data
        return state

    def __setstate__(self, state):
        self.__init__(data=state["data"])
