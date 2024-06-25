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
from abc import ABCMeta
from abc import abstractmethod

import numpy as np

from earthkit.data.core.index import Selection
from earthkit.data.core.index import normalize_selection

LOG = logging.getLogger(__name__)


def coords_to_index(coords, shape) -> int:
    """
    Map user coords to field index"""
    index = 0
    n = 1
    for i in range(len(coords) - 1, -1, -1):
        index += coords[i] * n
        n *= shape[i]
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
    _user_coords = None
    _user_dims = None
    _user_shape = None
    _field_coords = None
    _field_dims = None
    _field_shape = None
    # _coords = None
    _array = None
    _data = None
    flatten_values = None

    @property
    def full_shape(self):
        return self._full_shape

    @property
    def user_shape(self):
        return self._user_shape

    @property
    def field_shape(self):
        return self._field_shape

    @property
    def full_dims(self):
        d = dict(self._user_dims)
        d.update(self._field_dims)
        return d

    @property
    def user_dims(self):
        return self._user_dims

    @property
    def field_dims(self):
        return self._field_dims

    @property
    def full_coords(self):
        d = dict(self._user_coords)
        d.update(self._field_coords)
        return d

    @property
    def user_coords(self):
        return self._user_coords

    @property
    def field_coords(self):
        return self._field_coords

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

        while len(indexes) <= len(self.user_shape):
            indexes.append(slice(None, None, None))

        while len(indexes) > len(self.user_shape):
            indexes.pop()

        print(f"{indexes=} user_shape={self.user_shape=}")
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
                i for i, element in enumerate(self.user_coords[k]) if selection.match_element(element)
            )
            if len(r[k]) == 1:
                v = r[k][0]
                r[k] = slice(v, v + 1)
                # r[k] = r[k][0]

        indexes = []
        for k, v in self.user_coords.items():
            if k in r:
                indexes.append(r[k])
            else:
                indexes.append(slice(None, None, None))

        indexes = tuple(indexes)
        # print(f"{indexes=}")

        return self._subset(indexes)

    def isel(self, *args, remapping=None, **kwargs):
        # print("isel", args, kwargs)
        # print("isel", self.coords)
        kwargs = normalize_selection(*args, **kwargs)

        indexes = []
        for k, v in self.user_coords.items():
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
        for i, k in enumerate(self.user_coords.keys()):
            if i < len(indexes):
                idx = indexes[i]
                # print(f"{k=} {idx=} {self.coords[k]}")
                # print(self.coords[k][idx])
                if isinstance(idx, (int, slice)):
                    v = self._user_coords[k][idx]
                    if not isinstance(v, (list, np.ndarray)):
                        v = [v]
                    r[k] = v
                elif isinstance(idx, list):
                    r[k] = [self.coords[k][i] for i in idx]
            else:
                r[k] = self._user_coords[k]
        return r

    def _check(self):
        if self._full_shape != self._user_shape + self._field_shape:
            raise ValueError(
                (
                    f"shape={self._full_shape} differs from expected shape="
                    f"{self._user_shape} + {self._field_shape}"
                )
            )

        shape = self._coords_shape(self._user_coords) + self._dims_shape(self._field_dims)
        if shape != self._full_shape:
            raise ValueError(f"shape={self._full_shape} does not match shape deduced from coords={shape}")

    def copy(self, data=None):
        if data is None:
            data = self.to_numpy().copy()
        return ArrayTensor(data, self.coords, self.field_shape)

    @staticmethod
    def _coords_shape(coords):
        return tuple(len(v) for _, v in coords.items())

    @staticmethod
    def _dims_shape(dims):
        return tuple(v for _, v in dims.items())


class FieldListTensor(TensorCore):
    def __init__(
        self,
        source,
        user_coords,
        field_coords,
        field_dims,
        flatten_values,
    ):
        # print(f"FieldListTensor field_coords={field_coords.keys()} {field_dims=}")

        self.source = source
        self._user_coords = user_coords
        self._user_shape = self._coords_shape(user_coords)
        self._user_dims = {k: len(v) for k, v in user_coords.items()}
        self._field_coords = field_coords
        self._field_shape = self._dims_shape(field_dims)
        self._field_dims = field_dims
        self._full_shape = self._user_shape + self._field_shape
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
    def from_tensor(cls, owner, source, user_coords):
        # # print(f"from_tensor {coords=}")
        # user_shape = tuple(len(v) for _, v in user_coords.items())
        # flatten_values = owner.flatten_values

        # # field_shape = FieldListTensor._get_field_shape(source[0], flatten_values)
        # user_shape = [x for x in shape[: -len(field_shape)]]
        # if len(user_shape) == 1:
        #     user_shape = (user_shape,)
        # else:
        #     user_shape = tuple(user_shape)

        # # return cls(source, coords, user_shape, field_shape, flatten_values)

        return cls(
            source,
            user_coords,
            owner.field_coords,
            owner.field_dims,
            owner.flatten_values,
        )

    @classmethod
    def from_fieldlist(
        cls,
        ds,
        *args,
        remapping=None,
        flatten_values=False,
        sort=True,
        progress_bar=True,
        field_dims_and_coords=None,
    ):
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
        if names and sort:
            source = ds.order_by(*args, remapping=remapping)
        else:
            source = ds

        # Get a mapping of user names to unique values
        # With possible reduce dimensionality if the user uses 'level+param'
        if names:
            user_coords = CubeCoords(ds.unique_values(*names, remapping=remapping, progress_bar=progress_bar))
            for k, v in user_coords.items():
                user_coords[k] = sorted(v)
        else:
            user_coords = CubeCoords()

        # print(f"{self.user_coords=}")

        # user_shape = tuple(len(v) for _, v in user_coords.items())

        # field properties
        if field_dims_and_coords is not None:
            field_dims, field_coords = field_dims_and_coords
        else:
            field_dims, field_coords = FieldListTensor._field_part(source[0], flatten_values)

        # first = source[0]

        # # determine field shape
        # field_shape = FieldListTensor._get_field_shape(first, flatten_values)
        # real_field_shape = first.shape

        # # shape = user_shape + field_shape

        # if field_coords is None or not field_coords:
        #     field_coords = FieldListTensor.make_geo_coords(source[0], field_shape)
        # coords.update(geo_coords)

        # from earthkit.data.utils.diag import Diag

        # diag = Diag("T")
        # if len(field_shape) == 1:
        #     coords["values"] = np.linspace(0, field_shape[0], field_shape[0], dtype=int)

        # if len(field_shape) == 2:
        #     if geo_coords is not None:
        #         for k, v in geo_coords.items():
        #             coords[k] = v
        #     else:
        #         f = source[0]
        #         diag(" LATLON")
        #         geo = f.metadata().geography
        #         lat = geo.distinct_latitudes()
        #         lon = geo.distinct_longitudes()
        #         diag(" LATLON")
        #         if len(lat) == field_shape[0] and len(lon) == field_shape[1]:
        #             coords["latitude"] = lat
        #             coords["longitude"] = lon
        #         else:
        #             coords["x"] = np.linspace(
        #                 0, field_shape[0], field_shape[0], dtype=int
        #             )
        #             coords["y"] = np.linspace(
        #                 0, field_shape[1], field_shape[1], dtype=int
        #             )

        #         if hasattr(f, "unload"):
        #             f.unload()
        # diag(" LATLON")
        return cls(source, user_coords, field_coords, field_dims, flatten_values)

    @flatten_arg
    def to_numpy(self, field_index=None, **kwargs):
        if field_index is not None:
            if all(i == slice(None, None, None) for i in field_index):
                field_index = None

        if field_index is None:
            return self.source.to_numpy(**kwargs).reshape(*self.full_shape)
        else:
            n = self.source.to_numpy(field_index=field_index, **kwargs)
            shape = list(self._user_shape)
            shape += list(n.shape[1:])
            return n.reshape(*shape)

    @flatten_arg
    def latitudes(self, **kwargs):
        return self.source[0].data("lat", **kwargs)

    @flatten_arg
    def longitudes(self, **kwargs):
        return self.source[0].data("lon", **kwargs)

    def field_indexes(self, indexes):
        assert len(indexes) == len(self._full_shape)
        return indexes[len(self._user_shape) :]

    def _subset(self, indexes):
        """Only allow subsetting for the user coordinates.
        Indices for the field coordinates are ignored.
        """
        # Map the slices to a list of indexes per dimension
        assert len(indexes) >= len(self._user_shape)
        user_coords = []
        user_indexes = []

        for s, c in zip(indexes, self._user_shape):
            lst = np.array(list(range(c)))[s].tolist()
            if not isinstance(lst, list):
                lst = [lst]
            user_coords.append(lst)
            user_indexes.append(s)

        assert len(user_coords) == len(self._user_coords)

        dataset_indexes = []
        user_shape = self._user_shape
        for x in itertools.product(*user_coords):
            i = coords_to_index(x, user_shape)
            assert isinstance(i, int), i
            dataset_indexes.append(i)

        coords = self._subset_coords(user_indexes)
        assert len(coords) == len(self._user_coords)
        ds = self.source[tuple(dataset_indexes)]
        return self.from_tensor(self, ds, coords)

    # @staticmethod
    # def _get_shape(coords):
    #     return tuple(len(v) for _, v in coords.items())

    @staticmethod
    def _field_part(field, flatten_values):
        field_shape = field.shape

        if flatten_values:
            field_shape = (math.prod(field_shape),)

        assert isinstance(field_shape, tuple), (
            field_shape,
            field,
        )

        coords = {}
        dims = {}

        print(f"{field_shape=}")

        if len(field_shape) == 1:
            try:
                ll = field.to_latlon(flatten=True)
                coords["latitude"] = ll["lat"]
                coords["longitude"] = ll["lon"]
            except Exception:
                pass
            dims["values"] = field_shape[0]
        elif len(field_shape) == 2:
            # diag(" LATLON")
            geo = field.metadata().geography
            lat = geo.distinct_latitudes()
            lon = geo.distinct_longitudes()
            # diag(" LATLON")
            if len(lat) == field_shape[0] and len(lon) == field_shape[1]:
                coords["latitude"] = lat
                coords["longitude"] = lon
                dims["latitude"] = len(lat)
                dims["longitude"] = len(lon)
            else:
                ll = field.to_latlon(flatten=True)
                # coords["latitude"] = ll["lat"]
                # coords["longitude"] = ll["lon"]
                coords["latitude"] = ll["lat"].reshape(field_shape)
                coords["longitude"] = ll["lon"].reshape(field_shape)
                # coords["x"] = np.linspace(0, field_shape[0], field_shape[0], dtype=int)
                # coords["y"] = np.linspace(0, field_shape[1], field_shape[1], dtype=int)
                dims["y"] = field_shape[0]  # len(coords["y"])
                dims["x"] = field_shape[1]  # len(coords["x"])

        if hasattr(field, "unload"):
            field.unload()

        return dims, coords

    # @staticmethod
    # def _get_field_shape(field, flatten_values):
    #     field_shape = field.shape

    #     if flatten_values:
    #         field_shape = (math.prod(field_shape),)

    #     assert isinstance(field_shape, tuple), (
    #         field_shape,
    #         field,
    #     )
    #     return field_shape

    # @staticmethod
    # def make_geo_coords(field, field_shape):
    #     from earthkit.data.utils.diag import Diag

    #     coords = {}

    #     # diag = Diag("T")
    #     if len(field_shape) == 1:
    #         coords["values"] = np.linspace(0, field_shape[0], field_shape[0], dtype=int)

    #     if len(field_shape) == 2:
    #         f = field
    #         # diag(" LATLON")
    #         geo = f.metadata().geography
    #         lat = geo.distinct_latitudes()
    #         lon = geo.distinct_longitudes()
    #         # diag(" LATLON")
    #         if len(lat) == field_shape[0] and len(lon) == field_shape[1]:
    #             coords["latitude"] = lat
    #             coords["longitude"] = lon
    #         else:
    #             coords["x"] = np.linspace(0, field_shape[0], field_shape[0], dtype=int)
    #             coords["y"] = np.linspace(0, field_shape[1], field_shape[1], dtype=int)

    #         if hasattr(f, "unload"):
    #             f.unload()
    #     # diag(" LATLON")
    #     return coords

    def make_valid_datetime(self):
        dims_opt = [
            ["base_datetime", "step"],
            ["date", "time", "step"],
            ["date", "time"],
            ["date", "step"],
            ["time", "step"],
            ["step"],
        ]

        for dims in dims_opt:
            if all(d in self.user_dims for d in dims):
                # use same dim order as in user_dims
                dims = [d for d in dims if d in self.user_dims]
                other_dims = [d for d in self.user_dims if d not in dims]
                if other_dims:
                    import datetime

                    import numpy as np

                    other_coords = {
                        k: next(iter(self.user_coords[k])) for k in other_dims if k in self.user_coords
                    }

                    vals = np.array(
                        [
                            datetime.datetime.fromisoformat(x)
                            for x in self.source.sel(**other_coords).metadata("valid_datetime")
                        ]
                    )

                    shape = tuple([self.user_dims[d] for d in dims])
                    return tuple(dims), vals.reshape(shape)
        return None, None


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