# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from collections import namedtuple

from earthkit.data.core.constants import DATETIME
from earthkit.data.core.order import build_remapping
from earthkit.data.core.order import normalize_order_by
from earthkit.data.core.select import normalize_selection
from earthkit.data.decorators import cached_method
from earthkit.data.decorators import normalize
from earthkit.data.indexing.database.sql import SqlDatabase
from earthkit.data.indexing.database.sql import SqlOrder
from earthkit.data.indexing.database.sql import SqlRemapping
from earthkit.data.indexing.database.sql import SqlSelection
from earthkit.data.readers.grib.index.db import FieldListInFilesWithDBIndex
from earthkit.data.utils.serialise import register_serialisation

LOG = logging.getLogger(__name__)

SqlResultCache = namedtuple("SqlResultCache", ["first", "length", "result"])


@normalize(DATETIME, "date-list", format="%Y-%m-%d %H:%M:%S")
def _normalize_grib_kwargs_values(**kwargs):
    return kwargs


class FieldListInFilesWithSqlIndex(FieldListInFilesWithDBIndex):
    DBCLASS = SqlDatabase
    DB_CACHE_SIZE = 100_000
    DB_DICT_CACHE_SIZE = 100_000

    def apply_filters(self, filters):
        obj = self
        for f in filters:
            obj = obj.filter(f)
        return obj

    def _find_all_indices_dict(self):
        from earthkit.data.indexing.database import GRIB_KEYS_NAMES

        d = self.unique_values(*GRIB_KEYS_NAMES, remapping=None, progress_bar=None)

        for k, v in d.items():
            try:
                v.remove(None)
            except ValueError:
                pass
            d[k] = sorted(v)

        return d

    def unique_values(self, *coords, remapping=None, progress_bar=None):
        """Given a list of metadata attributes, such as date, param, levels,
        returns the list of unique values for each attributes
        """
        keys = coords

        remapping = build_remapping(remapping)
        # print("Not using remapping here")

        coords = {k: None for k in coords}
        coords = list(coords.keys())
        # print("coords:", coords)
        values = self.db.unique_values(*coords, remapping=remapping).values()

        dic = {k: v for k, v in zip(keys, values)}
        return dic

    def filter(self, filter):
        if filter.is_empty:
            return self
        db = self.db.filter(filter)
        return self.__class__(db=db)

    def sel(self, *args, remapping=None, **kwargs):
        kwargs = normalize_selection(*args, **kwargs)
        if DATETIME in kwargs and kwargs[DATETIME] is not None:
            kwargs = _normalize_grib_kwargs_values(**kwargs)

        if not kwargs:
            return self
        return self.filter(SqlSelection(kwargs, remapping))

    def order_by(self, *args, remapping=None, **kwargs):
        kwargs = normalize_order_by(*args, **kwargs)

        out = self

        if remapping is not None:
            out = out.filter(SqlRemapping(remapping=remapping))

        if kwargs:
            out = out.filter(SqlOrder(kwargs))

        return out

    def part(self, n):
        if self._cache is None or not (self._cache.first <= n < self._cache.first + self._cache.length):
            first = (n // self.DB_CACHE_SIZE) * self.DB_CACHE_SIZE
            result = self.db.lookup_parts(limit=self.DB_CACHE_SIZE, offset=first)
            self._cache = SqlResultCache(first, len(result), result)
        return self._cache.result[n % self.DB_CACHE_SIZE]

    def get_metadata(self, n):
        assert "Used only in virtual"
        if self._dict_cache is None or not (
            self._dict_cache.first <= n < self._dict_cache.first + self._dict_cache.length
        ):
            first = (n // self.DB_DICT_CACHE_SIZE) * self.DB_DICT_CACHE_SIZE
            result = self.db.lookup_dicts(
                limit=self.DB_DICT_CACHE_SIZE,
                offset=first,
                with_parts=False,
                # remove_none=False ?
            )
            result = list(result)

            self._dict_cache = SqlResultCache(first, len(result), result)
        return self._dict_cache.result[n % self.DB_DICT_CACHE_SIZE]

    @cached_method
    def number_of_parts(self):
        return self.db.count()


register_serialisation(
    FieldListInFilesWithSqlIndex,
    lambda x: [x.db.db_path, x.db._filters],
    lambda x: FieldListInFilesWithSqlIndex(db=SqlDatabase(x[0])).apply_filters(filters=x[1]),
)
