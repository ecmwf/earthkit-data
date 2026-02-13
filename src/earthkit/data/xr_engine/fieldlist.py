# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import logging
from collections import defaultdict

from earthkit.data.core.index import Selection
from earthkit.data.core.index import normalize_selection
from earthkit.data.core.order import build_remapping
from earthkit.data.indexing.fieldlist import FieldList

LOG = logging.getLogger(__name__)


class _CollectorJoiner:
    # PW: TODO: dead code due to `component` removal
    def __init__(self, func):
        self.func = func

    def format_name(self, x, **kwargs):
        return self.func(x, **kwargs)

    def format_string(self, x):
        return str(x)

    def join(self, args):
        remapped = "".join(str(x) for x in args)
        components = tuple([str(x) for x in args[1::2]])
        return (remapped, components)

    @staticmethod
    def patch(patch, value):
        if isinstance(value, tuple) and len(value) == 2:
            return patch(value[0]), value[1]
        return patch(value)


class IndexSelection(Selection):
    def match_element(self, element):
        return all(v(element) for k, v in self.actions.items())


class IndexDB:
    def __init__(self, index):
        # print(f"IndexDB: {index=}")
        self._index = index if index is not None else dict()

    def index(self, key, maker=None):
        # LOG.debug(f"index(): {key=} {self._index=}")
        if key not in self._index:
            # # LOG.debug(f"Key={key} not found in IndexDB")
            if maker is not None:
                self._index[key] = maker(key)[0][key]
            else:
                raise KeyError(f"Could not find index for {key=}")
        return self._index[key]

    def collect(self, keys):
        remaining_keys = list(keys)
        indices = dict()
        for k in keys:
            if k in self._index:
                indices[k] = self._index[k]
                remaining_keys.remove(k)
        return remaining_keys, indices

    def filter(self, *args, **kwargs):
        kwargs = normalize_selection(*args, **kwargs)

        index = dict()

        for k in self._index:
            if k in kwargs:
                selection = IndexSelection(dict(k=kwargs[k]))
                idx = list(i for i, element in enumerate(self._index[k]) if selection.match_element(element))
                index[k] = [self._index[k][i] for i in idx]
            else:
                index[k] = self._index[k]
        return IndexDB(index)

    def __repr__(self) -> str:
        return f"IndexDB(_index={self._index})"


class XArrayInputFieldList(FieldList):
    """
    A wrapper around a fieldlist that stores unique values.

    Only for internal use for building Xarray datasets.
    """

    def __init__(self, fieldlist, keys=None, db=None, remapping=None, scan_only=False):
        super().__init__()
        self.ds = fieldlist

        self.remapping = remapping
        if self.remapping is not None:
            self.remapping = build_remapping(remapping)

        self.db = IndexDB(None)
        if db is not None:
            self.db = db
        elif keys:
            # PW: DEBUG
            print(f"{keys=}", flush=True)
            print(f"{self.unique_values(keys)=}", flush=True)
            self.db = IndexDB(self.unique_values(keys))

        assert self.db

    def index(self, key):
        return self.db.index(key, self.unique_values)

    def _getitem(self, n):
        return self.ds._getitem(n)

    def __getitem__(self, n):
        return self.ds[n]

    def __len__(self):
        return len(self.ds)

    def make_releasable(self):
        self.ds = FieldList.from_fields([ReleasableField(f) for f in self.ds])

    def group(self, key, values):
        values = set(values)
        groups = defaultdict(list)
        for i, f in enumerate(self.ds):
            v = str(f.get(key, remapping=self.remapping, default=None))
            if v in values:
                groups[v].append(i)

        for k, v in groups.items():
            if not v:
                continue
            db = None
            # db = self.db   # TODO: would be nice but it does not work...
            mask_index = self.ds[v]
            groups[k] = XArrayInputFieldList(mask_index, db=db, remapping=self.remapping)

        return groups

    def sel(self, *args, **kwargs):
        assert "remapping" not in kwargs
        assert "patches" not in kwargs
        ds = self.ds.sel(*args, remapping=self.remapping, **kwargs)
        db = None
        # if not args and self.db and all(k in self.db for k in kwargs):
        #     db = self.db.filter(**kwargs)
        return XArrayInputFieldList(ds, db=db, remapping=self.remapping)

    def order_by(self, *args, **kwargs):
        if isinstance(self.ds, XArrayInputFieldList):
            kwargs.pop("remapping", None)

        assert "remapping" not in kwargs
        assert "patches" not in kwargs

        if isinstance(self.ds, XArrayInputFieldList):
            ds = self.ds.order_by(*args, **kwargs)
            return ds
        else:
            ds = self.ds.order_by(*args, remapping=self.remapping, **kwargs)
            ds = XArrayInputFieldList(
                ds,
                db=self.db,
                remapping=self.remapping,
            )
            return ds

    def unique_values(self, names):
        if isinstance(names, str):
            names = [names]

        keys, indices = self.db.collect(names)

        if keys:
            astype = [None] * len(keys)
            default = [None] * len(keys)
            vals = defaultdict(dict)
            for f in self.ds:
                r = f._get_fast(keys, default=default, astype=astype, remapping=self.remapping, output=dict)
                for k, v in r.items():
                    vals[k][v] = True

            vals = {k: tuple(values.keys()) for k, values in vals.items()}

            for k, v in vals.items():
                v = [x for x in v if x is not None]
                if all(isinstance(x, (int, datetime.timedelta)) for x in v):
                    vals[k] = sorted(v)
                else:
                    vals[k] = sorted(v, key=str)

            for k, v in vals.items():
                indices[k] = v

        return indices

    def unwrap(self):
        ds = self.ds
        while isinstance(ds, XArrayInputFieldList):
            ds = ds.ds
        return ds

    # PW: TODO: consider if this method shouldn't be put elsewhere
    def _get_user_coords_to_fl_idx(self, keys, remapping=None):
        # this method could be implemented in the class XArrayInputFieldList, but then FieldList.to_tensor wouldn't work
        # PW: actually, now it is...
        if isinstance(keys, str):
            keys = [keys]
        if remapping is None:
            # some subclasses (e.g. XArrayInputFieldList) has remapping as a member
            remapping = getattr(self, "remapping", None)

        user_coords_to_fl_idx = {}
        for i, f in enumerate(self):
            metadata = f.get(
                keys, remapping=remapping
            )  # PW: to be checked (can raise_on_missing? can use _get_fast?)
            user_coords = tuple(metadata)
            assert user_coords not in user_coords_to_fl_idx, (
                f"Multiple fields in {self} with {dict(zip(keys, user_coords))}: "
                f"#{user_coords_to_fl_idx[user_coords]} and #{i}"
            )
            user_coords_to_fl_idx[user_coords] = i

        return user_coords_to_fl_idx

    def __getstate__(self):
        """As a simplification, only serialise the unwrapped fieldlist.
        We can assume that when there is a need for serialisation the wrapper
        structure can be discarded.
        """
        r = {}
        r["ds"] = self.unwrap()
        return r

    def __setstate__(self, state):
        self.ds = state["ds"]
        self.db = None
        self.remapping = None


class ReleasableField:
    def __init__(self, field):
        self.field = field
        self.keep = True
        self.released = False

    def to_numpy(self, *args, **kwargs):
        if self.released:
            return None

        r = self.field.to_numpy(*args, **kwargs)
        if not self.keep:
            self._release()
        return r

    def to_array(self, *args, **kwargs):
        if self.released:
            return None

        r = self.field.to_array(*args, **kwargs)
        if not self.keep:
            self._release()
        return r

    def _release(self):
        if not self.released:
            if hasattr(self.field, "_release"):
                self.field._release()
            self.released = True

    def get(self, *args, **kwargs):
        if self.released:
            return None
        return self.field.get(*args, **kwargs)

    def metadata(self, *args, **kwargs):
        if self.released:
            return None
        return self.field.metadata(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self.field, name)
