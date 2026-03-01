# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

from earthkit.utils.decorators import thread_safe_cached_property

from earthkit.data.core.field import Field

from .indexed import IndexFieldListBase


class SimpleFieldListBase(IndexFieldListBase):
    @property
    @abstractmethod
    def _fields(self):
        pass

    def _getitem(self, n):
        if isinstance(n, int):
            return self._fields[n]

    def __len__(self):
        return len(self._fields)

    def mutate_source(self):
        return self

    def __getstate__(self) -> dict:
        ret = {}
        # print("SimpleFieldList Getstate")
        ret["_fields"] = self._fields
        return ret

    def __setstate__(self, state: dict):
        # print("SimpleFieldList Setstate")
        self._fields = state.pop("_fields")

    def to_pandas(self, *args, **kwargs):
        # TODO make it generic
        if len(self) > 0:
            if self[0]._default_encoder() == "grib":
                from earthkit.data.readers.grib.pandas import PandasMixIn

                class _C(PandasMixIn, SimpleFieldList):
                    pass

                return _C(self._fields).to_pandas(*args, **kwargs)
        else:
            import pandas as pd

            return pd.DataFrame()

    def to_xarray(self, *args, **kwargs):
        # TODO make it generic
        if len(self) > 0:
            encoder = self[0]._default_encoder()
            if encoder == "grib" or encoder is None:
                from earthkit.data.readers.grib.xarray import XarrayMixIn

                class _C(XarrayMixIn, SimpleFieldList):
                    pass

                return _C(self._fields).to_xarray(*args, **kwargs)
        else:
            import xarray as xr

            return xr.Dataset()

    def _default_encoder(self):
        if len(self) > 0:
            return self[0]._default_encoder()

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        assert len(args) == 2
        fs = args[0]
        indices = list(args[1])
        return cls.from_fields([fs._fields[i] for i in indices])

    @classmethod
    def merge(cls, sources):
        for s in sources:
            if not isinstance(s, SimpleFieldListBase):
                raise ValueError("SimpleFieldList can only be merged to another SimpleFieldLists")

        if not all(isinstance(_, SimpleFieldListBase) for _ in sources):
            raise ValueError("SimpleFieldList can only be merged to another SimpleFieldLists")

        from itertools import chain

        return cls.from_fields(list(chain(*[f for f in sources])))


class SimpleFieldList(SimpleFieldListBase):
    def __init__(self, fields=None):
        r"""Initialize a FieldList object."""
        if isinstance(fields, Field):
            fields = [fields]

        self.__fields = fields if fields is not None else []

    @property
    def _fields(self):
        return self.__fields

    def __getstate__(self) -> dict:
        ret = {}
        ret["_fields"] = self._fields
        return ret

    def __setstate__(self, state: dict):
        fields = state.pop("_fields")
        self.__init__(fields)


# class LazySimpleFieldList(SimpleFieldListCore):
#     def __init__(self, maker):
#         self._f = [None] * maker.size
#         self._maker = maker

#     @property
#     def _fields(self):
#         return self._f

#     def _getitem(self, n):
#         if isinstance(n, int):
#             r = self._fields[n]
#             if r is None:
#                 r = self._maker(n)
#                 self._fields[n] = r
#             return r
#         return None


class LazySimpleFieldList(SimpleFieldListBase):
    def __init__(self, reader):
        self._reader = reader

    @thread_safe_cached_property
    def _fields(self):
        fields = [x for x in self._reader]
        self._reader = None
        return fields

    def __getstate__(self) -> dict:
        ret = {}
        # print("SimpleFieldList Getstate")
        ret["_fields"] = self._fields
        return ret

    def __setstate__(self, state: dict):
        # print("SimpleFieldList Setstate")
        fields = state.pop("_fields")
        self.__init__(fields)
