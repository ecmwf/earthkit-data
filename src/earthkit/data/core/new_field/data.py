# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import math
from abc import ABCMeta
from abc import abstractmethod

from earthkit.utils.array import array_namespace


class Data(metaclass=ABCMeta):
    @property
    @abstractmethod
    def values(self):
        r"""array-like: Get the values stored in the field as a 1D array."""
        pass

    @abstractmethod
    def get_values(self, dtype=None):
        r"""array-like: Get the values stored in the field as an array.

        Parameters
        ----------
        dtype: data-type, optional
            The desired data type of the array. If not specified, the default data type is used.
        """
        pass

    # TODO: move it to eerthkit-utils
    @staticmethod
    def flatten(v):
        """Flatten the array without copying the data.

        Parameters
        ----------
        v: array-like
            The array to be flattened.

        Returns
        -------
        array-like
            1-D array.
        """
        if len(v.shape) != 1:
            n = (math.prod(v.shape),)
            return Data.reshape(v, n)
        return v

    # TODO: move it to earthkit-utils
    @staticmethod
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

    @staticmethod
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


class SimpleData(Data):
    @property
    def values(self):
        return Data.flatten(self.get_values())

    @abstractmethod
    def get_values(self, dtype=None):
        pass

    def _required_shape(self, flatten, shape=None):
        """Return the required shape of the array."""
        if shape is None:
            shape = self.shape
        return shape if not flatten else (math.prod(shape),)

    def _array_matches(self, array, flatten=False, dtype=None):
        """Check if the array matches the field and conditions."""
        shape = self._required_shape(flatten)
        return shape == array.shape and (dtype is None or dtype == array.dtype)
