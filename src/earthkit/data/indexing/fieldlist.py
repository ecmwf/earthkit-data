# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.core.fieldlist import FieldList


class SimpleFieldList(FieldList):
    def __init__(self, fields=None):
        self.fields = fields if fields is not None else []

    def append(self, field):
        self.fields.append(field)

    def _getitem(self, n):
        return self.fields[n]

    def __len__(self):
        return len(self.fields)

    def __repr__(self) -> str:
        return f"FieldArray({len(self.fields)})"

    def __getstate__(self) -> dict:
        ret = {}
        ret["_fields"] = self.fields
        return ret

    def __setstate__(self, state: dict):
        self.fields = state.pop("_fields")
        # self._array = state.pop("_array")
        # self._metadata = state.pop("_metadata")
        # super().__init__(metadata=self._metadata)

    def to_pandas(self, *args, **kwargs):
        from earthkit.data.readers.grib.pandas import PandasMixIn

        class _C(PandasMixIn, SimpleFieldList):
            pass

        return _C(self.fields).to_pandas(*args, **kwargs)

    def to_xarray(self, *args, **kwargs):
        from earthkit.data.readers.grib.xarray import XarrayMixIn

        class _C(XarrayMixIn, SimpleFieldList):
            pass

        print("len(self.fields)=", len(self.fields))
        return _C(self.fields).to_xarray(*args, **kwargs)

    def mutate_source(self):
        return self

    @classmethod
    def new_mask_index(self, *args, **kwargs):
        assert len(args) == 2
        fs = args[0]
        indices = list(args[1])
        return SimpleFieldList(fields=[fs.fields[i] for i in indices])

    @classmethod
    def merge(cls, sources):
        if not all(isinstance(_, SimpleFieldList) for _ in sources):
            raise ValueError("SimpleFieldList can only be merged to another SimpleFieldLists")
        # if not all(s.array_backend is s[0].array_backend for s in sources):
        #     raise ValueError("Only fieldlists with the same array backend can be merged")

        from itertools import chain

        return cls.from_fields(list(chain(*[f for f in sources])))


# For backwards compatibility
FieldArray = SimpleFieldList
