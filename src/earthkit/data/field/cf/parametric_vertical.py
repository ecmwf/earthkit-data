# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Base class, registry and generic decoder for CF parametric vertical coordinates."""

import logging
from abc import ABCMeta, abstractmethod

from .formula_terms import CF_PARAMETRIC_VERTICAL_TERMS

LOG = logging.getLogger(__name__)

_REGISTRY = {}


class ParametricVerticalCoordinate(metaclass=ABCMeta):
    """Base class for a CF parametric vertical coordinate.

    Subclasses must define the class attributes below and implement :meth:`encode` and
    :meth:`from_xarray`. They are registered with :func:`register_parametric_vertical`.

    Attributes
    ----------
    STANDARD_NAME: str
        CF standard name of the parametric vertical coordinate.
    COMPUTED_STANDARD_NAME: str
        CF standard name of the quantity computed from the formula.
    TERMS: tuple of str
        Names of the formula terms.
    """

    STANDARD_NAME = None
    COMPUTED_STANDARD_NAME = None
    TERMS = ()

    @abstractmethod
    def encode(self, **kwargs):
        """Encode the coordinate into an :obj:`xarray.Dataset` following the CF conventions."""
        pass

    @classmethod
    @abstractmethod
    def from_xarray(cls, ds, coord_name):
        """Create the object from the parametric vertical coordinate ``coord_name`` of ``ds``.

        Parameters
        ----------
        ds: xarray.Dataset
            Dataset containing the coordinate and the variables referred to by its ``formula_terms``.
        coord_name: str
            Name of the parametric vertical coordinate variable in ``ds``.
        """
        pass


def register_parametric_vertical(cls):
    """Class decorator registering a :class:`ParametricVerticalCoordinate` subclass.

    The class is registered under its ``STANDARD_NAME``.

    Raises
    ------
    ValueError
        If ``STANDARD_NAME`` is missing or is already registered by a different class.
    """
    name = getattr(cls, "STANDARD_NAME", None)
    if not name:
        raise ValueError(f"Cannot register {cls.__name__}: STANDARD_NAME is not defined")

    existing = _REGISTRY.get(name)
    if existing is not None and existing is not cls:
        raise ValueError(
            f"Cannot register {cls.__name__}: standard_name={name!r} is already registered by {existing.__name__}"
        )

    _REGISTRY[name] = cls
    return cls


def get_parametric_vertical_class(standard_name):
    """Return the registered class for ``standard_name``.

    Raises
    ------
    ValueError
        If the class is not registered. The message tells whether ``standard_name`` is a
        CF parametric vertical coordinate that is not yet supported or not a CF parametric
        vertical coordinate at all.
    """
    cls = _REGISTRY.get(standard_name)
    if cls is not None:
        return cls

    if standard_name in CF_PARAMETRIC_VERTICAL_TERMS:
        raise ValueError(f"Parametric vertical coordinate {standard_name!r} is not yet supported")

    raise ValueError(f"{standard_name!r} is not a CF parametric vertical coordinate")


def get_cf_attribute(var, name, default=None):
    """Return the CF attribute ``name`` of a variable, looking in ``attrs`` first and then in ``encoding``.

    :func:`xarray.decode_cf` and :func:`xarray.open_dataset` with ``decode_coords="all"`` move
    the ``bounds`` and ``formula_terms`` attributes from ``attrs`` into ``encoding``.

    Parameters
    ----------
    var: xarray.Variable or xarray.DataArray
        The variable.
    name: str
        Name of the attribute.
    default: object, optional
        Value returned when the attribute is in neither place.
    """
    if name in var.attrs:
        return var.attrs[name]
    return var.encoding.get(name, default)


def _find_parametric_vertical_names(ds):
    # variables referred to by the "bounds" attribute of any variable carry their own formula_terms
    # and must not be treated as independent coordinates
    bounds = set()
    for name, var in ds.variables.items():
        b = get_cf_attribute(var, "bounds")
        if isinstance(b, str) and b != name:
            bounds.add(b)

    return [
        name
        for name, var in ds.variables.items()
        if name not in bounds
        and (
            get_cf_attribute(var, "formula_terms") is not None
            or var.attrs.get("standard_name") in CF_PARAMETRIC_VERTICAL_TERMS
        )
    ]


def decode_parametric_vertical(ds, coord_name=None):
    """Decode a parametric vertical coordinate of an :obj:`xarray.Dataset`.

    Parameters
    ----------
    ds: xarray.Dataset
        The dataset.
    coord_name: str, optional
        Name of the parametric vertical coordinate variable. When None, the variable (coordinate or
        data variable) carrying ``formula_terms`` or a parametric vertical ``standard_name`` is
        used. Variables referred to by the ``bounds`` attribute of another variable are ignored.

    Returns
    -------
    ParametricVerticalCoordinate
        Object created by the class registered for the ``standard_name`` of the variable.

    Raises
    ------
    ValueError
        If ``coord_name`` is not in the dataset or has no ``standard_name``, if no parametric vertical
        coordinate is found, if it is ambiguous or if the ``standard_name`` is not supported.
    """
    if coord_name is None:
        names = _find_parametric_vertical_names(ds)
        if not names:
            raise ValueError("No parametric vertical coordinate found in dataset")
        if len(names) > 1:
            raise ValueError(
                f"Parametric vertical coordinate is ambiguous: found {names}, specify coord_name to select one"
            )
        coord_name = names[0]
    elif coord_name not in ds.variables:
        raise ValueError(f"Variable {coord_name!r} not found in dataset")

    standard_name = ds[coord_name].attrs.get("standard_name")
    if not standard_name:
        raise ValueError(f"Variable {coord_name!r} has no standard_name attribute")

    LOG.debug("Decoding parametric vertical coordinate %r with standard_name=%r", coord_name, standard_name)
    return get_parametric_vertical_class(standard_name).from_xarray(ds, coord_name)
