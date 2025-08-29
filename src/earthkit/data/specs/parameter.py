# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .spec import Aliases
from .spec import SimpleSpec
from .spec import normalise_set_kwargs
from .spec import spec_aliases


@spec_aliases
class Parameter(SimpleSpec):
    """A specification of a parameter."""

    KEYS = (
        "name",
        "units",
    )

    ALIASES = Aliases({"name": ("param")})

    def __init__(self, name: str = None, units: str = None) -> None:
        self._name = name
        self._units = units

    @property
    def name(self) -> str:
        r"""str: Return the parameter name."""
        return self._name

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

    @classmethod
    def from_grib(cls, handle) -> "Parameter":
        """Create a Parameter instance from a GRIB handle.

        Parameters
        ----------
        handle
            GRIB handle object.

        Returns
        -------
        Parameter
            The created Parameter instance.
        """
        from .grib.parameter import from_grib

        spec = cls.from_dict(from_grib(handle))
        setattr(spec, "_handle", handle)
        return spec

    def _to_grib(self, **kwargs) -> dict:
        """Convert the object to a GRIB dictionary.

        Parameters
        ----------
        **kwargs
            Additional keyword arguments.

        Returns
        -------
        dict
            GRIB dictionary representation.
        """
        from .grib.parameter import to_grib

        return to_grib(self, **kwargs)

    def to_dict(self) -> dict:
        """Convert the object to a dictionary.

        Returns
        -------
        dict
            Dictionary representation of the object.
        """
        return {"name": self.name, "units": self.units}

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
        spec = Parameter(**kwargs)
        return spec
