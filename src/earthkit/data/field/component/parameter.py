# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

from .component import SimpleFieldComponent
from .component import component_keys
from .component import mark_alias
from .component import mark_key


@component_keys
class BaseParameter(SimpleFieldComponent):
    """A specification of a parameter."""

    @mark_key("get")
    @abstractmethod
    def variable(self) -> str:
        r"""str: Return the parameter variable."""
        pass

    @mark_key("get")
    @abstractmethod
    def units(self) -> str:
        r"""str: Return the parameter units."""
        pass

    @mark_alias("variable")
    def param(self) -> str:
        pass


def create_parameter(d: dict) -> "BaseParameter":
    """Create a BaseParameter object from a dictionary.

    Parameters
    ----------
    d : dict
        Dictionary containing parameter data.

    Returns
    -------
    BaseEnsemble
        The created BaseEnsemble instance.
    """
    if not isinstance(d, dict):
        raise TypeError(f"Cannot create Parameter from {type(d)}, expected dict")

    cls = Parameter
    d1 = cls.normalise_create_kwargs(d, allowed_keys=("variable", "units"))
    return cls(**d1)


class Parameter(BaseParameter):
    def __init__(self, variable: str = None, units: str = None) -> None:
        self._variable = variable
        self._units = units

    def variable(self) -> str:
        r"""str: Return the parameter variable."""
        return self._variable

    def units(self) -> str:
        r"""str: Return the parameter units."""
        return self._units

    @classmethod
    def from_dict(cls, d: dict) -> "Parameter":
        """Create a Parameter object from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing parameter data.

        Returns
        -------
        Parameter
            The created Parameter instance.
        """
        return create_parameter(d)

    def to_dict(self):
        return {"variable": self._variable, "units": self._units}

    def __getstate__(self):
        state = {}
        state["variable"] = self._variable
        state["units"] = self._units
        return state

    def __setstate__(self, state):
        self.__init__(variable=state["variable"], units=state["units"])

    def set(self, *args, **kwargs):
        d = self.normalise_set_kwargs(*args, allowed_keys=("variable", "units"), **kwargs)

        current = {
            "variable": self._variable,
            "units": self._units,
        }

        current.update(d)
        return self.from_dict(current)
