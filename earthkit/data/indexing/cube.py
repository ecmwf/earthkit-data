# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import functools
import logging
import math
from abc import ABCMeta, abstractmethod

from earthkit.data.core.index import Selection, normalize_selection

LOG = logging.getLogger(__name__)


def coords_to_index(coords, shape) -> int:
    a = 0
    n = 1
    i = len(coords) - 1
    while i >= 0:
        a += coords[i] * n
        n *= shape[i]
        i -= 1
    return a


def index_to_coords(index: int, shape):
    assert isinstance(index, int), (index, type(index))

    result = [None] * len(shape)
    i = len(shape) - 1

    while i >= 0:
        result[i] = index % shape[i]
        index = index // shape[i]
        i -= 1

    result = tuple(result)

    assert len(result) == len(shape)
    return result


class CubeSelection(Selection):
    def match_element(self, element):
        return all(v(element) for k, v in self.actions.items())


class CubeDims(dict):
    def __repr__(self):
        t = "Dimensions:\n"
        max_len = max(len(k) for k in self.keys())
        for k, v in self.items():
            t += f"  {k:<{max_len+4}}{self._format_item(v)}\n"
        return t

    def _format_item(self, item, n=10):
        if len(item) == 0:
            return "??"

        t = f"[{type(item[0]).__name__}] "
        if len(item) == 1:
            t += str(item[0])
        elif len(item) < n:
            t += ", ".join([str(s) for s in item])
        else:
            t += ", ".join([str(s) for s in item[: n - 1]]) + " ,..., " + str(item[-1])

        return t


def flatten(func):
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        _kwargs = {**kwargs}
        _kwargs["flatten"] = len(self.field_shape) == 1
        return func(self, *args, **_kwargs)

    return wrapped


class FieldCubeCore(metaclass=ABCMeta):
    _shape = None
    _field_shape = None
    _dims = None
    _array = None
    flatten_values = None

    @property
    def shape(self):
        return self._shape

    @property
    def dims(self):
        return self._dims

    @property
    @abstractmethod
    def field_shape(self):
        pass

    @abstractmethod
    def to_numpy(self, **kwargs):
        pass

    def __getitem__(self, indexes):
        # Make sure the requested indexes are a list of slices matching the shape

        if isinstance(indexes, int):
            indexes = (indexes,)  # make tuple

        if isinstance(indexes, list):
            indexes = tuple(indexes)

        assert isinstance(indexes, tuple), (type(indexes), indexes)

        indexes = list(indexes)

        if indexes[-1] is Ellipsis:
            indexes.pop()

        while len(indexes) < len(self.shape):
            indexes.append(slice(None, None, None))

        # print(f"{indexes=}")
        indexes = tuple(indexes)

        dims = self._subset_dims(indexes)
        return MaskedCube(self, indexes, dims)

    def sel(self, *args, remapping=None, **kwargs):
        kwargs = normalize_selection(*args, **kwargs)
        # kwargs = self._normalize_kwargs_names(**kwargs)
        # if not kwargs:
        #     return self

        r = {}
        for k, v in kwargs.items():
            selection = CubeSelection(dict(k=v))
            r[k] = list(
                i
                for i, element in enumerate(self.dims[k])
                if selection.match_element(element)
            )

        indexes = []
        for k, v in self.dims.items():
            if k in r:
                indexes.append(r[k])
            else:
                indexes.append(slice(None, None, None))

        indexes = tuple(indexes)
        # print(f"{indexes=}")

        dims = self._subset_dims(indexes)

        return MaskedCube(self, indexes, dims)

    def _subset_dims(self, indexes):
        import numpy as np

        # TODO: avoid copying values
        r = CubeDims()
        for idx, k in zip(indexes, self.dims.keys()):
            # print(f"{k=} {idx=} {self.coords[k]}")
            # print(self.coords[k][idx])
            if isinstance(idx, (int, slice)):
                v = self.dims[k][idx]
                if not isinstance(v, (list, np.ndarray)):
                    v = [v]
                r[k] = v
            elif isinstance(idx, list):
                r[k] = [self.dims[k][i] for i in idx]
        return r

    def copy(self, data=None):
        if data is None:
            data = self.to_numpy().copy()
        return ArrayCube(data, self.dims, self.field_shape)


class FieldListCube(FieldCubeCore):
    def __init__(self, ds, *args, remapping=None, flatten_values=False):
        assert len(ds), f"No data in {ds}"
        self.flatten_values = flatten_values

        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            args = args[0]

        names = []
        for a in args:
            if isinstance(a, str):
                names.append(a)
            elif isinstance(a, dict):
                names += list(a.keys())

        # Sort the source
        self.source = ds.order_by(*args, remapping=remapping)

        # Get a mapping of user names to unique values
        # With possible reduce dimensionality if the user uses 'level+param'
        self._dims = CubeDims(ds.unique_values(*names, remapping=remapping))
        for k, v in self._dims.items():
            self._dims[k] = sorted(v)

        # print(f"{self.user_coords=}")

        self._shape = tuple(len(v) for k, v in self._dims.items())
        self._shape = self._shape + self.field_shape

        if len(self.field_shape) == 1:
            self._dims["values"] = [list(range(self._field_shape[0]))]

        if len(self.field_shape) == 2:
            f = self.source[0]
            geo = f.metadata().geography
            lat = geo.distinct_latitudes()
            lon = geo.distinct_longitudes()
            if len(lat) == self.field_shape[0] and len(lon) == self.field_shape[1]:
                self._dims["latitude"] = lat
                self._dims["longitude"] = lon
            else:
                self._dims["x"] = list(range(self._field_shape[0]))
                self._dims["y"] = list(range(self._field_shape[1]))

    @property
    def field_shape(self):
        if self._field_shape is None:
            self._field_shape = self.source[0].shape

            if self.flatten_values:
                self._field_shape = (math.prod(self._field_shape),)

            assert isinstance(self._field_shape, tuple), (
                self._field_shape,
                self.source[0],
            )
        return self._field_shape

    @flatten
    def to_numpy(self, **kwargs):
        if self._array is None:
            # print(f"shape={self.source.to_numpy(**kwargs).shape}")
            # print(f"kwargs={_kwargs} shape={self.source.to_numpy(**_kwargs).shape}")
            self._array = self.source.to_numpy(**kwargs).reshape(*self.shape)
        return self._array

    @flatten
    def latitudes(self, **kwargs):
        return self.source[0].data("lat", **kwargs)

    @flatten
    def longitudes(self, **kwargs):
        return self.source[0].data("lon", **kwargs)


class ArrayCube(FieldCubeCore):
    def __init__(self, array, dims, field_shape):
        self._array = array
        self._dims = dims
        self._shape = self._array.shape
        self._field_shape = field_shape

    def to_numpy(self, **kwargs):
        return self._array

    @property
    def field_shape(self):
        return self._field_shape


class MaskedCube(FieldCubeCore):
    def __init__(self, cube, indexes, dims):
        self.owner = cube
        self.indexes = indexes
        self._dims = dims
        self._shape = tuple(len(v) for _, v in self._dims.items())
        # print(f"MaskedCube indexes={self.indexes} {self._shape} {self._coords}")

    @flatten
    def to_numpy(self, **kwargs):
        indexes = []
        for idx in self.indexes:
            if idx == slice(None, None, None):
                idx = ":"
            indexes.append(idx)

        indexes = tuple(self.indexes)
        # print(f"to_numpy: {indexes=} {self.shape} {self._shape}")
        # print(f"shape={self.owner.to_numpy(**kwargs).shape}")
        return self.owner.to_numpy(**kwargs)[indexes].reshape(self.shape)

    @flatten
    def latitudes(self, **kwargs):
        return self.owner.latitudes(**kwargs)[tuple(self._field_indexes())]

    @flatten
    def longitudes(self, **kwargs):
        return self.owner.longitudes(**kwargs)[tuple(self._field_indexes())]

    @property
    def field_shape(self):
        if self._field_shape is None:
            if len(self.owner.field_shape) == 1:
                return (self.shape[-1],)
            elif len(self.owner.field_shape) == 2:
                return (self.shape[-2], self.shape[-1])
            else:
                raise ValueError(
                    f"Invalid field shape in owner = {self.owner.field_shape}"
                )
        return self._field_shape

    def _field_indexes(self):
        if len(self.field_shape) == 1:
            return [self.indexes[-1]]
        elif len(self.field_shape) == 2:
            return self.indexes[-2:]
