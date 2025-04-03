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
import threading
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

# from earthkit.data.utils.progbar import progress_bar

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
        return GribMultiFieldList(sources)

    def _custom_availability(self, ignore_keys=None, filter_keys=lambda k: True):
        from earthkit.data.utils.progbar import progress_bar

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

    def __getstate__(self):
        r = {}
        r["mask_index"] = self._index
        r["mask_indices"] = self._indices
        return r

    def __setstate__(self, state):
        _index = state["mask_index"]
        _indices = state["mask_indices"]
        self.__init__(_index, _indices)


class GribMultiFieldList(GribFieldList, MultiIndex):
    def __init__(self, *args, **kwargs):
        MultiIndex.__init__(self, *args, **kwargs)
        FieldList._init_from_multi(self, self)

    def __getstate__(self):
        r = {}
        r["multi_indexes"] = self._indexes
        r["kwargs"] = self._kwargs
        return r

    def __setstate__(self, state):
        self.__init__(
            state["multi_indexes"],
            **state["kwargs"],
        )


class GribFieldManager:
    def __init__(self, policy, owner):
        self.policy = policy
        self.cache = None
        self.lock = threading.Lock()

        if self.policy == "persistent":
            from lru import LRU

            # TODO: the number of fields might only be available only later (e.g. fieldlists with
            # an SQL index). Consider making cache a cached property.
            n = len(owner)
            if n > 0:
                self.cache = LRU(n)

        self.field_create_count = 0

        # check consistency
        if self.cache is not None:
            assert self.policy == "persistent"

    def field(self, n, create):
        if self.cache is not None:
            with self.lock:
                if n in self.cache:
                    return self.cache[n]
                else:
                    field = create(n)
                    self._field_created()
                    self.cache[n] = field
                    return field
        else:
            self._field_created()
            return create(n)

    def _field_created(self):
        self.field_create_count += 1

    def diag(self):
        r = defaultdict(int)
        r["grib_field_policy"] = self.policy
        if self.cache is not None:
            r["field_cache_size"] = len(self.cache)

        r["field_create_count"] = self.field_create_count
        return r


class GribHandleManager:
    # TODO: split into policies
    def __init__(self, policy, cache_size):
        self.policy = policy
        self.max_cache_size = cache_size
        self.cache = None
        self.lock = threading.Lock()

        if self.policy == "cache":
            if self.max_cache_size > 0:
                from lru import LRU

                self.cache = LRU(self.max_cache_size)
            else:
                raise ValueError(
                    'grib_handle_cache_size must be greater than 0 when grib_handle_policy="cache"'
                )

        self.handle_create_count = 0

        # check consistency
        if self.cache is not None:
            self.policy == "cache"
        else:
            self.policy in ["persistent", "temporary"]

    def handle(self, field, create):
        if self.policy == "cache":
            key = (field.path, field._offset)
            with self.lock:
                if key in self.cache:
                    return self.cache[key]
                else:
                    handle = create()
                    self._handle_created()
                    self.cache[key] = handle
                    return handle
        elif self.policy == "persistent":
            if field._handle is None:
                with self.lock:
                    if field._handle is None:
                        field._handle = create()
                        self._handle_created()
                    return field._handle
            return field._handle
        elif self.policy == "temporary":
            self._handle_created()
            return create()

    def _handle_created(self):
        self.handle_create_count += 1

    def diag(self):
        r = defaultdict(int)
        r["grib_handle_policy"] = self.policy
        r["grib_handle_cache_size"] = self.max_cache_size
        if self.cache is not None:
            r["handle_cache_size"] = len(self.cache)

        r["handle_create_count"] = self.handle_create_count
        return r


class GribFieldListInFiles(GribFieldList):
    def __init__(
        self,
        *args,
        grib_field_policy=None,
        grib_handle_policy=None,
        grib_handle_cache_size=None,
        use_grib_metadata_cache=None,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)

        from earthkit.data.core.config import CONFIG

        def _get_opt(v, name):
            return v if v is not None else CONFIG.get(name)

        self._field_manager = GribFieldManager(_get_opt(grib_field_policy, "grib-field-policy"), self)
        self._handle_manager = GribHandleManager(
            _get_opt(grib_handle_policy, "grib-handle-policy"),
            _get_opt(grib_handle_cache_size, "grib-handle-cache-size"),
        )

        self._use_metadata_cache = _get_opt(use_grib_metadata_cache, "use-grib-metadata-cache")

    def _create_field(self, n):
        part = self.part(n)
        field = GribField(
            part.path,
            part.offset,
            part.length,
            handle_manager=self._handle_manager,
            use_metadata_cache=self._use_metadata_cache,
        )
        if field is None:
            raise RuntimeError(f"Could not get a handle for part={part}")
        return field

    def _getitem(self, n):
        if isinstance(n, int):
            if n < 0:
                n += len(self)
            if n >= len(self):
                raise IndexError(f"Index {n} out of range")

            return self._field_manager.field(n, self._create_field)

    def __len__(self):
        return self.number_of_parts()

    def _cache_diag(self):
        """For testing only"""
        r = defaultdict(int)
        r.update(self._field_manager.diag())
        r.update(self._handle_manager.diag())

        if self._field_manager.cache is not None:
            from earthkit.data.utils.diag import collect_field_metadata_cache_diag

            for f in self._field_manager.cache.values():
                if f._handle is not None:
                    r["current_handle_count"] += 1

                if self._use_metadata_cache:
                    collect_field_metadata_cache_diag(f, r)
        return r

    @abstractmethod
    def part(self, n):
        self._not_implemented()

    @abstractmethod
    def number_of_parts(self):
        self._not_implemented()
