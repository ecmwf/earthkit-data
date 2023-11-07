# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
import itertools
import logging
import math
import re

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


class FieldCube:
    def __init__(
        self,
        ds,
        *args,
        remapping=None,
        flatten_values=False,
    ):
        assert len(ds), f"No data in {ds}"

        self.flatten_values = flatten_values
        self._array = None

        if len(args) == 1 and isinstance(args[0], (list, tuple)):
            args = args[0]

        names = []
        for a in args:
            if isinstance(a, str):
                names.append(a)
            elif isinstance(a, dict):
                names += list(a.keys())

        self._field_shape = None

        # Sort the source according to their
        # internal_args = reduce(operator.add, [Separator.split(a) for a in args], [])
        self.source = ds.order_by(*args, remapping=remapping)

        # Get a mapping of user names to unique values
        # With possible reduce dimentionality if the user use 'level+param'
        self.user_coords = ds.unique_values(*names, remapping=remapping)

        # print(f"{self.user_coords=}")

        self.user_shape = tuple(len(v) for k, v in self.user_coords.items())

        if math.prod(self.user_shape) != len(self.source):
            details = []
            for k, v in self.user_coords.items():
                details.append(f"{k=}, {len(v)}, {v}")
            assert not isinstance(
                self.source, str
            ), f"Not expecting a str here ({self.source})"
            for i, f in enumerate(self.source):
                details.append(f"{i}={f}")
                if i > 30:
                    details.append("...")
                    break

            msg = (
                f"Shape {self.user_shape} [{math.prod(self.user_shape):,}]"
                + f" does not match number of available fields {len(self.source):,}. "
                + f"Difference: {len(self.source)-math.prod(self.user_shape):,}"
                + "\n".join(details)
            )
            raise ValueError(msg)

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

    @property
    def extended_user_shape(self):
        return self.user_shape + self.field_shape

    def __str__(self):
        content = ", ".join([f"{k}:{len(v)}" for k, v in self.user_coords.items()])
        return f"{self.__class__.__name__}({content} ({len(self.source)} fields))"

    def squeeze(self):
        # TODO: remove an dimensions of one.
        return self

    def __getitem__(self, indexes_in):
        # Make sure the requested indexes are a list of slices matching the shape
        import copy

        indexes = copy.deepcopy(indexes_in)

        if isinstance(indexes, int):
            indexes = (indexes,)  # make tuple

        if isinstance(indexes, list):
            indexes = tuple(indexes)

        assert isinstance(indexes, tuple), (type(indexes), indexes)

        indexes = list(indexes)

        if indexes[-1] is Ellipsis:
            indexes.pop()

        while len(indexes) < len(self.user_shape):
            indexes.append(slice(None, None, None))

        print(f"indexes={indexes}")

        # Map the slices to a list of indexes per dimension
        coords = []
        for s, c in zip(indexes, self.user_coords.values()):
            lst = list(range(len(c)))[s]
            if not isinstance(lst, list):
                lst = [lst]
            coords.append(lst)

        print(f"coords={coords}")

        return MaskedCube(self, indexes_in, indexes)

        # Transform the coordinates to a list of indexes for the underlying dataset
        dataset_indexes = []
        user_shape = self.user_shape
        for x in itertools.product(*coords):
            i = coords_to_index(x, user_shape)
            dataset_indexes.append(i)

        # print(f"dataset_indexes={dataset_indexes}")
        ds = self.source[tuple(dataset_indexes)]

        # If we match just one element, we return it
        if all(len(_) == 1 for _ in coords):
            return ds[0]

        # For more than one element, we return a new cube
        return FieldCube(
            ds,
            *self.user_coords,
            flatten_values=self.flatten_values,
        )

    def sel(self, *args, remapping=None, **kwargs):
        kwargs = normalize_selection(*args, **kwargs)
        # kwargs = self._normalize_kwargs_names(**kwargs)
        # if not kwargs:
        #     return self

        r = {}
        for k, v in kwargs.items():
            selection = CubeSelection(dict(k=v))
            # for i, element in enumerate(self.user_coords[k]):
            #     print(f"{element=}")

            r[k] = list(
                i
                for i, element in enumerate(self.user_coords[k])
                if selection.match_element(element)
            )

        indexes = []
        for k, v in self.user_coords.items():
            if k in r:
                indexes.append(r[k])
            else:
                indexes.append(slice(None, None, None))

        indexes_in = tuple(indexes)

        print(f"{indexes_in=}")
        print(f"{indexes=}")

        return MaskedCube(self, indexes_in, indexes_in)

        # selection = Selection(kwargs, remapping=remapping)
        # if selection.is_empty:
        #     return self

        # indices = (
        #     i for i, element in enumerate(self) if selection.match_element(element)
        # )

        # return r

    def to_numpy(self, **kwargs):
        if self._array is not None:
            return self._array
        else:
            self._array = self.source.to_numpy(**kwargs).reshape(
                *self.extended_user_shape
            )
            return self._array

    def _names(self, coords, reading_chunks=None, **kwargs):
        if reading_chunks is None:
            reading_chunks = list(coords.keys())
        if isinstance(reading_chunks, (list, tuple)):
            assert all(isinstance(_, str) for _ in reading_chunks)
            reading_chunks = {k: len(coords[k]) for k in reading_chunks}

        for k, requested in reading_chunks.items():
            full_len = len(coords[k])
            assert full_len == requested, "only full chunks supported for now"

        names = list(coords[a] for a, _ in reading_chunks.items())

        return names

    def count(self, reading_chunks=None):
        names = self._names(reading_chunks=reading_chunks, coords=self.user_coords)
        return math.prod(len(lst) for lst in names)

    # def iterate_cubelets(self, reading_chunks=None, **kwargs):
    #     names = self._names(reading_chunks=reading_chunks, coords=self.user_coords)
    #     indexes = list(range(0, len(lst)) for lst in names)

    #     return (
    #         Cubelet(self, i, coords_names=n)
    #         for n, i in zip(itertools.product(*names), itertools.product(*indexes))
    #     )

    def chunking(self, chunks):
        if isinstance(chunks, (str, int)):
            m = re.match(r"(\d+)\s*(.*)?", str(chunks))
            if not m:
                raise ValueError(f"Cannot parse {chunks}")
            size = int(m.group(1))
            unit = m.group(2).lower()
            if unit == "":
                unit = "m"
            size *= dict(k=1024, m=1024 * 1024, g=1024 * 1024 * 1024)[unit[0]]

            # TODO: use dtype.
            # We assuming float32 = 4 bytes per

            rest = math.prod(self.extended_user_shape[1:]) * 4
            first = int(size / rest + 0.5)
            return (first,) + self.extended_user_shape[1:]

        if not chunks:
            return True  # Let ZARR choose

        lst = list(self.user_shape)
        for i, name in enumerate(self.user_coords):
            lst[i] = chunks.get(name, lst[i])

        return tuple(lst)


# class Cubelet:
#     def __init__(self, cube, coords, coords_names=None):
#         self._coords_names = coords_names  # only for display purposes
#         self.owner = cube
#         assert all(isinstance(_, int) for _ in coords), coords
#         self.coords = coords
#         self.flatten_values = cube.flatten_values

#     def __repr__(self):
#         return (
#             f"{self.__class__.__name__}({self.coords},index_names={self._coords_names})"
#         )

#     @property
#     def extended_icoords(self):
#         return self.coords

#     def to_numpy(self, **kwargs):
#         return self.owner[self.coords].to_numpy(
#             reshape=not self.flatten_values, **kwargs
#         )


class MaskedCube:
    def __init__(self, cube, raw_indexes, indexes):
        self.owner = cube
        self.raw_indexes = raw_indexes
        self.indexes = indexes
        self._user_coords = None
        # assert all(isinstance(_, int) for _ in coords), coords

    def to_numpy(self, **kwargs):
        return self.owner.to_numpy(**kwargs)[self.raw_indexes]

    @property
    def user_coords(self):
        r = {}
        cnt = 0
        for k, v in self.owner.user_coords.items():
            idx = self.indexes[cnt]
            if isinstance(idx, (int, slice)):
                r[k] = v[idx]
            elif isinstance(idx, list):
                print(f"{v=} {idx=}")
                r[k] = [v[x] for x in idx]
            cnt += 1
        return r
