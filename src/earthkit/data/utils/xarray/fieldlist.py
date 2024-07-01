# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import logging
from collections import defaultdict

from earthkit.data.core.order import build_remapping
from earthkit.data.indexing.fieldlist import FieldArray

LOG = logging.getLogger(__name__)


def _get_common_attributes(ds, keys):
    common_entries = {}
    if len(ds) > 0:
        first = ds[0]
        common_entries = {key: first.metadata(key) for key in keys if key in first.metadata()}
        for f in ds[1:]:
            dictionary = f.metadata()
            common_entries = {
                key: value
                for key, value in common_entries.items()
                if key in dictionary and common_entries[key] == dictionary[key]
            }
    return common_entries


class WrappedFieldList(FieldArray):
    def __init__(self, fieldlist, keys, db=None, fields=None, remapping=None):
        super().__init__()
        self.ds = fieldlist
        self.keys = keys
        self.db = db if db is not None else []

        # self.remapping = build_remapping(remapping)
        self.remapping = remapping
        if self.remapping is not None:
            self.remapping = build_remapping(remapping)
        if fields is not None:
            self.fields = fields
        else:
            self._parse()

    def _parse(self):
        indices = defaultdict(set)
        for i, f in enumerate(self.ds):
            r = f._attributes(self.keys, remapping=self.remapping)
            self.db.append(r)
            self.append(WrappedField(None, r, self.ds, i))

            for k, v in r.items():
                if v is not None:
                    indices[k].add(v)

        self._md_indices = {k: sorted(list(v)) for k, v in indices.items()}

    def common_attributes(self, keys):
        """Return the common attributes for all fields in the list"""
        if self.db:
            return {
                k: v
                for k, v in self.db[0].items()
                if k in keys and all([d[k] is not None and v == d[k] for d in self.db])
            }

    def common_attributes_other(self, ds, keys):
        common_entries = dict()
        for f in ds:
            if not common_entries:
                common_entries = {k: f.metadata(k) for k in keys}
            else:
                d = f.metadata(list(common_entries.keys()))
                common_entries = {
                    key: value
                    for i, (key, value) in enumerate(common_entries.items())
                    if d[i] is not None and value == d[i]
                }

        return common_entries

    def common_indices(self):
        return {k: v[0] for k, v in self.indices().items() if len(v) == 1}


# def flatten_arg(func):
#     @functools.wraps(func)
#     def wrapped(self, *args, **kwargs):
#         _kwargs = {**kwargs}
#         _kwargs["flatten"] = len(self.field_shape) == 1
#         return func(self, *args, **_kwargs)

#     return w


class WrappedField:
    def __init__(self, field, metadata, ds, idx):
        self._field = field
        self._meta = metadata
        self._ds = ds
        self._idx = idx

    @property
    def field(self):
        if self._field is None:
            self._field = self._ds[self._idx]
        return self._field

    def unload(self):
        self._field = None

    def clear_meta(self):
        self._meta = {}

    def _keys(self, *args):
        key = []
        key_arg_type = None
        if len(args) == 1 and isinstance(args[0], str):
            key_arg_type = str
        elif len(args) >= 1:
            key_arg_type = tuple
            for k in args:
                if isinstance(k, list):
                    key_arg_type = list
                    break

        for k in args:
            if isinstance(k, str):
                key.append(k)
            elif isinstance(k, (list, tuple)):
                key.extend(k)
            else:
                raise ValueError(f"metadata: invalid key argument={k}")

        return key, key_arg_type

    def metadata(self, *keys, **kwargs):
        if not keys:
            return self.field.metadata(*keys, **kwargs)

        _k, key_arg_type = self._keys(*keys)
        assert isinstance(_k, list)
        if all(k in self._meta for k in _k):
            r = []
            for k in _k:
                r.append(self._meta[k])
            if key_arg_type is str:
                return r[0]
            elif key_arg_type is tuple:
                return tuple(r)
            else:
                return r

        # print(f"Key={_k} not found in local metadata")
        r = self.field.metadata(*keys, **kwargs)
        self.unload()
        return r

    def __getattr__(self, name):
        return getattr(self.field, name)

    def to_numpy(self, *args, **kwargs):
        v = self.field.to_numpy(*args, **kwargs)
        self.unload()
        return v