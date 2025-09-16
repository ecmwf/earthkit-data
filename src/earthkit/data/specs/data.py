# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import math
from abc import abstractmethod

from earthkit.utils.array import array_namespace

from earthkit.data.utils.array import flatten

from .spec import SimpleSpec
from .spec import normalise_set_kwargs
from .spec import spec_aliases


@spec_aliases
class Data(SimpleSpec):
    """A specification of a data values."""

    KEYS = ("values",)

    @property
    @abstractmethod
    def values(self):
        r"""array-like: Get the values stored in the field as a 1D array."""
        pass

    @abstractmethod
    def get_values(self, dtype=None, copy=True, index=None):
        r"""array-like: Get the values stored in the field as an array.

        Parameters
        ----------
        dtype: data-type, optional
            The desired data type of the array. If not specified, the default data type is used.
        """
        pass

    # @abstractmethod
    # def to_numpy(self, shape, flatten=False, dtype=None):
    #     r"""Return the values stored in the field as an ndarray.

    #     Parameters
    #     ----------
    #     flatten: bool
    #         When it is True a flat ndarray is returned. Otherwise an ndarray with the field's
    #         :obj:`shape` is returned.
    #     dtype: str, numpy.dtype or None
    #         Typecode or data-type of the array. When it is :obj:`None` the default
    #         type used by the underlying data accessor is used. For GRIB it is ``float64``.

    #     Returns
    #     -------
    #     ndarray
    #         Field values

    #     """
    #     pass

    # @abstractmethod
    # def to_array(self, shape, flatten=False, dtype=None, array_backend=None):
    #     r"""Return the values stored in the field.

    #     Parameters
    #     ----------
    #     flatten: bool
    #         When it is True a flat array is returned. Otherwise an array with the field's
    #         :obj:`shape` is returned.
    #     dtype: str, array.dtype or None
    #         Typecode or data-type of the array. When it is :obj:`None` the default
    #         type used by the underlying data accessor is used. For GRIB it is ``float64``.
    #     array_backend: str, module or None
    #         The array backend to be used. When it is :obj:`None` the underlying array format
    #         of the field is used.

    #     Returns
    #     -------
    #     array-array
    #         Field values.

    #     """
    #     pass


class SimpleData(Data):
    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")
        d = normalise_set_kwargs(cls, add_spec_keys=False, **d)
        if "values" in d:
            return ArrayData(d["values"])
        raise ValueError("Invalid arguments")

    # @classmethod
    # def from_grib(cls, handle):
    #     from .grib.data import GribData

    #     return GribData(handle)

    # @classmethod
    # def from_xarray(cls, owner, selection):
    #     from .xarray.data import XArrayData

    #     return XArrayData(owner, selection)

    @property
    def values(self):
        r"""array-like: Get the values stored in the field as a 1D array."""
        return flatten(self.get_values())

    # def to_numpy(self, shape, flatten=False, dtype=None):
    #     r"""Return the values stored in the field as an ndarray.

    #     Parameters
    #     ----------
    #     flatten: bool
    #         When it is True a flat ndarray is returned. Otherwise an ndarray with the field's
    #         :obj:`shape` is returned.
    #     dtype: str, numpy.dtype or None
    #         Typecode or data-type of the array. When it is :obj:`None` the default
    #         type used by the underlying data accessor is used. For GRIB it is ``float64``.

    #     Returns
    #     -------
    #     ndarray
    #         Field values

    #     """
    #     v = array_to_numpy(self.get_values(dtype=dtype))
    #     shape = self.target_shape(v, flatten, shape)
    #     return self.reshape(v, shape)

    # def to_array(self, shape, flatten=False, dtype=None, array_backend=None):
    #     r"""Return the values stored in the field.

    #     Parameters
    #     ----------
    #     flatten: bool
    #         When it is True a flat array is returned. Otherwise an array with the field's
    #         :obj:`shape` is returned.
    #     dtype: str, array.dtype or None
    #         Typecode or data-type of the array. When it is :obj:`None` the default
    #         type used by the underlying data accessor is used. For GRIB it is ``float64``.
    #     array_backend: str, module or None
    #         The array backend to be used. When it is :obj:`None` the underlying array format
    #         of the field is used.

    #     Returns
    #     -------
    #     array-array
    #         Field values.

    #     """
    #     v = self.get_values(dtype=dtype)
    #     if array_backend is not None:
    #         v = convert_array(v, target_backend=array_backend)

    #     shape = self.target_shape(v, flatten, shape)
    #     return self.reshape(v, shape)

    # # TODO: move it to earthkit-utils
    # @staticmethod
    # def flatten(v):
    #     """Flatten the array without copying the data.

    #     Parameters
    #     ----------
    #     v: array-like
    #         The array to be flattened.

    #     Returns
    #     -------
    #     array-like
    #         1-D array.
    #     """
    #     if len(v.shape) != 1:
    #         n = (math.prod(v.shape),)
    #         return SimpleData.reshape(v, n)
    #     return v

    # # TODO: move it to earthkit-utils
    # @staticmethod
    # def reshape(v, shape):
    #     """Reshape the array to the required shape.

    #     Parameters
    #     ----------
    #     v: array-like
    #         The array to be reshaped.
    #     shape: tuple
    #         The desired shape of the array.

    #     Returns
    #     -------
    #     array-like
    #         Reshaped array.
    #     """
    #     if shape != v.shape:
    #         v = array_namespace(v).reshape(v, shape)
    #     return v

    # @staticmethod
    # def target_shape(array, flatten, field_shape):
    #     """Return the target shape of the array.

    #     Parameters
    #     ----------
    #     array: array-like
    #         The array to be reshaped.
    #     flatten: bool
    #         If True, return a flat shape.

    #     Returns
    #     -------
    #     tuple
    #         The target shape of the array.
    #     """
    #     if flatten:
    #         return (math.prod(array.shape),)
    #     return field_shape

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

    def set(self, **kwargs):
        """Set metadata fields for the field.

        Parameters
        ----------
        **kwargs: dict
            Metadata fields to be set.

        Returns
        -------
        FieldData
            A new instance of FieldData with the updated metadata.
        """
        kwargs = normalise_set_kwargs(self, add_spec_keys=False, **kwargs)
        if "values" in kwargs:
            return self.set_values(kwargs["values"])
        raise ValueError("Invalid arguments")

    def namespace(self, *args):
        return None

    def check(self, owner):
        if self.values.size != math.proc(owner.shape):
            raise ValueError(f"Data shape mismatch: {self.values.shape} (data) != {owner.shape} (field)")

    def get_grib_context(self, context):
        from .grib.data import COLLECTOR

        COLLECTOR.collect_keys(self, context)


class ArrayCache:
    def __init__(self, array):
        self.xp = array_namespace(array)
        self.cache_file = None

    def __del__(self):
        from earthkit.data.core.caching import CACHE

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


class ArrayData(SimpleData):
    """A simple data class that uses an array-like structure for values."""

    _cache = None

    def __init__(self, values):
        if isinstance(values, (list, tuple)):
            import numpy as np

            values = np.asarray(values)
        self._values = values

    def get_values(self, dtype=None, copy=True, index=None):
        """Get the values stored in the field as an array."""
        # self.load()
        v = self._values
        if index is not None:
            v = v[index]
        if copy:
            v = array_namespace(v).asarray(v, copy=True)
        if dtype is not None:
            v = array_namespace(v).astype(v, dtype)
        return v

    def check(self, owner):
        if math.prod(self._values.shape) != math.prod(owner.shape):
            raise ValueError(f"Data shape mismatch: {self._values.shape} (data) != {owner.shape} (field)")

    # def free(self):
    #     """Free the resources used by the data."""
    #     # TODO: make it thread safe
    #     if self._values is not None:
    #         if self._cache is None:
    #             self._cache = ArrayCache(self._values)
    #         self._cache.save(self._values)
    #         self._values = None

    # def load(self):
    #     # TODO: make it thread safe
    #     if self._values is None:
    #         assert self._cache is not None, "Cache must be set before loading."
    #         self._values = self._cache.load()

    # @property
    # def raw_values_shape(self):
    #     return self._values.shape

    def __getstate__(self):
        state = {}
        state["_values"] = self._values
        return state

    def __setstate__(self, state):
        self.__init__(state["_values"])


class OffLoader:
    def __init__(self, field):
        self.field = field

    def unload(self):
        self.field = None

    def load(self):
        if self.field is None:
            raise ValueError("Field is not loaded.")
        return self.field

    def __call__(self, data):
        """Free the resources used by the data."""
        # TODO: make it thread safe
        if self._values is not None:
            if self._cache is None:
                self._cache = ArrayCache(self._values)
            self._cache.save(self._values)
            self._values = None
