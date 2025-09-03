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
class Realisation(SimpleSpec):
    """Realisation specification."""

    KEYS = ("number",)
    ALIASES = Aliases({"number": ("realisation")})

    @property
    @abstractmethod
    def number(self) -> int:
        r"""int: Return the ensemble number."""
        pass


class SimpleRealisation(Realisation):
    """Realisation specification."""

    def __init__(self, *, number=0) -> None:
        self._number = number

    @property
    def number(self) -> int:
        return self._number

    @classmethod
    def from_dict(cls, d: dict) -> "SimpleRealisation":
        """Create a Realisation object from a dictionary.

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
        return {"number": self.number}

    def get_grib_context(self, context) -> dict:
        from .grib.realisation import get_grib_context

        get_grib_context(self, context)

    def set(self, *args, **kwargs) -> "SimpleRealisation":
        """
        Create a new SimpleRealisation instance with updated data.

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
        spec = SimpleRealisation(**kwargs)
        return spec

    def namespace(self, owner, name, result):
        if (
            name is None
            or name == "realisation"
            or (isinstance(name, (list, tuple)) and "realisation" in name)
        ):
            result["realisation"] = self.to_dict()

    def check(self, owner):
        pass
