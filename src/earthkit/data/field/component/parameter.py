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
    types (e.g. :meth:`chem`), and may return None.

    The parameter information can be accessed by methods like :meth:`variable`,
    :meth:`units`, and :meth:`chem`. Each of these methods has an associated key
    that can be used in the :meth:`get` method to retrieve the corresponding information. The list
    of supported keys are as follows:

    - "variable": string representing the parameter variable
    - "standard_name": string representing the standard name of the parameter variable, based
       on the CF standard name
    - "long_name": string representing the long name of the parameter variable
    - "units": as a string or a :class:`Units` object representing the parameter units
    - "chem": string representing the parameter chemical constituent or aerosol type, or None
    - "chem_long_name": string representing the long name of the parameter chemical constituent or aerosol type, or None
    - "wavelength": int representing the optical parameter wavelength in nanometers,
       or a 2-tuple of ints representing the wavelength range in nanometers, or None
    - "wavelength_bounds": 2-tuple of ints representing the optical parameter wavelength bounds
       in nanometers, or None
    - "wave_direction": float representing the wave direction in degrees of the 2D spectra parameter, or None
    - "wave_direction_index": int representing the 0-based index of the wave direction bin, or None
    - "wave_direction_bounds": 2-tuple of floats representing the wave direction bounds in degrees, or None
    - "wave_frequency": float representing the wave frequency in Hz of the 2D spectra parameter, or None
    - "wave_frequency_index": int representing the 0-based index of the wave frequency bin, or None
    - "wave_frequency_bounds": 2-tuple of floats representing the wave frequency bounds in Hz, or None
    - "param": alias of "variable"

    Depending on the type of parameter information available, some of these keys may not be supported
    and will return None in the subclasses. For example, the "chem" key is only supported
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

        The parameter units are :class:`Units` objects. The units are based on Pint (when possible)
        and are normalised to a standard form. They can be used for unit conversions and comparisons.
        """
        pass

    @mark_get_key
    @abstractmethod
    def chem(self) -> Optional[str]:
        r"""Return the parameter chemical constituent or aerosol type."""
        pass

    @mark_get_key
    @abstractmethod
    def chem_long_name(self) -> Optional[str]:
        r"""Return the long name of the parameter chemical constituent or aerosol type."""
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

    @mark_get_key
    @abstractmethod
    def wavelength(self) -> Optional[Union[int, tuple[int, int]]]:
        """Return the optical parameter wavelength or wavelength interval in nanometers."""
        pass

    @mark_get_key
    @abstractmethod
    def wavelength_bounds(self) -> Optional[tuple[int, int]]:
        """Return the optical parameter wavelength bounds in nanometers."""
        pass

    @mark_get_key
    @abstractmethod
    def wave_direction(self) -> Optional[float]:
        """Return the wave direction in degrees of the 2D spectra parameter."""
        pass

    @mark_get_key
    @abstractmethod
    def wave_direction_index(self) -> Optional[int]:
        """Return the 0-based index of the wave direction bin."""
        pass

    @mark_get_key
    @abstractmethod
    def wave_direction_bounds(self) -> Optional[tuple[float, float]]:
        """Return the wave direction bounds in degrees of the 2D spectra parameter."""
        pass

    @mark_get_key
    @abstractmethod
    def wave_frequency(self) -> Optional[float]:
        """Return the wave frequency in Hz of the 2D spectra parameter."""
        pass

    @mark_get_key
    @abstractmethod
    def wave_frequency_index(self) -> Optional[int]:
        """Return the 0-based index of the wave frequency bin."""
        pass

    @mark_get_key
    @abstractmethod
    def wave_frequency_bounds(self) -> Optional[tuple[float, float]]:
        """Return the wave frequency bounds in Hz of the 2D spectra parameter."""
        pass

    @classmethod
    def from_dict(cls, d: dict) -> "ParameterBase":
        """Create a parameter object from a dictionary.

        The appropriate subclass is determined automatically based on the dictionary contents.

        Parameters
        ----------
        d : dict
            Dictionary containing parameter data.

            The dictionary can contain the following keys:

            - "variable": The parameter variable.
            - "standard_name": The standard name of the parameter variable.
            - "long_name": The long name of the parameter variable.
            - "units": The parameter units, as a string or a Units object.
            - "chem": The chemical constituent or aerosol type of the parameter.
            - "chem_long_name": The long name of the chemical constituent or aerosol type of the parameter.
            - "wavelength": The optical parameter wavelength in nanometers, or a wavelength range in nanometers,
               as an int or a 2-tuple of ints.
            - "wavelength_bounds": The optical parameter wavelength bounds in nanometers, as a 2-tuple of ints.
            - "wave_direction": The wave direction in degrees of the 2D spectra parameter.
            - "wave_direction_index": The 0-based index of the wave direction bin.
            - "wave_direction_bounds": The wave direction bounds in degrees, as a 2-tuple of floats.
            - "wave_frequency": The wave frequency in Hz of the 2D spectra parameter.
            - "wave_frequency_index": The 0-based index of the wave frequency bin.
            - "wave_frequency_bounds": The wave frequency bounds in Hz, as a 2-tuple of floats.

        Returns
        -------
        ParameterBase
            The created parameter instance. The actual type depends on the dictionary contents:
            :class:`ChemicalOpticalParameter`, :class:`ChemicalParameter`,
            :class:`OpticalParameter`, :class:`WaveSpectraParameter`, or :class:`Parameter`.
        """
        return create_parameter(d)


def create_parameter(d: dict) -> ParameterBase:
    """Create a ParameterBase object from a dictionary.

    The appropriate subclass is determined automatically based on the dictionary contents:

    - If both ``chem`` and ``wavelength`` are present, a :class:`ChemicalOpticalParameter` is created.
    - If only ``chem`` is present, a :class:`ChemicalParameter` is created.
    - If only ``wavelength`` is present, an :class:`OpticalParameter` is created.
    - If ``wave_direction`` or ``wave_frequency`` is present, a :class:`WaveSpectraParameter` is created.
    - Otherwise, a :class:`Parameter` is created.

    Parameters
    ----------
    d : dict
        Dictionary containing parameter data.

    Returns
    -------
    ParameterBase
        The created parameter instance. The actual type depends on the dictionary contents.
    """
    if not isinstance(d, dict):
        raise TypeError(f"Cannot create Parameter from {type(d)}, expected dict")

    d1 = Parameter._normalise_create_kwargs(
        d,
        allowed_keys=(
            "variable",
            "units",
            "chem",
            "chem_long_name",
            "standard_name",
            "long_name",
            "wavelength",
            "wavelength_bounds",
            "wave_direction",
            "wave_direction_index",
            "wave_direction_bounds",
            "wave_frequency",
            "wave_frequency_index",
            "wave_frequency_bounds",
        ),
    )
    if "variable" not in d1:
        raise ValueError("Cannot create Parameter without variable")

    has_chem = d1.get("chem") is not None
    has_wavelength = d1.get("wavelength") is not None
    has_wave_spectra = d1.get("wave_direction") is not None or d1.get("wave_frequency") is not None

    if has_chem and has_wavelength:
        cls = ChemicalOpticalParameter
    elif has_chem:
        cls = ChemicalParameter
    elif has_wavelength:
        cls = OpticalParameter
    elif has_wave_spectra:
        cls = WaveSpectraParameter
    else:
        cls = Parameter

    return cls._create_component(d1)


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

    def chem(self) -> None:
        r"""Return the parameter chemical constituent or aerosol type.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    def chem_long_name(self) -> None:
        r"""Return the long name of the parameter chemical constituent or aerosol type.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    def wavelength(self) -> None:
        r"""Return the optical parameter wavelength or wavelength interval in nanometers.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    def wavelength_bounds(self) -> None:
        r"""Return the optical parameter wavelength bounds in nanometers.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    def wave_direction(self) -> None:
        r"""Return the wave direction in degrees of the 2D spectra parameter.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    def wave_direction_index(self) -> None:
        r"""Return the 0-based index of the wave direction bin.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    def wave_direction_bounds(self) -> None:
        r"""Return the wave direction bounds in degrees of the 2D spectra parameter.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    def wave_frequency(self) -> None:
        r"""Return the wave frequency in Hz of the 2D spectra parameter.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    def wave_frequency_index(self) -> None:
        r"""Return the 0-based index of the wave frequency bin.

        An EmptyParameter does not contain any parameter information, and this method returns None.
        """
        return None

    def wave_frequency_bounds(self) -> None:
        r"""Return the wave frequency bounds in Hz of the 2D spectra parameter.

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
    """Parameter component representing a regular parameter.

    A regular parameter is one that does not have any chemical, optical, or wave spectra
    properties. For parameters with chemical constituents, use :class:`ChemicalParameter`.
    For parameters with optical wavelength information, use :class:`OpticalParameter`.
    For parameters with both chemical and optical properties, use :class:`ChemicalOpticalParameter`.
    For parameters with wave spectra properties, use :class:`WaveSpectraParameter`.

    Parameters
    ----------
    variable : str, optional
        The parameter variable, by default None.
    standard_name : str, optional
        The standard name of the parameter variable, by default None.
    long_name : str, optional
        The long name of the parameter variable, by default None.
    units : str or Units, optional
        The parameter units, by default None. Can be provided as a string or a Units object.
    """

    def __init__(
        self,
        variable: str = None,
        standard_name: str = None,
        long_name: str = None,
        units: Union[str, "Units"] = None,
    ) -> None:
        self._variable = variable
        self._standard_name = standard_name
        self._long_name = long_name
        self._units = Units.from_any(units)

    def variable(self) -> Optional[str]:
        return self._variable

    def standard_name(self) -> Optional[str]:
        return self._standard_name

    def long_name(self) -> Optional[str]:
        return self._long_name

    def units(self) -> Optional["Units"]:
        return self._units

    def chem(self) -> None:
        r"""Return the parameter chemical constituent or aerosol type.

        A regular Parameter does not have chemical information, and this method returns None.
        """
        return None

    def chem_long_name(self) -> None:
        r"""Return the long name of the parameter chemical constituent or aerosol type.

        A regular Parameter does not have chemical information, and this method returns None.
        """
        return None

    def wavelength(self) -> None:
        r"""Return the optical parameter wavelength or wavelength interval in nanometers.

        A regular Parameter does not have optical information, and this method returns None.
        """
        return None

    def wavelength_bounds(self) -> None:
        r"""Return the optical parameter wavelength bounds in nanometers.

        A regular Parameter does not have optical information, and this method returns None.
        """
        return None

    def wave_direction(self) -> None:
        r"""Return the wave direction in degrees of the 2D spectra parameter.

        A regular Parameter does not have wave spectra information, and this method returns None.
        """
        return None

    def wave_direction_index(self) -> None:
        r"""Return the 0-based index of the wave direction bin.

        A regular Parameter does not have wave spectra information, and this method returns None.
        """
        return None

    def wave_direction_bounds(self) -> None:
        r"""Return the wave direction bounds in degrees of the 2D spectra parameter.

        A regular Parameter does not have wave spectra information, and this method returns None.
        """
        return None

    def wave_frequency(self) -> None:
        r"""Return the wave frequency in Hz of the 2D spectra parameter.

        A regular Parameter does not have wave spectra information, and this method returns None.
        """
        return None

    def wave_frequency_index(self) -> None:
        r"""Return the 0-based index of the wave frequency bin.

        A regular Parameter does not have wave spectra information, and this method returns None.
        """
        return None

    def wave_frequency_bounds(self) -> None:
        r"""Return the wave frequency bounds in Hz of the 2D spectra parameter.

        A regular Parameter does not have wave spectra information, and this method returns None.
        """
        return None

    def to_dict(self):
        """Return a dictionary representation of the parameter."""
        return {
            "variable": self._variable,
            "standard_name": self._standard_name,
            "long_name": self._long_name,
            "units": str(self._units),
        }

    def __getstate__(self):
        return self.to_dict()

    def __setstate__(self, state):
        self.__init__(**state)

    def set(self, *args, **kwargs):
        """Create a new instance with updated data.

        The returned instance type is determined by the resulting dictionary contents,
        which may differ from the current instance type.

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
            - "chem": The chemical constituent or aerosol type of the parameter.
            - "chem_long_name": The long name of the chemical constituent or aerosol type of the parameter.
            - "wavelength": The optical parameter wavelength in nanometers, or a wavelength range in nanometers.
            - "wavelength_bounds": The optical parameter wavelength bounds in nanometers, as a 2-tuple of ints.
            - "wave_direction": The wave direction in degrees of the 2D spectra parameter.
            - "wave_direction_index": The 0-based index of the wave direction bin.
            - "wave_direction_bounds": The wave direction bounds in degrees, as a 2-tuple of floats.
            - "wave_frequency": The wave frequency in Hz of the 2D spectra parameter.
            - "wave_frequency_index": The 0-based index of the wave frequency bin.
            - "wave_frequency_bounds": The wave frequency bounds in Hz, as a 2-tuple of floats.
        """
        d = self._normalise_set_kwargs(
            *args,
            allowed_keys=(
                "variable",
                "units",
                "chem",
                "chem_long_name",
                "standard_name",
                "long_name",
                "wavelength",
                "wavelength_bounds",
                "wave_direction",
                "wave_direction_index",
                "wave_direction_bounds",
                "wave_frequency",
                "wave_frequency_index",
                "wave_frequency_bounds",
            ),
            **kwargs,
        )

        current = self.to_dict()
        current.update(d)
        return create_parameter(current)


class ChemicalParameter(Parameter):
    """Parameter component representing a chemical parameter.

    A chemical parameter includes a chemical constituent or aerosol type identifier.
    For parameters that also have optical wavelength information, use
    :class:`ChemicalOpticalParameter`.

    Parameters
    ----------
    variable : str, optional
        The parameter variable, by default None.
    standard_name : str, optional
        The standard name of the parameter variable, by default None.
    long_name : str, optional
        The long name of the parameter variable, by default None.
    units : str or Units, optional
        The parameter units, by default None. Can be provided as a string or a Units object.
    chem : str, optional
        The parameter chemical constituent or aerosol type, by default None.
    chem_long_name : str, optional
        The long name of the parameter chemical constituent or aerosol type, by default None.
    """

    def __init__(
        self,
        variable: str = None,
        standard_name: str = None,
        long_name: str = None,
        units: Union[str, "Units"] = None,
        chem: str = None,
        chem_long_name: str = None,
    ) -> None:
        Parameter.__init__(self, variable=variable, standard_name=standard_name, long_name=long_name, units=units)
        self._chem = chem
        self._chem_long_name = chem_long_name

    def chem(self) -> Optional[str]:
        r"""Return the parameter chemical constituent or aerosol type."""
        return self._chem

    def chem_long_name(self) -> Optional[str]:
        r"""Return the long name of the parameter chemical constituent or aerosol type."""
        return self._chem_long_name

    def to_dict(self):
        """Return a dictionary representation of the chemical parameter."""
        d = Parameter.to_dict(self)
        d["chem"] = self._chem
        d["chem_long_name"] = self._chem_long_name
        return d


class OpticalParameter(Parameter):
    """Parameter component representing an optical parameter.

    An optical parameter includes a wavelength or wavelength range but no chemical
    constituent. For parameters that have both chemical and optical properties, use
    :class:`ChemicalOpticalParameter`.

    Parameters
    ----------
    variable : str, optional
        The parameter variable, by default None.
    standard_name : str, optional
        The standard name of the parameter variable, by default None.
    long_name : str, optional
        The long name of the parameter variable, by default None.
    units : str or Units, optional
        The parameter units, by default None. Can be provided as a string or a Units object.
    wavelength : int or 2-tuple of ints, optional
        The optical parameter wavelength in nanometers, or a wavelength range in nanometers, by default None.
    wavelength_bounds : 2-tuple of ints, optional
        The optical parameter wavelength bounds in nanometers, by default None.
    """

    def __init__(
        self,
        variable: str = None,
        standard_name: str = None,
        long_name: str = None,
        units: Union[str, "Units"] = None,
        wavelength: Union[int, tuple[int, int]] = None,
        wavelength_bounds: Optional[tuple[int, int]] = None,
    ) -> None:
        Parameter.__init__(self, variable=variable, standard_name=standard_name, long_name=long_name, units=units)
        self._wavelength = wavelength
        self._wavelength_bounds = wavelength_bounds

    def wavelength(self) -> Optional[Union[int, tuple[int, int]]]:
        r"""Return the optical parameter wavelength or wavelength interval in nanometers."""
        return self._wavelength

    def wavelength_bounds(self) -> Optional[tuple[int, int]]:
        r"""Return the optical parameter wavelength bounds in nanometers."""
        return self._wavelength_bounds

    def to_dict(self):
        """Return a dictionary representation of the optical parameter."""
        d = Parameter.to_dict(self)
        d["wavelength"] = self._wavelength
        d["wavelength_bounds"] = self._wavelength_bounds
        return d


class ChemicalOpticalParameter(ChemicalParameter, OpticalParameter):
    """Parameter component representing a chemical-optical parameter.

    A chemical-optical parameter includes both a chemical constituent or aerosol type
    and an optical wavelength or wavelength range. It inherits chemical properties from
    :class:`ChemicalParameter` and optical properties from :class:`OpticalParameter`.

    Parameters
    ----------
    variable : str, optional
        The parameter variable, by default None.
    standard_name : str, optional
        The standard name of the parameter variable, by default None.
    long_name : str, optional
        The long name of the parameter variable, by default None.
    units : str or Units, optional
        The parameter units, by default None. Can be provided as a string or a Units object.
    chem : str, optional
        The parameter chemical constituent or aerosol type, by default None.
    chem_long_name : str, optional
        The long name of the parameter chemical constituent or aerosol type, by default None.
    wavelength : int or 2-tuple of ints, optional
        The optical parameter wavelength in nanometers, or a wavelength range in nanometers, by default None.
    wavelength_bounds : 2-tuple of ints, optional
        The optical parameter wavelength bounds in nanometers, by default None.
    """

    def __init__(
        self,
        variable: str = None,
        standard_name: str = None,
        long_name: str = None,
        units: Union[str, "Units"] = None,
        chem: str = None,
        chem_long_name: str = None,
        wavelength: Union[int, tuple[int, int]] = None,
        wavelength_bounds: Optional[tuple[int, int]] = None,
    ) -> None:
        Parameter.__init__(self, variable=variable, standard_name=standard_name, long_name=long_name, units=units)
        self._chem = chem
        self._chem_long_name = chem_long_name
        self._wavelength = wavelength
        self._wavelength_bounds = wavelength_bounds

    def to_dict(self):
        """Return a dictionary representation of the chemical-optical parameter."""
        d = Parameter.to_dict(self)
        d["chem"] = self._chem
        d["chem_long_name"] = self._chem_long_name
        d["wavelength"] = self._wavelength
        d["wavelength_bounds"] = self._wavelength_bounds
        return d


class WaveSpectraParameter(Parameter):
    """Parameter component representing a wave spectra parameter.

    A wave spectra parameter includes wave direction and/or wave frequency information
    from 2D wave spectra fields.

    Parameters
    ----------
    variable : str, optional
        The parameter variable, by default None.
    standard_name : str, optional
        The standard name of the parameter variable, by default None.
    long_name : str, optional
        The long name of the parameter variable, by default None.
    units : str or Units, optional
        The parameter units, by default None. Can be provided as a string or a Units object.
    wave_direction : float, optional
        The wave direction in degrees of the 2D spectra parameter, by default None.
    wave_direction_index : int, optional
        The 0-based index of the wave direction bin, by default None.
    wave_direction_bounds : 2-tuple of floats, optional
        The wave direction bounds in degrees of the 2D spectra parameter, by default None.
    wave_frequency : float, optional
        The wave frequency in Hz of the 2D spectra parameter, by default None.
    wave_frequency_index : int, optional
        The 0-based index of the wave frequency bin, by default None.
    wave_frequency_bounds : 2-tuple of floats, optional
        The wave frequency bounds in Hz of the 2D spectra parameter, by default None.
    """

    def __init__(
        self,
        variable: str = None,
        standard_name: str = None,
        long_name: str = None,
        units: Union[str, "Units"] = None,
        wave_direction: float = None,
        wave_direction_index: Optional[int] = None,
        wave_direction_bounds: Optional[tuple[float, float]] = None,
        wave_frequency: float = None,
        wave_frequency_index: Optional[int] = None,
        wave_frequency_bounds: Optional[tuple[float, float]] = None,
    ) -> None:
        Parameter.__init__(self, variable=variable, standard_name=standard_name, long_name=long_name, units=units)
        self._wave_direction = wave_direction
        self._wave_direction_index = wave_direction_index
        self._wave_direction_bounds = wave_direction_bounds
        self._wave_frequency = wave_frequency
        self._wave_frequency_index = wave_frequency_index
        self._wave_frequency_bounds = wave_frequency_bounds

    def wave_direction(self) -> Optional[float]:
        r"""Return the wave direction in degrees of the 2D spectra parameter."""
        return self._wave_direction

    def wave_direction_index(self) -> Optional[int]:
        r"""Return the 0-based index of the wave direction bin."""
        return self._wave_direction_index

    def wave_direction_bounds(self) -> Optional[tuple[float, float]]:
        r"""Return the wave direction bounds in degrees of the 2D spectra parameter."""
        return self._wave_direction_bounds

    def wave_frequency(self) -> Optional[float]:
        r"""Return the wave frequency in Hz of the 2D spectra parameter."""
        return self._wave_frequency

    def wave_frequency_index(self) -> Optional[int]:
        r"""Return the 0-based index of the wave frequency bin."""
        return self._wave_frequency_index

    def wave_frequency_bounds(self) -> Optional[tuple[float, float]]:
        r"""Return the wave frequency bounds in Hz of the 2D spectra parameter."""
        return self._wave_frequency_bounds

    def to_dict(self):
        """Return a dictionary representation of the wave spectra parameter."""
        d = Parameter.to_dict(self)
        d["wave_direction"] = self._wave_direction
        d["wave_direction_index"] = self._wave_direction_index
        d["wave_direction_bounds"] = self._wave_direction_bounds
        d["wave_frequency"] = self._wave_frequency
        d["wave_frequency_index"] = self._wave_frequency_index
        d["wave_frequency_bounds"] = self._wave_frequency_bounds
        return d
