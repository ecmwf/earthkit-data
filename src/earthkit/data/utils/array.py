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


def flatten(array):
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
        return reshape(array, n)
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


def reshape(v, shape):
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
