# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .fieldlist import FieldList

GRIB_KEYS_NAMES = [
    "class",
    "stream",
    "levtype",
    "type",
    "expver",
    "date",
    "hdate",
    "andate",
    "time",
    "antime",
    "reference",
    "anoffset",
    "verify",
    "fcmonth",
    "fcperiod",
    "leadtime",
    "opttime",
    "origin",
    "domain",
    "method",
    "diagnostic",
    "iteration",
    "number",
    "quantile",
    "levelist",
    "param",
]

LS_KEYS = [
    "name",
    "level",
    "level_type",
    "base_datetime",
    "step",
    "valid_datetime",
    "number",
    "gridType",
]
INDEX_KEYS = list(GRIB_KEYS_NAMES)


def build_remapping(remapping, patches):
    if remapping is not None or patches is not None:
        from earthkit.data.core.order import build_remapping

        remapping = build_remapping(remapping, patches)
    return None


class SimpleFieldList(FieldList):
    def __init__(self, fields=None):
        r"""Initialize a FieldList object."""
        self._fields = fields if fields is not None else []

    # @property
    # def fields(self):
    #     """Return the fields in the list."""
    #     return self._fields

    def append(self, field):
        self._fields.append(field)

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
            if self[0].default_encoder() == "grib":
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
            if self[0].default_encoder() in ("grib", "dict"):
                from earthkit.data.readers.grib.xarray import XarrayMixIn

                class _C(XarrayMixIn, SimpleFieldList):
                    pass

                return _C(self._fields).to_xarray(*args, **kwargs)
        else:
            import xarray as xr

            return xr.Dataset()

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        assert len(args) == 2
        fs = args[0]
        indices = list(args[1])
        return cls.from_fields([fs._fields[i] for i in indices])

    @classmethod
    def merge(cls, sources):
        if not all(isinstance(_, SimpleFieldList) for _ in sources):
            raise ValueError("SimpleFieldList can only be merged to another SimpleFieldLists")

        from itertools import chain

        return cls.from_fields(list(chain(*[f for f in sources])))


class LazySimpleFieldList(SimpleFieldList):
    def __init__(self, maker):
        self._fields = [None] * maker.size
        self._maker = maker

    def _getitem(self, n):
        if isinstance(n, int):
            r = self._fields[n]
            if r is None:
                r = self._maker(n)
                self._fields[n] = r
            return r
        return None
