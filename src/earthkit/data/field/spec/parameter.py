# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .spec import Aliases
from .spec import normalise_create_kwargs_2
from .spec import normalise_set_kwargs_2
from .spec import spec_aliases

# from .spec import SimpleSpec
# from .spec import normalise_set_kwargs
# from .spec import spec_aliases

# from abc import abstractmethod


# from .spec import SimpleSpec
# from .spec import normalise_set_kwargs
# from .spec import spec_aliases


@spec_aliases
class Parameter:
    """A specification of a parameter."""

    _SET_KEYS = (
        "variable",
        "units",
    )

    _ALIASES = Aliases({"variable": ("param")})

    def __init__(self, variable: str = None, units: str = None) -> None:
        self._variable = variable
        self._units = units

    @property
    def variable(self) -> str:
        r"""str: Return the parameter variable."""
        return self._variable

    @property
    def units(self) -> str:
        r"""str: Return the parameter units."""
        return self._units

    @classmethod
    def from_dict(cls, d: dict):
        """Create a Ensemble object from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing parameter data.

        Returns
        -------
        Realisation
            The created Realisation instance.
        """

        d = normalise_create_kwargs_2(cls, allowed_keys=cls._SET_KEYS, **d)
        # print(" ->", d)
        return cls(**d)

    def __getstate__(self):
        state = {}
        state["member"] = self._member
        return state

    def __setstate__(self, state):
        self.__init__(member=state["member"])

    def set(self, *args, **kwargs):
        d = normalise_set_kwargs_2(self, *args, allowed_keys=self._SET_KEYS, remove_nones=False, **kwargs)

        current = {
            "variable": self._variable,
            "units": self._units,
        }

        current.update(d)
        return self.from_dict(current)
