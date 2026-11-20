# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Attach the CF hybrid sigma-pressure parametric vertical coordinate to the datasets built by the engine.

The work is split into two steps because the datasets are built in several stages:

1. :func:`collect_level_dims` is called before the data variables are built (building a
   variable may release its source fields). It reads the level type and the hybrid coefficients from
   the first field of each variable that has a level dimension.
2. :func:`add_hybrid_coordinates` is called on the final dataset (after the dimensions were renamed) and
   adds the coordinate to every level dimension that qualifies.
"""

import logging
from typing import NamedTuple, Optional

import numpy as np

LOG = logging.getLogger(__name__)

_HYBRID = "hybrid"


class _VarInfo(NamedTuple):
    """Information about a data variable on a level dimension, collected before the build."""

    # name of the variable in the final dataset
    name: str
    level_type: Optional[str]
    # (A, B) half level coefficients as arrays, None when not available
    coefficients: Optional[tuple]
    # number of trailing horizontal (field) dimensions of the variable
    num_field_dims: int


def _get_coefficients(vertical):
    try:
        coeffs = vertical.coefficients()
    except Exception:
        LOG.debug("Could not read the vertical coefficients", exc_info=True)
        return None

    if coeffs is None:
        return None

    try:
        if len(coeffs) != 2:
            return None
        return tuple(np.asarray(x, dtype=np.float64) for x in coeffs)
    except (TypeError, ValueError):
        return None


def collect_level_dims(var_builders, tensor_coords, rename_variable):
    """Collect the information needed to encode the hybrid coordinate of each level dimension.

    Parameters
    ----------
    var_builders: dict
        Mapping from the variable name to a :class:`VariableBuilder`.
    tensor_coords: dict
        Mapping from the (not yet renamed) dimension name to a :class:`Coord`.
    rename_variable: callable
        Gives the name in the final dataset for a variable name in ``var_builders``.

    Returns
    -------
    dict
        Mapping from the not yet renamed level dimension name to the list of :class:`_VarInfo` of the
        variables that have the dimension. The coefficients are read from the first field of each variable
        only, and only for variables with hybrid level type.
    """
    from .coord import LevelCoord

    result = {}
    for name, vb in var_builders.items():
        level_dims = [d for d in vb.var_dims if isinstance(tensor_coords.get(d), LevelCoord)]
        if not level_dims:
            continue

        vertical = vb.tensor.source[0].vertical
        level_type = vertical.level_type()
        coeffs = _get_coefficients(vertical) if level_type == _HYBRID else None
        info = _VarInfo(rename_variable(name), level_type, coeffs, len(vb.tensor.field_dims))
        for d in level_dims:
            result.setdefault(d, []).append(info)
    return result


def _final_name(profile, dim):
    """Return the name of ``dim`` in the dataset after the renaming done by ``profile``."""
    import xarray

    ds = profile.rename_dataset_dims(xarray.Dataset(coords={dim: [0]}))
    return next(iter(ds.dims))


def _hybrid_model(dim, infos, levels):
    """Return the model for the level dimension or None when it does not qualify."""
    from earthkit.data.field.cf import AtmosphereHybridSigmaPressureCoordinate

    if any(x.level_type != _HYBRID for x in infos):
        LOG.debug("Level dimension %s is not only used by hybrid levels, no CF hybrid coordinate added", dim)
        return None

    if any(x.coefficients is None for x in infos):
        LOG.debug("Hybrid levels of dimension %s have no coefficients, no CF hybrid coordinate added", dim)
        return None

    A, B = infos[0].coefficients
    for x in infos[1:]:
        if not (np.array_equal(A, x.coefficients[0]) and np.array_equal(B, x.coefficients[1])):
            LOG.warning(
                "The hybrid level coefficients of the variables on dimension %s differ, no CF hybrid coordinate added",
                dim,
            )
            return None

    try:
        return AtmosphereHybridSigmaPressureCoordinate.from_half_levels(A, B, levels=levels)
    except ValueError as e:
        LOG.warning("Cannot create the CF hybrid coordinate for dimension %s: %s", dim, e)
        return None


def add_hybrid_coordinates(dataset, level_dims, profile):
    """Add the CF hybrid sigma-pressure coordinate to the qualifying level dimensions of a dataset.

    The coordinate (``ap``, ``b``, ``p0``, bounds, the all-NaN ``ps`` placeholder on the horizontal
    grid and ``formula_terms``) is added as coordinates, so the data variables are unchanged. The level
    values remain the model level numbers.

    Parameters
    ----------
    dataset: xarray.Dataset
        The final dataset, i.e. after the dimensions were renamed.
    level_dims: dict
        The output of :func:`collect_level_dims`.
    profile: Profile
        The profile used to build the dataset.

    Returns
    -------
    xarray.Dataset
        ``dataset`` if nothing was added, otherwise a new dataset.
    """
    from earthkit.data.field.cf import add_parametric_vertical

    for dim, infos in level_dims.items():
        if not infos or infos[0].level_type != _HYBRID:
            continue

        name = _final_name(profile, dim)
        if name not in dataset.dims or dataset.variables[name].dims != (name,):
            continue

        model = _hybrid_model(name, infos, dataset.variables[name].values)
        if model is None:
            continue

        # the horizontal dims are the last dims of a variable
        first = infos[0]
        if first.name not in dataset.variables:
            continue
        dims = dataset.variables[first.name].dims
        ps_dims = {d: dataset.sizes[d] for d in dims[len(dims) - first.num_field_dims :]}

        dataset = add_parametric_vertical(dataset, model, name, ps_dims=ps_dims, coord_values="level_number")

    return dataset
