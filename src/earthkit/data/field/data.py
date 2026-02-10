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
from typing import Any

from earthkit.utils.array import array_namespace as eku_array_namespace

from earthkit.data.utils.array import flatten

from .core import FieldComponent
from .core import LazyFieldComponentHandler


class BaseDataFieldComponent(FieldComponent):
    """Base class for the data component of a field.

    This class defines the interface for accessing and manipulating the data values
    associated with a field. It provides methods to retrieve the data as an array,
    set new values, and check for consistency with the field's shape.

    It is an abstract class and should be subclassed to provide concrete implementations
    for specific data storage mechanisms.
    """

    ALL_KEYS = ("values",)
    SET_KEYS = ("values",)
    NAME = "data"

    @property
    def spec(self):
        """This field component has no spec."""
        return None

    @property
    @abstractmethod
    def values(self):
        r"""array-like: Get the values stored in the field as a 1D array."""
        pass

    @abstractmethod
    def get_values(self, dtype=None, copy=True):
        r"""array-like: Get the values stored in the field as an array.

        Parameters
        ----------
        dtype: data-type, optional
            The desired data type of the array. If not specified, the default data type is used.
        copy: bool, optional
            If True, a copy of the array is returned. If False, a view is returned if possible. Default is True.
        """
        pass

    def __contains__(self, name):
        """Check if the key is in the specification."""
        return name in self.ALL_KEYS

    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        if key == "values":
            if astype:
                return flatten(self.get_values(dtype=astype, copy=True))
            return self.values

        if raise_on_missing:
            raise KeyError(f"Key {key} not found in specification")

        return default


class DataFieldComponent(BaseDataFieldComponent):
    """Simple data class that provides basic implementation for the data component of a field.

    DataFieldComponent has to be subclassed to provide concrete implementation
    for :py:meth:`get_values`.
    """

    @classmethod
    def from_dict(cls, d, allow_unused=False) -> "DataFieldComponent":
        """Create a DataFieldComponent object from a dictionary."""
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")
        # d = normalise_set_kwargs(cls, add_spec_keys=False, **d)
        if "values" in d:
            v = d["values"]
            return ArrayData(v)
        raise ValueError("Invalid arguments")

    @classmethod
    def from_any(cls, data: Any, **dict_kwargs) -> "DataFieldComponent":
        """Create a DataFieldComponent object from any input.

        Parameters
        ----------
        data: Any
            The input data from which to create the DataFieldComponent instance.
        dict_kwargs: dict, optional
            Additional keyword arguments to be passed when creating the instance from
            a dictionary.

        Returns
        -------
        DataFieldComponent
            An instance of DataFieldComponent. If the input is already an instance
            of DataFieldComponent, it is returned as is. Otherwise, it is assumed to be a
            specification object and a new DataFieldComponent instance is created from it.
        """
        if isinstance(data, (cls, LazyFieldComponentHandler)):
            return data
        elif isinstance(data, dict):
            dict_kwargs = dict_kwargs or {}
            return cls.from_dict(data, **dict_kwargs)

        raise TypeError(f"Cannot create {cls.__name__} from {type(data)}")

    @property
    def values(self):
        r"""array-like: Get the values stored in the field as a 1D array."""
        return flatten(self.get_values(copy=False))

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

    def set(self, values=None, **kwargs):
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
        if values is not None:
            return self.set_values(values)
        raise ValueError("Invalid arguments")

    def dump(self, *args, **kwargs):
        """This field component has no dump."""
        return None

    def check(self, owner):
        """Check that the data is consistent with the field's shape."""
        if self.values.size != math.prod(owner.shape):
            raise ValueError(f"Data shape mismatch: {self.values.shape} (data) != {owner.shape} (field)")

    def get_grib_context(self, context):
        """Get the GRIB context for the data component of the field."""
        from earthkit.data.field.grib.data import COLLECTOR

        COLLECTOR.collect_keys(self, context)


class ArrayCache:
    def __init__(self, array):
        self.xp = eku_array_namespace(array)
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


class ArrayData(DataFieldComponent):
    """Data component of a field that stores values in an array."""

    _cache = None

    def __init__(self, values):
        if isinstance(values, (list, tuple)):
            import numpy as np

            values = np.asarray(values)
        self._values = values

    def get_values(self, dtype=None, copy=True):
        # self.load()
        v = self._values
        xp = eku_array_namespace(v)
        if copy:
            v = xp.asarray(v, copy=True)
        if dtype is not None:
            xp = eku_array_namespace(v)
            try:
                dtype = xp.xp.dtype(dtype)
                return xp.astype(v, dtype, copy=False)
            except Exception:
                pass
        return v

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
