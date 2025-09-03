# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from sklearn.naive_bayes import abstractmethod

from .spec import Aliases
from .spec import SimpleSpec
from .spec import normalise_set_kwargs
from .spec import spec_aliases


@spec_aliases
class Parameter(SimpleSpec):
    """A specification of a parameter."""

    KEYS = (
        "variable",
        "units",
    )

    ALIASES = Aliases({"variable": ("param")})

    @property
    @abstractmethod
    def variable(self) -> str:
        r"""str: Return the parameter variable."""
        pass

    @property
    @abstractmethod
    def units(self) -> str:
        r"""str: Return the parameter units."""
        pass


class SimpleParameter(Parameter):
    """A specification of a parameter."""

    KEYS = (
        "variable",
        "units",
    )

    ALIASES = Aliases({"variable": ("param")})

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
    def from_dict(cls, d: dict) -> "Parameter":
        """Create a UserTime object from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing parameter data.

        Returns
        -------
        ParameterSpec
            The created Parameter instance.
        """
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")
        d = normalise_set_kwargs(cls, add_spec_keys=False, **d)
        return cls(**d)

    # @classmethod
    # def from_grib(cls, handle) -> "Parameter":
    #     """Create a Parameter instance from a GRIB handle.

    #     Parameters
    #     ----------
    #     handle
    #         GRIB handle object.

    #     Returns
    #     -------
    #     Parameter
    #         The created Parameter instance.
    #     """
    #     from .grib.parameter import from_grib

    #     spec = cls.from_dict(from_grib(handle))
    #     setattr(spec, "_handle", handle)
    #     return spec

    # @classmethod
    # def from_xarray(cls, owner, selection) -> "Parameter":
    #     from .xarray.parameter import from_xarray

    #     return cls.from_dict(from_xarray(owner, selection))

    def get_grib_context(self, context) -> dict:
        from .grib.parameter import get_grib_context

        get_grib_context(self, context)

    def to_dict(self) -> dict:
        """Convert the object to a dictionary.

        Returns
        -------
        dict
            Dictionary representation of the object.
        """
        return {"variable": self.variable, "units": self.units}

    def set(self, *args, **kwargs) -> "Parameter":
        """
        Create a new Parameter instance with updated data.

        Parameters
        ----------
        *args
            Positional arguments.
        **kwargs
            Keyword arguments.

        Returns
        -------
        Parameter
            The created Parameter instance.
        """
        kwargs = normalise_set_kwargs(self, *args, **kwargs)
        spec = SimpleParameter(**kwargs)
        return spec

    def namespace(self, owner, name, result):
        if name is None or name == "parameter" or (isinstance(name, (list, tuple)) and "parameter" in name):
            result["parameter"] = self.to_dict()

    def check(self, owner):
        pass
