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

from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.order import build_remapping

LOG = logging.getLogger(__name__)


class WrappedFieldList(FieldList):
    def __init__(self, fieldlist, keys=None, db=None, remapping=None):
        super().__init__()

        self.ds = fieldlist

        self.remapping = remapping
        if self.remapping is not None:
            self.remapping = build_remapping(remapping)

        self.db = dict()
        if db is not None:
            self.db = db
        elif keys:
            self.db = self.unique_values(keys)

    def index(self, key):
        # print(f"called {key=}")
        if key not in self.db:
            # print(f"Key={key} not found in local metadata")
            self.db[key] = self.unique_values(key)[key]
            # return self.ds.index(key)
        return self.db[key]

    def __getitem__(self, n):
        return self.ds[n]

    def __len__(self):
        return len(self.ds)

    def sel(self, *args, **kwargs):
        assert "remapping" not in kwargs
        assert "patches" not in kwargs
        return WrappedFieldList(
            self.ds.sel(*args, remapping=self.remapping, **kwargs), remapping=self.remapping
        )

    def order_by(self, *args, **kwargs):
        assert "remapping" not in kwargs
        assert "patches" not in kwargs
        return WrappedFieldList(
            self.ds.order_by(*args, remapping=self.remapping, **kwargs), db=self.db, remapping=self.remapping
        )

    def unique_values(self, names):
        if isinstance(names, str):
            names = [names]

        indices = dict()
        keys = list(names)
        for k in names:
            if k in self.db:
                indices[k] = self.db[k]
                keys.remove(k)

        if keys:
            vals = defaultdict(dict)
            for f in self.ds:
                r = f._attributes(keys, remapping=self.remapping)
                for k, v in r.items():
                    vals[k][v] = True

            vals = {k: tuple(values.keys()) for k, values in vals.items()}

            for k, v in vals.items():
                v = [x for x in v if x is not None]
                vals[k] = sorted(v)

            for k, v in vals.items():
                indices[k] = v

        return indices
