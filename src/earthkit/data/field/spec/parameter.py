# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .spec import mark_alias
from .spec import mark_key
from .spec import normalise_create_kwargs
from .spec import normalise_set_kwargs
from .spec import spec_keys


@spec_keys
class Parameter:
    """A specification of a parameter."""

    def __init__(self, variable: str = None, units: str = None) -> None:
        self._variable = variable
        self._units = units

    @mark_key("get", "set")
    def variable(self) -> str:
        r"""str: Return the parameter variable."""
        return self._variable

    @mark_key("get", "set")
    def units(self) -> str:
        r"""str: Return the parameter units."""
        return self._units

    @mark_alias("variable")
    def param(self) -> str:
        r"""str: Return the parameter variable (alias of `variable`)."""
        return self.variable()

    @classmethod
    def from_dict(cls, d: dict, allow_unused=False) -> "Parameter":
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

        d1 = normalise_create_kwargs(cls, d, allowed_keys=("variable", "units"), allow_unused=allow_unused)
        # print(" ->", d)
        return cls(**d1)

    def __getstate__(self):
        state = {}
        state["variable"] = self._variable
        state["units"] = self._units
        return state

    def __setstate__(self, state):
        self.__init__(variable=state["variable"], units=state["units"])

    def set(self, *args, **kwargs):
        d = normalise_set_kwargs(self, *args, allowed_keys=self._SET_KEYS, remove_nones=False, **kwargs)

        current = {
            "variable": self._variable,
            "units": self._units,
        }

        current.update(d)
        return self.from_dict(current)
