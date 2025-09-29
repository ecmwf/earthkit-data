# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from collections import defaultdict

from earthkit.data.decorators import thread_safe_cached_property

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


class FieldListIndices:
    def __init__(self, field_list):
        self.fs = field_list
        self.user_indices = dict()

    @thread_safe_cached_property
    def default_index_keys(self):
        return INDEX_KEYS
        # if len(self.fs) > 0:
        #     return self.fs[0]._metadata.index_keys()
        # else:
        #     return []

    def _index_value(self, key):
        values = set()
        for f in self.fs:
            v = f.get(key, default=None)
            if v is not None:
                values.add(v)

        return sorted(list(values))

    @thread_safe_cached_property
    def default_indices(self):
        indices = defaultdict(set)
        keys = self.default_index_keys
        for f in self.fs:
            v = f.get(keys, default=None)
            for i, k in enumerate(keys):
                if v[i] is not None:
                    indices[k].add(v[i])

        return {k: sorted(list(v)) for k, v in indices.items()}

    def indices(self, squeeze=False):
        r = {**self.default_indices, **self.user_indices}

        if squeeze:
            return {k: v for k, v in r.items() if len(v) > 1}
        else:
            return r

    def index(self, key):
        if key in self.user_indices:
            return self.user_indices[key]

        if key in self.default_index_keys:
            return self.default_indices[key]

        self.user_indices[key] = self._index_value(key)
        return self.user_indices[key]
