# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

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


class FieldCubeCore(metaclass=ABCMeta):
    _shape = None
    _field_shape = None
    _coords = None
    _array = None
    flatten_values = None

    @property
    def shape(self):
        return self._shape

    @property
    def coords(self):
        return self._coords

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

        coords = self.subset_coords(indexes)
        return MaskedCube(self, indexes, coords)

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

        indexes = []
        for k, v in self.coords.items():
            if k in r:
                indexes.append(r[k])
            else:
                indexes.append(slice(None, None, None))

        indexes = tuple(indexes)
        # print(f"{indexes=}")

        coords = self.subset_coords(indexes)

        return MaskedCube(self, indexes, coords)

    def subset_coords(self, indexes):
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


class FieldListCube(FieldCubeCore):
    def __init__(self, ds, *args, remapping=None, flatten_values=False):
        assert len(ds), f"No data in {ds}"
        self.flatten_values = flatten_values
        # self._array = None
        # self._field_shape = None

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
        self._coords = CubeCoords(ds.unique_values(*names, remapping=remapping))
        for k, v in self._coords.items():
            self._coords[k] = sorted(v)

        # print(f"{self.user_coords=}")

        self._shape = tuple(len(v) for k, v in self._coords.items())
        self._shape = self._shape + self.field_shape

        if len(self._field_shape) == 1:
            self._coords["position"] = [list(range(self._field_shape[0]))]

        if len(self._field_shape) == 2:
            latlon = self.source[0].to_latlon(flatten=False)
            self._coords["latitude"] = latlon["lat"][:, 0]
            self._coords["longitude"] = latlon["lon"][0]

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

    def to_numpy(self, **kwargs):
        if self._array is None:
            # print(f"shape={self.source.to_numpy(**kwargs).shape}")
            _kwargs = dict(kwargs)
            _kwargs["flatten"] = self.flatten_values
            # print(f"kwargs={_kwargs} shape={self.source.to_numpy(**_kwargs).shape}")
            self._array = self.source.to_numpy(**_kwargs).reshape(*self.shape)
        return self._array


class ArrayCube(FieldCubeCore):
    def __init__(self, array, coords):
        self._array = array
        self._coords = coords
        self._shape = self._array.shape

    def to_numpy(self, **kwargs):
        return self._array


class MaskedCube(FieldCubeCore):
    def __init__(self, cube, indexes, coords):
        self.owner = cube
        self.indexes = indexes
        self._coords = coords
        self._shape = tuple(len(v) for _, v in self._coords.items())
        # print(f"MaskedCube indexes={self.indexes} {self._shape} {self._coords}")

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

    @property
    def field_shape(self):
        if self._field_shape is None:
            if len(self.owner.field.shape) == 1:
                return (self.shape[-1],)
            elif len(self.owner.field.shape) == 2:
                return (self.shape[-2], self.shape[-1])
            else:
                raise ValueError(
                    f"Invalid field shape in owner = {self.owner.field_shape}"
                )
        return self._field_shape
