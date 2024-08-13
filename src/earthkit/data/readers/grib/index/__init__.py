# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import math
import os
from abc import abstractmethod
from collections import defaultdict

from earthkit.data.core.fieldlist import FieldList
from earthkit.data.core.index import MaskIndex
from earthkit.data.core.index import MultiIndex
from earthkit.data.decorators import alias_argument
from earthkit.data.decorators import detect_out_filename
from earthkit.data.indexing.database import FILEPARTS_KEY_NAMES
from earthkit.data.indexing.database import MORE_KEY_NAMES
from earthkit.data.indexing.database import MORE_KEY_NAMES_WITH_UNDERSCORE
from earthkit.data.indexing.database import STATISTICS_KEY_NAMES
from earthkit.data.readers.grib.codes import GribField
from earthkit.data.readers.grib.pandas import PandasMixIn
from earthkit.data.readers.grib.xarray import XarrayMixIn
from earthkit.data.utils.availability import Availability
from earthkit.data.utils.progbar import progress_bar

LOG = logging.getLogger(__name__)


class GribFieldList(PandasMixIn, XarrayMixIn, FieldList):
    r"""Represents a list of :obj:`GribField <data.readers.grib.codes.GribField>`\ s.

    We can **iterate** through the fields as follows:

    >>> import earthkit.data
    >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")
    >>> len(ds)
    6
    >>> for f in ds:
    ...     print(f)
    ...
    GribField(t,1000,20180801,1200,0,0)
    GribField(u,1000,20180801,1200,0,0)
    GribField(v,1000,20180801,1200,0,0)
    GribField(t,850,20180801,1200,0,0)
    GribField(u,850,20180801,1200,0,0)
    GribField(v,850,20180801,1200,0,0)

    :obj:`Fieldset` objects can be **concatenated** with the + operator:

    >>> import earthkit.data
    >>> ds1 = earthkit.data.from_source("file", "docs/examples/test.grib")
    >>> len(ds1)
    2
    >>> ds2 = earthkit.data.from_source("file", "docs/examples/test6.grib")
    >>> len(ds2)
    6
    >>> ds = ds1 + ds2
    >>> len(ds)
    8

    Standard Python slicing works:

    >>> import earthkit.data
    >>> ds = earthkit.data.from_source("file", "docs/examples/test6.grib")
    >>> len(ds)
    6
    >>> ds[0]
    GribField(t,1000,20180801,1200,0,0)
    >>> for f in ds[0:3]:
    ...     print(f)
    GribField(t,1000,20180801,1200,0,0)
    GribField(u,1000,20180801,1200,0,0)
    GribField(v,1000,20180801,1200,0,0)
    >>> for f in ds[0:4:2]:
    ...     print(f)
    GribField(t,1000,20180801,1200,0,0)
    GribField(v,1000,20180801,1200,0,0)
    >>> ds[-1]
    GribField(v,850,20180801,1200,0,0)
    >>> for f in ds[-2:]:
    ...     print(f)
    GribField(u,850,20180801,1200,0,0)
    GribField(v,850,20180801,1200,0,0)

    Slicing also works with a list or an ndarray:

    >>> for f in ds[[1, 3]]:
    ...     print(f)
    ...
    GribField(u,1000,20180801,1200,0,0)
    GribField(t,850,20180801,1200,0,0)
    >>> for f in ds[np.array([1, 3])]:
    ...     print(f)
    ...
    GribField(u,1000,20180801,1200,0,0)
    GribField(t,850,20180801,1200,0,0)

    """

    _availability = None

    def __init__(self, *args, **kwargs):
        if self.availability_path is not None and os.path.exists(self.availability_path):
            self._availability = Availability(self.availability_path)

        # Index.__init__(self, *args, **kwargs)
        FieldList.__init__(self, *args, **kwargs)

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        return GribMaskFieldList(*args, **kwargs)

    @property
    def availability_path(self):
        return None

    @classmethod
    def merge(cls, sources):
        if not all(isinstance(_, GribFieldList) for _ in sources):
            raise ValueError("GribFieldList can only be merged to another GribFieldLists")
        if not all(s.array_backend is s[0].array_backend for s in sources):
            raise ValueError("Only fieldlists with the same array backend can be merged")

        return GribMultiFieldList(sources)

    def _custom_availability(self, ignore_keys=None, filter_keys=lambda k: True):
        def dicts():
            for i in progress_bar(iterable=range(len(self)), desc="Building availability"):
                dic = self.get_metadata(i)

                for k in list(dic.keys()):
                    if not filter_keys(k):
                        dic.pop(k)
                        continue
                    if ignore_keys and k in ignore_keys:
                        dic.pop(k)
                        continue
                    if dic[k] is None:
                        dic.pop(k)
                        continue

                yield dic

        from earthkit.data.utils.availability import Availability

        return Availability(dicts())

    @property
    def availability(self):
        if self._availability is not None:
            return self._availability
        LOG.debug("Building availability")

        self._availability = self._custom_availability(
            ignore_keys=FILEPARTS_KEY_NAMES
            + STATISTICS_KEY_NAMES
            + MORE_KEY_NAMES_WITH_UNDERSCORE
            + MORE_KEY_NAMES
        )
        return self.availability

    def _is_full_hypercube(self):
        non_empty_coords = {k: v for k, v in self.availability._tree.unique_values().items() if len(v) > 1}
        expected_size = math.prod([len(v) for k, v in non_empty_coords.items()])
        return len(self) == expected_size

    @alias_argument("levelist", ["level", "levellist"])
    @alias_argument("levtype", ["leveltype"])
    @alias_argument("param", ["variable", "parameter"])
    @alias_argument("number", ["realization", "realisation"])
    @alias_argument("class", "klass")
    def _normalize_kwargs_names(self, **kwargs):
        return kwargs

    @detect_out_filename
    def save(self, filename, append=False, bits_per_value=None):
        r"""Write all the fields into a file.

        Parameters
        ----------
        filename: str
            The target file path.
        append: bool
            When it is true append data to the target file. Otherwise
            the target file be overwritten if already exists.
        bits_per_value: int or None
            Set the ``bitsPerValue`` GRIB key for each message in the generated
            output. When None the ``bitsPerValue`` stored in the message metadata
            will be used.

        See Also
        --------
        write

        """
        super().save(
            filename,
            append=append,
            bits_per_value=bits_per_value,
        )


class GribMaskFieldList(GribFieldList, MaskIndex):
    def __init__(self, *args, **kwargs):
        MaskIndex.__init__(self, *args, **kwargs)
        FieldList._init_from_mask(self, self)


class GribMultiFieldList(GribFieldList, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)
        FieldList._init_from_multi(self, self)


class GribCache:
    def __init__(self, owner, store_grib_fields_in_memory, grib_handle_cache_size, use_grib_metadata_cache):
        from earthkit.data.core.settings import SETTINGS

        grib_field_cache = (
            store_grib_fields_in_memory
            if store_grib_fields_in_memory is not None
            else SETTINGS.get("store-grib-fields-in-memory")
        )
        grib_handle_cache_size = (
            grib_handle_cache_size
            if grib_handle_cache_size is not None
            else SETTINGS.get("grib-handle-cache-size")
        )
        self.use_metadata_cache = (
            use_grib_metadata_cache
            if use_grib_metadata_cache is not None
            else SETTINGS.get("use-grib-metadata-cache")
        )

        self.field_cache = None
        if grib_field_cache:
            from lru import LRU

            # TODO: the number of fields might only be available only later (e.g. fieldlists with
            # an SQL index). Consider making _field_cache a cached property.
            n = len(owner)
            if n > 0:
                self.field_cache = LRU(n)

        self.handle_cache = None
        if grib_handle_cache_size > 0:
            from lru import LRU

            self.handle_cache = LRU(grib_handle_cache_size)

        self.handle_create_count = 0
        self.field_create_count = 0

    @property
    def use_temporary_handle(self):
        return self.handle_cache is None and self.field_cache is not None

    def field(self, n, create=None):
        if self.field_cache is not None:
            if n in self.field_cache:
                return self.field_cache[n]
            elif callable(create):
                field = create(n)
                self.field_cache[n] = field
                self.field_create_count += 1
                return field

    def handle(self, field, create=None):
        if self.handle_cache is not None:
            key = (field.path, field._offset)
            if key in self.handle_cache:
                return self.handle_cache[key]
            elif callable(create):
                handle = create()
                self.handle_create_count += 1
                self.handle_cache[key] = handle
                return handle

    def diag(self):
        r = defaultdict(int)
        if self.field_cache is not None:
            r["field_cache_size"] = len(self.field_cache)
            r["field_cache_create_count"] = self.field_create_count

        if self.handle_cache is not None:
            r["handle_cache_size"] = len(self.handle_cache)
            r["handle_cache_create_count"] = self.handle_create_count

        return r


class GribFieldListInFiles(GribFieldList):
    def __init__(
        self, *args, grib_field_cache=None, grib_handle_cache_size=None, grib_metadata_cache=None, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self._caches = GribCache(self, grib_field_cache, grib_handle_cache_size, grib_metadata_cache)

    def _create_field(self, n):
        part = self.part(n)
        return GribField(
            part.path,
            part.offset,
            part.length,
            self.array_backend,
            cache=self._caches,
        )

    def _getitem(self, n):
        # TODO: check if we need a mutex here
        if isinstance(n, int):
            if n < 0:
                n += len(self)

            field = self._caches.field(n, create=self._create_field)
            if field is not None:
                return field
            else:
                return self._create_field(n)

    def __len__(self):
        return self.number_of_parts()

    def _diag(self):
        r = defaultdict(int)
        r.update(self._caches.diag())

        for f in self:
            if f._handle is not None:
                r["handle_count"] += 1

            try:
                md_cache = f._metadata.get.cache_info()
                r["metadata_cache_hits"] += md_cache.hits
                r["metadata_cache_misses"] += md_cache.misses
                r["metadata_cache_size"] += md_cache.currsize
            except Exception:
                pass

        return r

    @abstractmethod
    def part(self, n):
        self._not_implemented()

    @abstractmethod
    def number_of_parts(self):
        self._not_implemented()
