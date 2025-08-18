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
from earthkit.utils.array import array_to_numpy
from earthkit.utils.array import convert_array

from earthkit.data.core.caching import CACHE


class FieldDataCore(metaclass=ABCMeta):
    KEYS = None

    @property
    def values(self):
        r"""array-like: Get the values stored in the field as a 1D array."""
        return FieldDataCore.flatten(self.get_values())

    @abstractmethod
    def get_values(self, dtype=None):
        r"""array-like: Get the values stored in the field as an array.

        Parameters
        ----------
        dtype: data-type, optional
            The desired data type of the array. If not specified, the default data type is used.
        """
        pass

    def to_numpy(self, shape, flatten=False, dtype=None):
        r"""Return the values stored in the field as an ndarray.

        Parameters
        ----------
        flatten: bool
            When it is True a flat ndarray is returned. Otherwise an ndarray with the field's
            :obj:`shape` is returned.
        dtype: str, numpy.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.

        Returns
        -------
        ndarray
            Field values

        """
        v = array_to_numpy(self.get_values(dtype=dtype))
        shape = self.target_shape(v, flatten, shape)
        return self.reshape(v, shape)

    def to_array(self, shape, flatten=False, dtype=None, array_backend=None):
        r"""Return the values stored in the field.

        Parameters
        ----------
        flatten: bool
            When it is True a flat array is returned. Otherwise an array with the field's
            :obj:`shape` is returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.
        array_backend: str, module or None
            The array backend to be used. When it is :obj:`None` the underlying array format
            of the field is used.

        Returns
        -------
        array-array
            Field values.

        """
        v = self.get_values(dtype=dtype)
        if array_backend is not None:
            v = convert_array(v, target_backend=array_backend)

        shape = self.target_shape(v, flatten, shape)
        return self.reshape(v, shape)

    # TODO: move it to earthkit-utils
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
            return FieldDataCore.reshape(v, n)
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


class FieldData(FieldDataCore):
    @property
    def values(self):
        return self.flatten(self.get_values())

    @abstractmethod
    def get_values(self, dtype=None):
        pass

    def set_values(self, array):
        """Set the values of the field.

        Parameters
        ----------
        array: array-like
            The values to be set in the field.

        Returns
        -------
        FieldData
            A new instance of FieldData with the updated values.
        """
        return ArrayData(array)

    # def _required_shape(self, flatten, shape=None):
    #     """Return the required shape of the array."""
    #     if shape is None:
    #         shape = self.shape
    #     return shape if not flatten else (math.prod(shape),)

    # def _array_matches(self, array, flatten=False, dtype=None):
    #     """Check if the array matches the field and conditions."""
    #     shape = self._required_shape(flatten)
    #     return shape == array.shape and (dtype is None or dtype == array.dtype)


class ArrayCache:
    def __init__(self, array):
        self.xp = array_namespace(array)
        self.cache_file = None

    def __del__(self):

        CACHE._decache_file(self.cache_file)

    def id(self):
        """Return a unique identifier for the data."""
        import datetime
        import hashlib
        from random import randrange

        m = hashlib.sha256()
        m.update(datetime.datetime.now().isoformat().encode("utf-8"))
        m.update(str(randrange(10000000)).encode("utf-8"))
        return m.hexdigest()

    def load(self):
        assert self.cache_file is not None, "Cache file must be set before loading."
        return self.xp.load(self.cache_file)

    def save(self, array):
        def _create(self, path):
            self.xp.save(path, array)

        if self.cache_file is None:
            from earthkit.data.core.caching import cache_file

            self.cache_file = cache_file(
                "array",
                self.create,
                {"id": self.id()},
                extension=".npy",
            )
        else:
            _create(self.cache_file)


class ArrayData(FieldData):
    """A simple data class that uses an array-like structure for values."""

    _cache = None

    def __init__(self, values):
        self._values = values

    def get_values(self, dtype=None):
        """Get the values stored in the field as an array."""
        self.load()
        if dtype is not None:
            return array_namespace(self._values).astype(self._values, dtype)
        return self._values

    def free(self):
        """Free the resources used by the data."""
        # TODO: make it thread safe
        if self._values is not None:
            if self._cache is None:
                self._cache = ArrayCache(self._values)
            self._cache.save(self._values)
            self._values = None

    def load(self):
        # TODO: make it thread safe
        if self._values is None:
            assert self._cache is not None, "Cache must be set before loading."
            self._values = self._cache.load()


# class NumpyData(ArrayData):
#     """A simple data class that uses NumPy for array operations."""

#     def __init__(self, values):
#         self._values = values

#     def get_values(self, dtype=None):
#         """Get the values stored in the field as an array."""
#         if dtype is not None:
#             return self._values.astype(dtype)
#         return self._values
