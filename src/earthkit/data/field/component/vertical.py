# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, Union

if TYPE_CHECKING:
    from earthkit.utils.units import Units

from .component import SimpleFieldComponent, component_keys, mark_get_key
from .level_type import LevelType, get_level_type


@component_keys
class VerticalBase(SimpleFieldComponent):
    """Base class for vertical coordinate component of a field.

    This class defines the interface for vertical components, which can represent different types of vertical
    information. Some of the methods may not be applicable to all vertical types (e.g. :meth:`layer`),
    and may return None.

    The vertical information can be accessed by methods like :meth:`level`, and :meth:`level_type`.
    Each of these methods has an associated key that can be used in the :meth:`get` method to retrieve
    the corresponding information. The list of supported keys are as follows:

    - "level"
    - "level_type"
    - "layer"
    - "cf"
    - "abbreviation"
    - "units"
    - "positive"

    Depending on the type of vertical information available, some of these keys may not be supported
    and will return None in the subclasses. For example, the "layer" key is only supported for certain
    vertical types, and will return None for other types.

    Typically, this object is used as a component of a field, and can be accessed via the
    :attr:`vertical` attribute of a field. The keys above can also be accessed via the :meth:`get` method
    of the field, using the "vertical." prefix.

    The following example demonstrates how to access the vertical information from a field using various
    methods and keys:

        >>> import earthkit.data as ekd
        >>> field = ekd.from_source("sample", "tuv_pl.grib").to_fieldlist()[0]
        >>> field.vertical.level()
        1000
        >>> field.vertical.get("level")
        1000
        >>> field.get("vertical.level")
        1000
        >>> field.vertical.level_type()
        'pressure'
        >>> field.vertical.get("level_type")
        'pressure'
        >>> field.get("vertical.level_type")
        'pressure'

    The vertical component is immutable. The :meth:`set` method to create a new instance with updated
    values. For example, the following code creates a new vertical component with an updated level:

        >>> new_vertical = field.vertical.set(level=500)
        >>> new_vertical.level()
        500

    We can also call the Field's :meth:`set` method to create a new field with an updated vertical
    component:

        >>> new_field = field.set({"vertical.level": 500})
        >>> new_field.vertical.level()
        500
    """

    @mark_get_key
    @abstractmethod
    def level(self) -> Union[int, float]:
        """Return the level."""
        pass

    @mark_get_key
    @abstractmethod
    def layer(self) -> Optional[tuple[float, float]]:
        """Return the layer.

        The layer is represented as a tuple of two values (bottom, top). The layer information is only
        available for certain vertical types, and will return None for other types.
        """
        pass

    @mark_get_key
    @abstractmethod
    def cf(self) -> Optional[dict]:
        """
        Return the CF metadata for the vertical coordinate.

        The CF metadata is a dictionary containing the following keys:
        - "standard_name": the CF standard name for the vertical coordinate
        - "long_name": the CF long name for the vertical coordinate
        - "positive": the positive direction of the vertical coordinate (e.g. "up" or "down")
        - "units": the units as str for the vertical coordinate
        """
        pass

    @mark_get_key
    @abstractmethod
    def abbreviation(self) -> Optional[str]:
        """Return the abbreviation of level type."""
        pass

    @mark_get_key
    @abstractmethod
    def units(self) -> Optional[Units]:
        """Return the units of the level type.

        The units are returned an :py:class:`earthkit.utils.units.Units` object.
        """
        pass

    @mark_get_key
    @abstractmethod
    def positive(self) -> Optional[str]:
        """Return the positive direction of the vertical coordinate.

        The positive direction is typically "up" or "down". It may return None if the positive direction
        is not defined for the vertical type.
        """
        pass

    @mark_get_key
    @abstractmethod
    def level_type(self) -> LevelType:
        """
        Return the level type.

        Returns
        -------
        LevelType
             The level type is returned as a :py:class:`LevelType` object.
        """
        pass


def create_vertical(d: dict) -> "Vertical":
    """Create a Vertical object from a dictionary.

    Parameters
    ----------
    d : dict
        Dictionary containing parameter data.

    Returns
    -------
    Vertica
        The created Vertical instance.
    """
    if not isinstance(d, dict):
        raise TypeError(f"Cannot create Vertical from {type(d)}, expected dict")

    cls = Vertical
    d1 = cls._normalise_create_kwargs(d, allowed_keys=("level", "layer", "level_type"))
    return cls(**d1)


class EmptyVertical(VerticalBase):
    """Empty vertical component, representing the absence of vertical information."""

    def __init__(self):
        self._type = get_level_type(None)

    def level(self) -> None:
        """Return the level.

        The level information is not available for this vertical type, and this method returns None.
        """
        return None

    def layer(self) -> None:
        """Return the layer.

        The layer information is not available for this vertical type, and this method returns None.
        """
        return None

    def cf(self) -> None:
        """Return the CF metadata for the level type.

        The CF metadata is not available for this vertical type, and this method returns None.
        """
        return None

    def abbreviation(self) -> None:
        """Return the abbreviation of level type.

        The abbreviation is not available for this vertical type, and this method returns None.
        """
        return None

    def units(self) -> None:
        """Return the units of  the level type.

        The units are not available for this vertical type, and this method returns None.
        """
        return None

    def positive(self) -> None:
        """Return the positive direction of the vertical coordinate.

        The positive direction is not available for this vertical type, and this method returns None.
        """
        return None

    def level_type(self) -> LevelType:
        """Return the level type.

        Returns an UnknownLevelType, indicating the absence of vertical information.
        """
        return self._type

    @classmethod
    def from_dict(cls, d: dict) -> "VerticalBase":
        """Create a Vertical object from a dictionary.

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

    def to_dict(self) -> dict:
        """Convert the object to a dictionary."""
        return {}

    def set(self, *args, **kwargs) -> None:
        """Create a new instance with updated data.

        An EmptyVertical object cannot be updated, and this method raises a
        ValueError if any data is provided.
        """
        raise ValueError("Cannot set values on EmptyVertical")

    def __getstate__(self) -> dict:
        return {}

    def __setstate__(self, state: dict) -> None:
        self.__init__()


class Vertical(VerticalBase):
    """Vertical component of a field, representing the vertical coordinate information.

    Parameters
    ----------
    level: int or float, optional
        The level value. The meaning of the level value depends on the ``level_type``.
    layer: tuple of two floats, optional
        The layer information, represented as a tuple of two values (bottom, top). The layer information is
        only applicable for certain vertical types, and may be None for other types.
    level_type: LevelType or str, optional
        The level type, which defines the type of vertical coordinate  (e.g. "pressure", "height",
        "isotherm", etc.). It can be specified as a LevelType object or as a string. If specified as
        a string, it will be converted to a LevelType object using the :func:`get_level_type` function.
        The level type is used to interpret the level and layer information, and to provide additional
        metadata such as units and CF attributes.
    """

    def __init__(
        self,
        level: Union[int, float] = None,
        layer: Optional[tuple[float, float]] = None,
        level_type: Optional[Union[LevelType, str]] = None,
    ) -> None:

        self._level = level
        self._layer = layer
        self._type = get_level_type(level_type)
        self._check()

    def level(self) -> Union[int, float]:
        return self._level

    def layer(self) -> Optional[tuple[float, float]]:
        return self._layer

    def cf(self) -> Optional[dict]:
        return self._type.cf

    def abbreviation(self) -> Optional[str]:
        return self._type.abbreviation

    def units(self) -> Optional[Units]:
        return self._type.units

    def positive(self) -> Optional[str]:
        return self._type.positive

    def level_type(self) -> LevelType:
        return self._type.name

    def __print__(self) -> str:
        return f"{self.level} {self.units} ({self.abbreviation})"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(level={self.level()}, units={self.units()}, level_type={self._type.name})"

    @classmethod
    def from_dict(cls, d: dict, allow_unused=False) -> "Vertical":
        """Create a Vertical object from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing vertical coordinate data.

            The dictionary can contain the following keys:

            - "level": The level value.
            - "layer": The layer information.
            - "level_type": The level type.

        The "level_type" key can be specified as a LevelType object or as a string. If
        specified as a string, it will be converted to a LevelType object using
        the :func:`get_level_type` function.

        Returns
        -------
        Vertical
            The created Vertical instance.
        """
        return create_vertical(d)

    def to_dict(self) -> dict:
        """Convert the object to a dictionary."""
        return {
            "level": self._level,
            "layer": self._layer,
            "level_type": self._type.name,
        }

    def __getstate__(self) -> dict:
        state = {}
        state["level"] = self._level
        state["layer"] = self._layer
        state["type"] = self._type.name
        return state

    def __setstate__(self, state: dict) -> None:
        self.__init__(level=state["level"], layer=state["layer"], level_type=state["level_type"])

    def _check(self) -> None:
        if self.layer() is not None:
            if len(self.layer()) != 2:
                raise ValueError("Layer must be a tuple of two values or None")

    def set(self, *args, **kwargs) -> "Vertical":
        """Create a new instance with updated data.

        Parameters
        ----------
        args : tuple
            Positional arguments containing time data. Only dictionaries are allowed.
        kwargs : dict
            Keyword arguments containing time data.

        Returns
        -------
        Vertical
            The created Vertical instance.


        The allowed keys in the dictionaries and keyword arguments are:

        - "level"
        - "layer"
        - "level_type"

        The "level_type" key can be specified as a LevelType object or as a string. If
        specified as a string, it will be converted to a LevelType object using
        the :func:`get_level_type` function.
        """
        d = self._normalise_set_kwargs(*args, allowed_keys=("level", "layer", "level_type"), **kwargs)

        current = {
            "level": self._level,
            "layer": self._layer,
            "level_type": self._type.name,
        }

        current.update(d)
        return self.from_dict(current)
