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

from .component import SimpleFieldComponent
from .component import component_keys
from .component import mark_get_key
from .level_type import LevelType
from .level_type import get_level_type


@component_keys
class BaseVertical(SimpleFieldComponent):
    @mark_get_key
    @abstractmethod
    def level(self) -> Union[int, float]:
        """Return the level."""
        pass

    @mark_get_key
    @abstractmethod
    def layer(self) -> Optional[tuple[float, float]]:
        """Return the layer."""
        pass

    @mark_get_key
    @abstractmethod
    def cf(self):
        """Return the level type."""
        pass

    @mark_get_key
    @abstractmethod
    def abbreviation(self):
        """Return the level type."""
        pass

    @mark_get_key
    @abstractmethod
    def units(self):
        """Return the level type."""
        pass

    @mark_get_key
    @abstractmethod
    def positive(self):
        """Return the level type."""
        pass

    @mark_get_key
    @abstractmethod
    def type(self):
        """Return the level type."""
        pass


def create_vertical(d: dict) -> "BaseVertical":
    """Create a BaseVertical object from a dictionary.

    Parameters
    ----------
    d : dict
        Dictionary containing parameter data.

    Returns
    -------
    BaseVertical
        The created BaseVertical instance.
    """
    if not isinstance(d, dict):
        raise TypeError(f"Cannot create Vertical from {type(d)}, expected dict")

    cls = Vertical
    d1 = cls.normalise_create_kwargs(d, allowed_keys=("level", "layer", "type"))
    return cls(**d1)


class EmptyVertical(BaseVertical):
    def __init__(self):
        self._type = get_level_type(None)

    def level(self) -> Union[int, float]:
        """Return the level."""
        return None

    def layer(self) -> Optional[tuple[float, float]]:
        """Return the layer."""
        return None

    def cf(self):
        """Return the level type."""
        return None

    def abbreviation(self):
        """Return the level type."""
        return None

    def units(self):
        """Return the level type."""
        return None

    def positive(self):
        """Return the level type."""
        return None

    def type(self):
        """Return the level type."""
        return self._type.name

    def from_dict(cls, d: dict) -> "EmptyVertical":
        """Create a NoVertical object from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing parameter data.

        Returns
        -------
        EmptyVertical
            The created EmptyVertical instance.
        """
        if d:
            return create_vertical(d)
        return cls()

    def to_dict(self):
        return {}

    def set(self, *args, **kwargs):
        raise ValueError("Cannot set values on EmptyVertical")

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        self.__init__()


class Vertical(BaseVertical):
    def __init__(
        self,
        level: Union[int, float] = None,
        layer: Optional[tuple[float, float]] = None,
        type: Optional[Union[LevelType, str]] = None,
    ) -> None:

        self._level = level
        self._layer = layer
        self._type = get_level_type(type)
        self._check()

    def level(self) -> Union[int, float]:
        """Return the level."""
        return self._level

    def layer(self) -> Optional[tuple[float, float]]:
        """Return the layer."""
        return self._layer

    def cf(self):
        """Return the level type."""
        return self._type.cf

    def abbreviation(self):
        """Return the level type."""
        return self._type.abbreviation

    def units(self):
        """Return the level type."""
        return self._type.units

    def positive(self):
        """Return the level type."""
        return self._type.positive

    def type(self):
        """Return the level type."""
        return self._type.name

    def __print__(self):
        return f"{self.level} {self.units} ({self.abbreviation})"

    def __repr__(self):
        return f"{self.__class__.__name__}(level={self.level()}, units={self.units()}, level_type={self._type.name})"

    @classmethod
    def from_dict(cls, d: dict, allow_unused=False) -> "Vertical":
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
        return create_vertical(d)

    def to_dict(self):
        return {
            "level": self._level,
            "layer": self._layer,
            "type": self._type.name,
        }

    def __getstate__(self):
        state = {}
        state["level"] = self._level
        state["layer"] = self._layer
        state["type"] = self._type.name
        return state

    def __setstate__(self, state):
        self.__init__(level=state["level"], layer=state["layer"], type=state["type"])

    def _check(self):
        if self.layer() is not None:
            if len(self.layer()) != 2:
                raise ValueError("Layer must be a tuple of two values or None")

    def set(self, *args, **kwargs):
        d = self.normalise_set_kwargs(*args, allowed_keys=("level", "layer", "type"), **kwargs)

        current = {
            "level": self._level,
            "layer": self._layer,
            "type": self._type.name,
        }

        current.update(d)
        return self.from_dict(current)
