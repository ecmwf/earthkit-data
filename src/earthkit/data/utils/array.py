# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import math

from earthkit.utils.array import array_namespace


def flatten_array(array):
    """Flatten the array without copying the data.

    Parameters
    ----------
    array: array-like
        The array to be flattened.

    Returns
    -------
    array-like
        1-D array.
    """
    if len(array.shape) != 1:
        n = (math.prod(array.shape),)
        return reshape_array(array, n)
    return array


def target_shape(array, flatten, field_shape):
    """Return the target shape of the array.

    Parameters
    ----------
    array: array-like
        The array to be reshaped.
    flatten: bool
        If True, return a flat shape.

    Returns
    -------
    tuple
        The target shape of the array.
    """
    if flatten:
        return (math.prod(array.shape),)
    return field_shape


def reshape_array(v, shape):
    """Reshape the array to the required shape.

    Parameters
    ----------
    v: array-like
        The array to be reshaped.
    shape: tuple
        The desired shape of the array.

    Returns
    -------
    array-like
        Reshaped array.
    """
    if shape != v.shape:
        v = array_namespace(v).reshape(v, shape)
    return v


def adjust_array(v, flatten=False, dtype=None):
    if flatten:
        v = flatten_array(v)

    if dtype is not None:
        from earthkit.utils.array.convert import convert_dtype

        target_xp = array_namespace(v)
        target_dtype = convert_dtype(dtype, target_xp)
        if target_dtype is not None:
            v = target_xp.astype(v, target_dtype, copy=False)

    return v


def outer_indexing(v, indices):
    """Performs an outer indexing of an array ``v``.
    The parameter ``indices`` is a tuple of indices.
    Each index is either an int, a slice of an array of int's.
    Each index form ``indices`` restricts/sub-selects the corresponding dimension of the array ``v``,
    independently (orthogonally) to other indices (hence the name: "outer indexing").

    This function mimics the behaviour of ``xarray.DataArray(v)[indices].values``,
    and in general it is different from the behaviour of e.g.
    the numpy indexing, i.e. ``v[indices]``
    (see https://numpy.org/doc/stable/user/basics.indexing.html#advanced-indexing).

    Parameters
    ----------
    v: array-like
        The array to be reshaped.
    indices: tuple of items, each being an int, a slice or an array-like of int's

    Returns
    -------
    array-like
        Sub-selection of the array ``v`` according to ``indices``
    """
    if not isinstance(indices, tuple):
        indices = (indices,)
    full_slices = ()
    ndim = v.ndim
    for idx in indices:
        _1d_index = full_slices + (idx,)
        v = v[_1d_index]
        v_ndim = v.ndim
        if v_ndim == ndim:
            full_slices = full_slices + (slice(None),)
        else:
            # the current dimension has collapsed
            ndim = v_ndim
    return v
