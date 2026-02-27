# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import re
from abc import ABCMeta
from abc import abstractmethod

import pint
from pint import UnitRegistry

ureg = UnitRegistry()
Q_ = ureg.Quantity

UNITS_PATTERN = re.compile(r"([a-zA-Z])(-?\d+)")
UNIT_STR_ALIASES = {"(0 - 1)": "percent"}


def _prepare_str(units: str = None):
    """
    Convert a unit string to a Pint-compatible unit.

    For example, it converts "m s-1" to "m.s^-1".

    Parameters
    ----------
    units : str
        The unit string to convert.
    """

    if units is None:
        units = "dimensionless"

    if not isinstance(units, str):
        raise ValueError(f"Unsupported type for units: {type(units)}")

    if units in UNIT_STR_ALIASES:
        units = UNIT_STR_ALIASES[units]

    # Replace spaces with dots
    units = units.replace(" ", ".")

    # Insert ^ between characters and numbers (including negative numbers)
    units = UNITS_PATTERN.sub(r"\1^\2", units)

    return units


class Units(metaclass=ABCMeta):
    @abstractmethod
    def __repr__(self):
        pass

    @abstractmethod
    def __str__(self):
        pass

    @abstractmethod
    def __eq__(self):
        pass

    @abstractmethod
    def __hash__(self):
        pass

    @abstractmethod
    def __getstate__(self):
        pass

    @abstractmethod
    def __setstate__(self, state):
        pass

    @abstractmethod
    def to_pint(self):
        pass

    @staticmethod
    def from_any(units):
        if isinstance(units, str) or units is None:
            units = _prepare_str(units)
            try:
                return PintUnits(ureg(units).units)
            except (pint.errors.UndefinedUnitError, AssertionError, AttributeError):
                return UndefinedUnits(units)
        elif isinstance(units, pint.Unit):
            return PintUnits(units)
        elif isinstance(units, Units):
            return units

        else:
            raise ValueError(f"Unsupported type for units: {type(units)}")


class UndefinedUnits(Units):
    def __init__(self, units: str) -> None:
        self._units = units

    def __repr__(self):
        return self._units

    def __str__(self):
        return self._units

    def __eq__(self, other):
        other = Units.from_any(other)
        return str(other) == self._units

    def __hash__(self):
        return hash(str(self))

    def to_pint(self):
        return None

    def __getstate__(self):
        return {"units": self._units}

    def __setstate__(self, state):
        self._units = state["units"]


class PintUnits(Units):
    def __init__(self, units: pint.Unit) -> None:
        self._units = units

    def __repr__(self):
        return self._units.__repr__()

    def __str__(self):
        return str(self._units)

    def __eq__(self, other):
        other = Units.from_any(other)
        self_pint = self.to_pint()
        other_pint = other.to_pint()
        if self_pint is None and other_pint is None:
            return self_pint == other_pint

        return str(self) == str(other)

    def __hash__(self):
        return hash(str(self))

    def to_pint(self):
        return self._units

    @staticmethod
    def _to_pint(self, units):
        return ureg(units).units

    def __getattr__(self, name):
        return getattr(self._units, name)

    def __getstate__(self):
        return {"units": str(self)}

    def __setstate__(self, state):
        self._units = PintUnits._to_pint(self, state["units"])
