# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from __future__ import annotations

from abc import abstractmethod
from typing import TYPE_CHECKING, Optional, Union

from earthkit.utils.units import Units

from .component import SimpleFieldComponent, component_keys, mark_alias, mark_get_key

if TYPE_CHECKING:
    from earthkit.utils.units import Units


@component_keys
class ParameterBase(SimpleFieldComponent):
    """Base class for the parameter component of a field.

    This class defines the interface for parameter components, which can represent
    different types of parameter information. Some of the methods may not be applicable to all parameter
    types (e.g. :meth:`chem_variable`), and may return None.

    The parameter information can be accessed by methods like :meth:`variable`,
    :meth:`units`, and :meth:`chem_variable`. Each of these methods has an associated key
    that can be used in the :meth:`get` method to retrieve the corresponding information. The list
    of supported keys are as follows:

    - "variable": string representing the parameter variable
    - "standard_name": string representing the standard name of the parameter variable, based
       on the CF standard name
    - "long_name": string representing the long name of the parameter variable
    - "units": as a string or a :class:`Units` object representing the parameter units
    - "chem_variable": string representing the parameter chemical variable
    - "param": alias of "variable"

    Depending on the type of parameter information available, some of these keys may not be supported
    and will return None in the subclasses. For example, the "chem_variable" key is only supported
    for chemical parameters, and will return None for other parameter types.

    Typically, this object is used as a component of a field, and can be accessed via the :attr:`parameter`
    attribute of a field. The keys above can also be accessed via the :meth:`get` method of the field,
    using the "parameter." prefix.

    The following example demonstrates how to access the parameter information from a field using
    various methods and keys:

        >>> import earthkit.data as ekd
        >>> field = ekd.from_source("sample", "test.grib").to_fieldlist()[0]
        >>> field.parameter.variable()
        '2t'
        >>> field.parameter.get("variable")
        '2t'
        >>> field.get("parameter.variable")
        '2t'

    The parameter component is immutable. The :meth:`set` method to create a new
    instance with updated values. For example, the following code creates a new parameter
    component with an updated variable:

        >>> new_parameter = field.parameter.set(variable="msl", units="Pa")
        >>> new_parameter.variable()
        'msl'

    We can also call the Field's :meth:`set` method to create a new field with an updated parameter component:

        >>> new_field = field.set({"parameter.variable": "msl", "parameter.units": "Pa"})
        >>> new_field.parameter.variable()
        'msl'

    """

    @mark_get_key
    @abstractmethod
    def variable(self) -> Optional[str]:
        r"""Return the parameter variable.

        The parameter variable is a string representing the parameter variable. At the moment it
        not normalised, but takes the value as it is in the source data. For example, for GRIB data,
        it will be the value of the "shortName" key in the GRIB message.
        """
        pass

    @mark_get_key
    @abstractmethod
    def units(self) -> Optional["Units"]:
        r"""Return the parameter units.

        The parameter units are :class:`Units` objects. The units are are based on Pint (when possible)
        and are normalised to a standard form. They can be used for unit conversions and comparisons.
        """
        pass

    @mark_get_key
    @abstractmethod
    def chem_variable(self) -> Optional[str]:
        r"""Return the parameter chemical variable."""
        pass

    @mark_alias("variable")
    def param(self) -> Optional[str]:
        pass

    @mark_get_key
    @abstractmethod
    def standard_name(self) -> Optional[str]:
        """Return the standard name of the parameter variable.

        The standard name is a string representing the standard name of the parameter variable. It is
        based on the CF standard name.
        """
        pass

    @mark_get_key
    @abstractmethod
    def long_name(self) -> Optional[str]:
        """Return the long name of the parameter variable.

        The long name is a string representing the long name of the parameter variable
        """
        pass


def create_parameter(d: dict) -> "ParameterBase":
    """Create a ParameterBase object from a dictionary.

    Parameters
    ----------
    d : dict
        Dictionary containing parameter data.

    Returns
    -------
    ParameterBase
        The created ParameterBase instance.
    """
    if not isinstance(d, dict):
        raise TypeError(f"Cannot create Parameter from {type(d)}, expected dict")

    cls = Parameter
    d1 = cls._normalise_create_kwargs(
        d, allowed_keys=("variable", "units", "chem_variable", "standard_name", "long_name")
    )
    if "variable" not in d1:
        raise ValueError("Cannot create Parameter without variable")

    return cls(**d1)


class EmptyParameter(ParameterBase):
    """Empty parameter component, representing the absence of parameter information."""

    def variable(self) -> None:
        r"""Return the parameter variable.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    def standard_name(self) -> None:
        r"""Return the standard name of the parameter variable.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    def long_name(self) -> None:
        r"""Return the long name of the parameter variable.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    def units(self) -> None:
        r"""Return the parameter units.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    def chem_variable(self) -> None:
        r"""Return the parameter chemical variable.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    @classmethod
    def from_dict(cls, d: dict) -> "ParameterBase":
        """Create an EmptyParameter object from a dictionary."""
        if d:
            return create_parameter(d)
        return cls()

    def to_dict(self):
        """Return a dictionary representation of the EmptyParameter."""
        return {"variable": None, "units": None}

    def set(self, *args, **kwargs):
        """Create a new instance with updated data.

        An EmptyParameter object cannot be updated, and this method raises a ValueError.
        """
        raise ValueError("Cannot set values on MissingParameter")

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        self.__init__()


class Parameter(ParameterBase):
    """Parameter component representing parameter information.

    Parameters
    ----------
    variable : str, optional
        The parameter variable, by default None.
    units : str or Units, optional
        The parameter units, by default None. Can be provided as a string or a Units object.
    chem_variable : str, optional
        The parameter chemical variable, by default None.
    """

    _chem_variable = None

    def __init__(
        self,
        variable: str = None,
        standard_name: str = None,
        long_name: str = None,
        units: Union[str, "Units"] = None,
        chem_variable: str = None,
    ) -> None:
        self._variable = variable
        self._standard_name = standard_name
        self._long_name = long_name
        self._units = Units.from_any(units)
        if chem_variable is not None:
            self._chem_variable = chem_variable

    def variable(self) -> Optional[str]:
        return self._variable

    def standard_name(self) -> Optional[str]:
        return self._standard_name

    def long_name(self) -> Optional[str]:
        return self._long_name

    def units(self) -> Optional["Units"]:
        return self._units

    def chem_variable(self) -> Optional[str]:
        return self._chem_variable

    @classmethod
    def from_dict(cls, d: dict) -> "Parameter":
        """Create a Parameter object from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing parameter data.

            The dictionary can contain the following keys:

            - "variable": The parameter variable.
            - "units": The parameter units, as a string or a Units object.

        Returns
        -------
        Parameter
            The created Parameter instance.
        """
        return create_parameter(d)

    def to_dict(self):
        return {
            "variable": self._variable,
            "standard_name": self._standard_name,
            "long_name": self._long_name,
            "units": str(self._units),
            "chem_variable": self._chem_variable,
        }

    def __getstate__(self):
        state = {}
        state["variable"] = self._variable
        state["standard_name"] = self._standard_name
        state["long_name"] = self._long_name
        state["units"] = str(self._units)
        state["chem_variable"] = self._chem_variable
        return state

    def __setstate__(self, state):
        self.__init__(
            variable=state["variable"],
            standard_name=state["standard_name"],
            long_name=state["long_name"],
            units=state["units"],
            chem_variable=state["chem_variable"],
        )

    def set(self, *args, **kwargs):
        """Create a new instance with updated data.

        Parameters
        ----------
        args : tuple
            Positional arguments containing parameter data. Only dictionaries are allowed.
        kwargs : dict
            Keyword arguments containing parameter data.

        The following keys can be provided to update the parameter information:

            - "variable": The parameter variable.
            - "units": The parameter units, as a string or a Units object.
            - "standard_name": The standard name of the parameter variable.
            - "long_name": The long name of the parameter variable.
            - "chem_variable": The chemical variable of the parameter.
        """
        d = self._normalise_set_kwargs(
            *args, allowed_keys=("variable", "units", "chem_variable", "standard_name", "long_name"), **kwargs
        )

        current = {
            "variable": self._variable,
            "standard_name": self._standard_name,
            "long_name": self._long_name,
            "units": self._units,
            "chem_variable": self._chem_variable,
        }

        current.update(d)
        return self.from_dict(current)
