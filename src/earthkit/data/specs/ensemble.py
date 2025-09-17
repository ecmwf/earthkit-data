# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

from .spec import Aliases
from .spec import SimpleSpec
from .spec import normalise_set_kwargs
from .spec import spec_aliases


@spec_aliases
class Ensemble(SimpleSpec):
    """Realisation specification."""

    KEYS = ("member",)
    ALIASES = Aliases({"member": ("realisation", "realization")})

    @property
    @abstractmethod
    def member(self) -> str:
        r"""int: Return the ensemble member."""
        pass


class SimpleEnsemble(Ensemble):
    """Ensemble specification."""

    def __init__(self, *, member=0) -> None:
        self._member = member

    @property
    def member(self) -> str:
        return self._member

    @classmethod
    def from_dict(cls, d: dict) -> "SimpleEnsemble":
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
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")
        d = normalise_set_kwargs(cls, add_spec_keys=False, **d)
        return cls(**d)

    def to_dict(self) -> dict:
        """Convert the object to a dictionary.

        Returns
        -------
        dict
            Dictionary representation of the object.
        """
        return {"member": self.member}

    def get_grib_context(self, context) -> dict:
        from .grib.ensemble import COLLECTOR

        COLLECTOR.collect(self, context)

    def set(self, *args, **kwargs) -> "SimpleEnsemble":
        """
        Create a new SimpleEnsemble instance with updated data.

        Parameters
        ----------
        *args
            Positional arguments.
        **kwargs
            Keyword arguments.

        Returns
        -------
        SimpleRealisation
            The created SimpleRealisation instance.
        """
        kwargs = normalise_set_kwargs(self, *args, **kwargs)
        spec = SimpleEnsemble(**kwargs)
        return spec

    def namespace(self, owner, name, result):
        if name is None or name == "ensemble" or (isinstance(name, (list, tuple)) and "ensemble" in name):
            result["realisation"] = self.to_dict()

    def check(self, owner):
        pass

    def __getstate__(self):
        state = {}
        state["member"] = self.member
        return state

    def __setstate__(self, state):
        self.__init__(member=state["member"])
