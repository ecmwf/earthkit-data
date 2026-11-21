# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Clash-safe merge of an encoded CF parametric vertical coordinate into an existing xarray Dataset."""

import logging

from .formula_terms import format_formula_terms, parse_formula_terms
from .parametric_vertical import get_cf_attribute

LOG = logging.getLogger(__name__)

# Prefix of the temporary names used by add_parametric_vertical() when encoding.
_TEMP_PREFIX = "__earthkit_cf_"


def _name_candidates(name):
    yield name
    i = 1
    while True:
        yield f"{name}_{i}"
        i += 1


def _align_levels(target, encoded, level_dim):
    """Return the positions in ``encoded[level_dim]`` of the levels of ``target[level_dim]``."""
    import pandas as pd

    t_idx = pd.Index(target.variables[level_dim].values)
    e_idx = pd.Index(encoded.variables[level_dim].values)

    if not t_idx.is_unique or not e_idx.is_unique:
        raise ValueError(f"The values of the level coordinate {level_dim!r} must be unique")

    pos = e_idx.get_indexer(t_idx)
    if len(t_idx) != len(e_idx) or (pos < 0).any():
        raise ValueError(
            f"The level values of the target {t_idx.tolist()} differ from those of the encoded "
            f"coordinate {e_idx.tolist()}"
        )
    return pos


def merge_parametric_vertical(target, encoded, level_dim, *, preferred_names=None, as_coords=True):
    """Merge an encoded CF parametric vertical coordinate into a dataset.

    The variables of ``encoded`` that belong to the coordinate (the formula term variables, the level
    bounds variable, the bounds dimension and any other variable of ``encoded``) are added to a copy
    of ``target``. Name clashes are resolved automatically and the ``formula_terms`` and ``bounds`` attributes
    of the level coordinate and of its bounds variable are rewritten to the final names.

    Parameters
    ----------
    target: xarray.Dataset
        The dataset to merge into. It is not modified. It must have the coordinate ``level_dim``
        with the same set of values as ``encoded[level_dim]`` (in any order).
    encoded: xarray.Dataset
        Dataset holding the encoded coordinate as ``encoded[level_dim]`` (e.g. the output of
        :meth:`AtmosphereHybridSigmaPressureCoordinate.encode`), with the CF ``formula_terms`` attribute
        and optionally ``bounds``. These are read with :func:`get_cf_attribute`. The variables referred to by
        the ``formula_terms`` of the coordinate and of its bounds variable are taken from ``encoded``. A
        referred variable that is not in ``encoded`` (e.g. ``ps`` written by name only) is not added and its
        name is kept as it is. All the dimensions of the added variables other than ``level_dim`` and
        the bounds dimension (i.e. the dimension of the bounds variable that is not ``level_dim``)
        must exist in ``target`` with the same size.
    level_dim: str
        Name of the level dimension and level coordinate, in both datasets.
    preferred_names: dict, optional
        Mapping from a name in ``encoded`` (variable or bounds dimension) to the name wanted in the result.
        Default: the name in ``encoded``. Keys that are not in ``encoded`` are ignored.
    as_coords: bool
        If True the added variables are coordinates, so :attr:`xarray.Dataset.data_vars` of the result is
        the same as that of ``target``. Otherwise they are data variables.

    Returns
    -------
    xarray.Dataset
        A copy of ``target`` with the added variables, in the level order of ``target``. The level
        coordinate keeps its values and its attributes are updated with those of ``encoded[level_dim]``.

    Raises
    ------
    ValueError
        If ``level_dim`` is missing or not 1D in either dataset, the level values differ, ``encoded[level_dim]``
        has no valid ``formula_terms`` or refers to a bounds variable that is not in ``encoded``, or an added
        variable has a dimension that is not in ``target`` with the same size.

    Notes
    -----
    The names are resolved against ``target`` in this order: the bounds dimension, the term variables (the names
    in the ``formula_terms`` of the coordinate and of the bounds variable, including ``ps`` and ``p0``), the level
    bounds variable and the remaining variables of ``encoded``. Variable and dimension names of ``target``
    are both taken. For each name the first of ``name``, ``name_1``, ``name_2``, ... that:

    - is not a variable or dimension name of ``target`` (and was not allocated before) is used for a new variable
    - is a variable of ``target`` identical (:meth:`xarray.Variable.identical`, i.e. dimensions, values with
      NaNs equal and attributes) to the new variable, whose references to other variables (``formula_terms``,
      ``bounds``) and dimensions were already rewritten to their final names, is reused and not added again
    - is, for the bounds dimension, a dimension of ``target`` of the same size that is not ``level_dim``, is
      reused. ``level_dim`` itself is never reused and never given to another variable.
    """
    import xarray as xr

    pref = dict(preferred_names or {})

    for label, ds in (("target", target), ("encoded", encoded)):
        if level_dim not in ds.variables:
            raise ValueError(f"Level coordinate {level_dim!r} not found in {label}")
        if ds.variables[level_dim].dims != (level_dim,):
            raise ValueError(
                f"Level coordinate {level_dim!r} of {label} must be 1D with dimension {level_dim!r}, "
                f"got dims {ds.variables[level_dim].dims}"
            )

    enc_coord = encoded.variables[level_dim]
    coord_ft = get_cf_attribute(enc_coord, "formula_terms")
    if coord_ft is None:
        raise ValueError(f"Variable {level_dim!r} of encoded has no formula_terms attribute")
    coord_terms = parse_formula_terms(coord_ft)

    bounds_name = get_cf_attribute(enc_coord, "bounds")
    bounds_terms = {}
    bdim = None
    if bounds_name is not None:
        if not isinstance(bounds_name, str) or bounds_name not in encoded.variables:
            raise ValueError(f"Bounds variable {bounds_name!r} of {level_dim!r} not found in encoded")
        bvar = encoded.variables[bounds_name]
        bounds_ft = get_cf_attribute(bvar, "formula_terms")
        if bounds_ft is not None:
            bounds_terms = parse_formula_terms(bounds_ft)
        other = [d for d in bvar.dims if d != level_dim]
        if len(other) != 1 or level_dim not in bvar.dims:
            raise ValueError(
                f"Bounds variable {bounds_name!r} must have the dimensions {level_dim!r} and one bounds "
                f"dimension, got {bvar.dims}"
            )
        bdim = other[0]

    # align the encoded variables with the levels of the target, by label
    pos = _align_levels(target, encoded, level_dim)
    enc = encoded.isel({level_dim: pos})

    occupied = set(target.variables) | set(target.dims)
    allocated = set()

    def pick(name, reusable):
        for cand in _name_candidates(pref.get(name, name)):
            if cand == level_dim or cand in allocated:
                continue
            if cand not in occupied:
                return cand, False
            if reusable(cand):
                return cand, True

    # 1. bounds dim
    dim_map = {}
    if bdim is not None:
        size = enc.sizes[bdim]

        def same_dim(cand):
            return cand != level_dim and target.sizes.get(cand) == size

        final_bdim, _ = pick(bdim, same_dim)
        dim_map[bdim] = final_bdim
        allocated.add(final_bdim)

    def map_dims(name, var):
        dims = []
        for d in var.dims:
            if d == level_dim:
                dims.append(d)
            elif d in dim_map:
                dims.append(dim_map[d])
            elif d in target.sizes and target.sizes[d] == var.sizes[d]:
                dims.append(d)
            elif d in target.sizes:
                raise ValueError(
                    f"Dimension {d!r} of variable {name!r} has size {var.sizes[d]} "
                    f"but is size {target.sizes[d]} in target"
                )
            else:
                raise ValueError(f"Dimension {d!r} of variable {name!r} is not in target")
        return tuple(dims)

    def make_variable(var, dims, attrs=None):
        attrs = dict(var.attrs) if attrs is None else attrs
        encoding = dict(var.encoding)
        if "formula_terms" in attrs or "bounds" in attrs:
            encoding.pop("formula_terms", None)
            encoding.pop("bounds", None)
        return xr.Variable(dims, var.data, attrs, encoding)

    final = {}
    added = {}

    def add(name, attrs=None):
        var = enc.variables[name]
        new = make_variable(var, map_dims(name, var), attrs)

        def same_variable(cand):
            return cand in target.variables and target.variables[cand].identical(new)

        fname, reused = pick(name, same_variable)
        final[name] = fname
        if not reused:
            allocated.add(fname)
            added[fname] = new

    # 2. term variables
    for term_name in [*coord_terms.values(), *bounds_terms.values()]:
        if term_name in final or term_name == level_dim or term_name not in encoded.variables:
            continue
        if term_name == bounds_name:
            continue
        add(term_name)

    def rewrite_terms(terms):
        return {t: final.get(v, v) for t, v in terms.items()}

    # 3. level bounds variable
    if bounds_name is not None:
        attrs = dict(enc.variables[bounds_name].attrs)
        if bounds_terms:
            attrs["formula_terms"] = format_formula_terms(rewrite_terms(bounds_terms))
        add(bounds_name, attrs)

    # any other variable of the encoded dataset (e.g. the model level number)
    for name in enc.variables:
        if name != level_dim and name not in final:
            add(name)

    # 4. attributes of the level coordinate
    coord_attrs = dict(enc_coord.attrs)
    coord_attrs["formula_terms"] = format_formula_terms(rewrite_terms(coord_terms))
    if bounds_name is not None:
        coord_attrs["bounds"] = final[bounds_name]

    result = target.copy(deep=False)
    level_var = result.variables[level_dim]
    level_var.attrs.update(coord_attrs)
    level_var.encoding.pop("formula_terms", None)
    level_var.encoding.pop("bounds", None)

    if added:
        result = result.assign_coords(added) if as_coords else result.assign(added)

    return result


def add_parametric_vertical(target, model, level_dim, *, ps_dims=None, coord_values="level_number", bounds=True):
    """Encode a parametric vertical coordinate and merge it into a dataset.

    The coordinate is encoded with temporary names that cannot clash with ``level_dim`` or each other and merged
    with :func:`merge_parametric_vertical`, so that the final names (``ap``, ``b``, ``p0``, ``ps``, ``ap_bnds``,
    ``b_bnds``, ``<level_dim>_bnds``, ``bnds`` and ``model_level_number``) are chosen against ``target``. ``level_dim``
    can have any name, including those of the terms (e.g. ``ap``, ``ps`` or ``bnds``).

    Parameters
    ----------
    target: xarray.Dataset
        The dataset. It is not modified. It must have the coordinate ``level_dim`` with the same level values
        as the encoded coordinate (e.g. model level numbers with ``coord_values="level_number"``).
    model: AtmosphereHybridSigmaPressureCoordinate
        The coordinate, or any other object whose ``encode()`` accepts the same arguments and names.
    level_dim: str
        Name of the level dimension and level coordinate of ``target``.
    ps_dims: dict, optional
        Mapping from dimension name to size of the surface pressure placeholder. When specified, an all-NaN
        ``ps`` variable (the name is ``model.ps_name``) with these dimensions is added unless an identical
        one is in ``target``. The dimensions must be in ``target`` with the same size. When None
        the ``ps`` variable is not added and is referred to by the name ``model.ps_name`` only (no ``ps`` term
        when it is None).
    coord_values: str
        See :meth:`AtmosphereHybridSigmaPressureCoordinate.encode`.
    bounds: bool
        See :meth:`AtmosphereHybridSigmaPressureCoordinate.encode`.

    Returns
    -------
    xarray.Dataset
        See :func:`merge_parametric_vertical`. The added variables are coordinates.

    Raises
    ------
    ValueError
        If the encoding fails (e.g. ``ps_dims`` is specified but ``model.ps_name`` is None, or ``model.ps_name`` is the
        same as ``level_dim`` and ``ps_dims`` is None) or the merge fails.
    """
    ps_name = model.ps_name

    # the temporary names must not be level_dim or a dimension of the placeholder
    reserved = [level_dim, *(ps_dims or ())]
    prefix = _TEMP_PREFIX
    while any(isinstance(n, str) and n.startswith(prefix) for n in reserved):
        prefix = "_" + prefix

    keys = ("ap", "b", "ap_bnds", "b_bnds", "p0", "level_bnds", "bnds", "level_number")
    tmp = {k: f"{prefix}{k}" for k in keys}
    preferred = {
        tmp["ap"]: "ap",
        tmp["b"]: "b",
        tmp["ap_bnds"]: "ap_bnds",
        tmp["b_bnds"]: "b_bnds",
        tmp["p0"]: "p0",
        tmp["level_bnds"]: f"{level_dim}_bnds",
        tmp["bnds"]: "bnds",
        tmp["level_number"]: "model_level_number",
    }

    if ps_dims is not None and ps_name is not None:
        tmp["ps"] = f"{prefix}ps"
        preferred[tmp["ps"]] = ps_name

    encoded = model.encode(
        level_dim=level_dim,
        coord_values=coord_values,
        bounds=bounds,
        names=tmp,
        ps_dims=ps_dims,
    )

    return merge_parametric_vertical(target, encoded, level_dim, preferred_names=preferred, as_coords=True)
