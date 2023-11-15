# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import functools
import itertools
import logging
import math
from abc import ABCMeta, abstractmethod

import numpy as np

from earthkit.data.core.index import Selection, normalize_selection

LOG = logging.getLogger(__name__)


def coords_to_index(coords, shape) -> int:
    """
    Map user coords to field index"""
    index = 0
    n = 1
    # i = len(coords) - 1
    for i in range(len(coords) - 1, 0, -1):
        # while i >= 0:
        index += coords[i] * n
        n *= shape[i]
        # i -= 1
    return index


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


class CubeCoords(dict):
    def __repr__(self):
        t = "Coordinates:\n"
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


def flatten_arg(func):
    @functools.wraps(func)
    def wrapped(self, *args, **kwargs):
        _kwargs = {**kwargs}
        _kwargs["flatten"] = len(self.field_shape) == 1
        return func(self, *args, **_kwargs)

    return wrapped


class TensorCore(metaclass=ABCMeta):
    _type = None
    _shape = None
    _user_shape = None
    _field_shape = None
    _coords = None
    _array = None
    _data = None
    flatten_values = None

    @property
    def shape(self):
        return self._shape

    @property
    def user_shape(self):
        return self._user_shape

    @property
    def field_shape(self):
        return self._field_shape

    @property
    def coords(self):
        return self._coords

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

        return self._subset(indexes)

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
                for i, element in enumerate(self.coords[k])
                if selection.match_element(element)
            )
            if len(r[k]) == 1:
                v = r[k][0]
                r[k] = slice(v, v + 1)
                # r[k] = r[k][0]

        indexes = []
        for k, v in self.coords.items():
            if k in r:
                indexes.append(r[k])
            else:
                indexes.append(slice(None, None, None))

        indexes = tuple(indexes)
        # print(f"{indexes=}")

        return self._subset(indexes)

    def isel(self, *args, remapping=None, **kwargs):
        kwargs = normalize_selection(*args, **kwargs)

        indexes = []
        for k, v in self.coords.items():
            if k in kwargs:
                indexes.append(kwargs[k])
            else:
                indexes.append(slice(None, None, None))

        indexes = tuple(indexes)
        # print(f"{indexes=}")

        return self._subset(indexes)

    @abstractmethod
    def _subset(self, indexes):
        pass

    def _subset_coords(self, indexes):
        import numpy as np

        # TODO: avoid copying values
        r = CubeCoords()
        for idx, k in zip(indexes, self.coords.keys()):
            # print(f"{k=} {idx=} {self.coords[k]}")
            # print(self.coords[k][idx])
            if isinstance(idx, (int, slice)):
                v = self.coords[k][idx]
                if not isinstance(v, (list, np.ndarray)):
                    v = [v]
                r[k] = v
            elif isinstance(idx, list):
                r[k] = [self.coords[k][i] for i in idx]
        return r

    def _check(self):
        if self._shape != self._user_shape + self._field_shape:
            raise ValueError(
                f"shape={self._shape} differs from expected shape={self._user_shape} + {self._field_shape}"
            )

        s = tuple(len(v) for _, v in self._coords.items())
        if s != self._shape:
            raise ValueError(
                f"shape={self._shape} does not match shape deduced from coords={s}"
            )

    def copy(self, data=None):
        if data is None:
            data = self.to_numpy().copy()
        return ArrayTensor(data, self.coords, self.field_shape)


class FieldListTensor(TensorCore):
    def __init__(self, source, coords, user_shape, field_shape, flatten_values):
        self.source = source
        self._coords = coords
        self._user_coords = {
            k: coords[k] for k in list(coords.keys())[: -len(field_shape)]
        }
        self._shape = user_shape + field_shape
        self._user_shape = user_shape
        self._field_shape = field_shape
        self.flatten_values = flatten_values

        # consistency check
        self._check()

        if len(self.source) != math.prod(self._user_shape):
            raise ValueError(
                (
                    f"user shape={self._user_shape} does not match number of available "
                    f"fields={len(self.source)}"
                )
            )

    @classmethod
    def from_tensor(cls, owner, source, coords):
        shape = tuple(len(v) for _, v in coords.items())
        flatten_values = owner.flatten_values
        field_shape = FieldListTensor._get_field_shape(source[0], flatten_values)
        user_shape = [x for x in shape[: -len(field_shape)]]
        if len(user_shape) == 1:
            user_shape = (user_shape,)
        else:
            user_shape = tuple(user_shape)

        return cls(source, coords, user_shape, field_shape, flatten_values)

    @classmethod
    def from_fieldlist(cls, ds, *args, remapping=None, flatten_values=False):
        assert len(ds), f"No data in {ds}"

        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            args = args[0]

        names = []
        for a in args:
            if isinstance(a, str):
                names.append(a)
            elif isinstance(a, dict):
                names += list(a.keys())

        # Sort the source
        source = ds.order_by(*args, remapping=remapping)

        # Get a mapping of user names to unique values
        # With possible reduce dimensionality if the user uses 'level+param'
        coords = CubeCoords(ds.unique_values(*names, remapping=remapping))
        for k, v in coords.items():
            coords[k] = sorted(v)

        # print(f"{self.user_coords=}")

        user_shape = tuple(len(v) for k, v in coords.items())

        # determine field shape
        field_shape = FieldListTensor._get_field_shape(source[0], flatten_values)

        # shape = user_shape + field_shape

        if len(field_shape) == 1:
            coords["values"] = np.linspace(
                0, field_shape[0], field_shape[0] + 1, dtype=int
            )

        if len(field_shape) == 2:
            f = source[0]
            geo = f.metadata().geography
            lat = geo.distinct_latitudes()
            lon = geo.distinct_longitudes()
            if len(lat) == field_shape[0] and len(lon) == field_shape[1]:
                coords["latitude"] = lat
                coords["longitude"] = lon
            else:
                coords["x"] = np.linspace(
                    0, field_shape[0], field_shape[0] + 1, dtype=int
                )
                coords["y"] = np.linspace(
                    0, field_shape[1], field_shape[1] + 1, dtype=int
                )

        return cls(source, coords, user_shape, field_shape, flatten_values)

    @flatten_arg
    def to_numpy(self, **kwargs):
        return self.source.to_numpy(**kwargs).reshape(*self.shape)

    @flatten_arg
    def latitudes(self, **kwargs):
        return self.source[0].data("lat", **kwargs)

    @flatten_arg
    def longitudes(self, **kwargs):
        return self.source[0].data("lon", **kwargs)

    def _subset(self, indexes):
        # Map the slices to a list of indexes per dimension
        coords = []
        # print(f"{indexes=}")
        for s, c in zip(indexes, self._user_shape):
            lst = np.array(list(range(c)))[s].tolist()
            if not isinstance(lst, list):
                lst = [lst]
            coords.append(lst)
            # print(f"{coords=}")

        # Transform the coordinates to a list of indexes for the underlying dataset
        dataset_indexes = []
        user_shape = self._user_shape
        for x in itertools.product(*coords):
            i = coords_to_index(x, user_shape)
            assert isinstance(i, int), i
            dataset_indexes.append(i)

        coords = self._subset_coords(indexes)
        ds = self.source[tuple(dataset_indexes)]
        return self.from_tensor(self, ds, coords)

    # @staticmethod
    # def _get_shape(coords):
    #     return tuple(len(v) for _, v in coords.items())

    @staticmethod
    def _get_field_shape(field, flatten_values):
        field_shape = field.shape

        if flatten_values:
            field_shape = (math.prod(field_shape),)

        assert isinstance(field_shape, tuple), (
            field_shape,
            field,
        )
        return field_shape


class ArrayTensor(TensorCore):
    def __init__(self, array, coords, field_shape):
        self._array = array
        self._coords = coords
        self._shape = self._array.shape
        self._field_shape = field_shape

    def to_numpy(self, **kwargs):
        return self._array

    def _subset(self, indexes):
        coords = self._subset_coords(indexes)
        # print(f"{indexes=}")
        data = self._array[indexes]
        return ArrayTensor(data, coords, self.field_shape)
