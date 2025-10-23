# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from typing import Optional
from typing import Union

from .level_type import LevelType
from .level_type import get_level_type
from .spec import Aliases
from .spec import normalise_create_kwargs_2
from .spec import normalise_set_kwargs_2
from .spec import spec_aliases


@spec_aliases
class Vertical:
    # _KEYS = ("level", "layer", "cf", "abbreviation", "units", "positive", "type")
    _SET_KEYS = ("level", "layer", "type")
    _ALIASES = Aliases({"level": "levelist", "type": ("level_type",)})

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
        if not isinstance(d, dict):
            raise TypeError("d must be a dictionary")
        # print("d=", d)
        d1 = normalise_create_kwargs_2(cls, d, allowed_keys=cls._SET_KEYS, allow_unused=allow_unused)

        # print(" ->", d)
        return cls(**d1)

    def _check(self):
        if self.layer is not None:
            if len(self.layer) != 2:
                raise ValueError("Layer must be a tuple of two values or None")

    def set(self, *args, **kwargs):
        d = normalise_set_kwargs_2(self, *args, allowed_keys=self._SET_KEYS, remove_nones=False, **kwargs)

        current = {
            "level": self._level,
            "layer": self._layer,
            "type": self._type,
        }

        current.update(d)
        return self.from_dict(current)
