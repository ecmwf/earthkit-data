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


@spec_aliases
class Ensemble:
    _SET_KEYS = ("member",)
    _ALIASES = Aliases({"member": ("realisation", "realization")})

    def __init__(self, member=None) -> None:
        if member is None:
            self._member = "0"
        elif isinstance(member, int):
            self._member = str(member)
        else:
            self._member = member

    @property
    def member(self) -> str:
        """Return the ensemble member."""
        return self._member

    @classmethod
    def from_dict(cls, d: dict, allow_unused=False) -> "Ensemble":
        """Create a Ensemble object from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing parameter data.

        Returns
        -------
        Ensemble
            The created Ensemble instance.
        """

        d1 = normalise_create_kwargs_2(
            cls, d, allowed_keys=cls._SET_KEYS, allow_unused=allow_unused, remove_nones=True
        )
        return cls(**d1)

    def __getstate__(self):
        state = {}
        state["member"] = self._member
        return state

    def __setstate__(self, state):
        self.__init__(member=state["member"])

    def set(self, *args, **kwargs):
        d = normalise_set_kwargs_2(self, *args, allowed_keys=self._SET_KEYS, remove_nones=False, **kwargs)

        if d:
            return self.from_dict(d)
        else:
            return Ensemble(member=self._member)
