# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

from .part import SimpleFieldPart
from .part import mark_alias
from .part import mark_key
from .part import part_keys


@part_keys
class BaseEnsemble(SimpleFieldPart):
    @mark_key("get")
    @abstractmethod
    def member(self) -> str:
        """Return the ensemble member."""
        pass

    @mark_alias("member")
    def realization(self) -> str:
        """Return the ensemble member (alias of `member`)."""
        pass

    @mark_alias("member")
    def realisation(self) -> str:
        """Return the ensemble member (alias of `member`)."""
        pass


def create_ensemble(d: dict) -> "BaseEnsemble":
    """Create a BaseEnsemble object from a dictionary.

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
        raise TypeError(f"Cannot create Ensemble from {type(d)}, expected dict")

    cls = Ensemble
    d1 = cls.normalise_create_kwargs(d, allowed_keys=("member",))
    return cls(**d1)


class Ensemble(BaseEnsemble):
    def __init__(self, member=None) -> None:
        if member is None:
            self._member = "0"
        elif isinstance(member, int):
            self._member = str(member)
        else:
            self._member = member

    def member(self) -> str:
        """Return the ensemble member."""
        return self._member

    @classmethod
    def from_dict(cls, d: dict) -> "Ensemble":
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
        return create_ensemble(d)

    def to_dict(self):
        return {"member": self._member}

    def set(self, *args, **kwargs):
        d = self.normalise_set_kwargs(*args, allowed_keys=("member",), **kwargs)

        if d:
            return self.from_dict(d)
        else:
            return Ensemble(member=self._member)

    def __getstate__(self):
        state = {}
        state["member"] = self._member
        return state

    def __setstate__(self, state):
        self.__init__(member=state["member"])
