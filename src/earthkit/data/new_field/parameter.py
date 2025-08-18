# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import ABCMeta
from abc import abstractmethod


class Parameter(metaclass=ABCMeta):
    KEYS = (
        "name",
        "units",
    )

    ALIASES = {
        "param": "name",
    }

    @property
    @abstractmethod
    def name(self):
        """Return the name of the parameter."""
        pass

    @property
    def param(self):
        """Return the parameter ID."""
        return self.name

    @property
    @abstractmethod
    def units(self):
        """Return the units of the parameter."""
        pass

    def set(self, **kwargs):
        """Set the name and/or units of the parameter."""
        for key, value in kwargs.items():
            key = self._resolve_key(key)
            if key in self.KEYS:
                setattr(self, f"_{key}", value)

    def to_dict(self, **kwargs):
        """Convert the Parameter object to a dictionary."""
        return {key: getattr(self, key) for key in self.KEYS}

    def _resolve_key(self, key):
        """Resolve a key to its canonical form."""
        return self.ALIASES.get(key, key)


class ParamSpec(Parameter):
    """A specification of a parameter."""

    def __init__(self, name=None, units=None):
        self._name = name
        self._units = units

    @property
    def name(self):
        return self._name

    @property
    def units(self):
        return self._units

    def set_name(self, name):
        """Set the name of the parameter."""
        self._name = name

    def set_units(self, units):
        """Set the units of the parameter."""
        self._units = units

    @classmethod
    def from_dict(cls, data):
        """Create a UserTime object from a dictionary."""
        if not isinstance(data, dict):
            raise TypeError("data must be a dictionary")
        return cls(**data)

    @classmethod
    def from_grib(cls, handle):
        def _get(key, default=None):
            return handle.get(key, default)

        v = _get("shortName ", None)
        if v is None:
            v = _get("param", None)
        name = v

        units = _get("units", None)

        return cls(
            name=name,
            units=units,
        )

    def to_dict(self):
        """Convert the TimeSpec object to a dictionary."""
        return {"name": self.name, "units": self.units}
