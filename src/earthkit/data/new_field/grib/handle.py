# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import threading
from abc import ABCMeta
from abc import abstractmethod
from collections import defaultdict

import eccodes
import numpy as np

from earthkit.data.utils.message import CodesHandle
from earthkit.data.utils.message import CodesReader

LOG = logging.getLogger(__name__)


class GribCodesFloatArrayAccessor:
    HAS_FLOAT_SUPPORT = None
    KEY = None

    def __init__(self):
        if GribCodesFloatArrayAccessor.HAS_FLOAT_SUPPORT is None:
            GribCodesFloatArrayAccessor.HAS_FLOAT_SUPPORT = hasattr(eccodes, "codes_get_float_array")

    def get(self, handle, dtype=None):
        v = eccodes.codes_get_array(handle, self.KEY)
        if dtype is not None:
            return v.astype(dtype)
        else:
            return v


class GribCodesValueAccessor(GribCodesFloatArrayAccessor):
    KEY = "values"

    def __init__(self):
        super().__init__()

    def get(self, handle, dtype=None):
        if dtype is np.float32 and self.HAS_FLOAT_SUPPORT:
            return eccodes.codes_get_array(handle, self.KEY, ktype=dtype)
        else:
            return super().get(handle, dtype=dtype)


class GribCodesLatitudeAccessor(GribCodesFloatArrayAccessor):
    KEY = "latitudes"

    def __init__(self):
        super().__init__()


class GribCodesLongitudeAccessor(GribCodesFloatArrayAccessor):
    KEY = "longitudes"

    def __init__(self):
        super().__init__()


VALUE_ACCESSOR = GribCodesValueAccessor()
LATITUDE_ACCESSOR = GribCodesLatitudeAccessor()
LONGITUDE_ACCESSOR = GribCodesLongitudeAccessor()


class GribCodesHandle(CodesHandle):
    PRODUCT_ID = eccodes.CODES_PRODUCT_GRIB

    def get(self, name, ktype=None, **kwargs):
        if name == "values":
            return self.get_values()
        elif name == "md5GridSection":
            return self.get_md5GridSection()
        elif name == "gridSpec":
            # Temporary measure because from ecCodes 2.41.0, when we ask for the gridSpec
            # ecCodes raises a gribapi.errors.FunctionNotImplementedError exception, which is
            # not caught by the  high level eccodes API even if a default value is provided.
            if "default" in kwargs:
                try:
                    return super().get(name, ktype, **kwargs)
                except Exception as e:
                    if "FunctionNotImplementedError" in str(type(e)):
                        return kwargs.get("default", None)

        return super().get(name, ktype, **kwargs)

    def get_md5GridSection(self):
        # Special case because:
        #
        # 1) eccodes is returning size > 1 for 'md5GridSection'
        # (size = 16 : it is the number of bytes of the value)
        # This is already fixed in eccodes 2.27.1
        #
        # 2) sometimes (see below), the value for "shapeOfTheEarth" is inconsistent.
        # This impacts the (computed on-the-fly) value of "md5GridSection".
        # ----------------
        # Example of data with inconsistent values:
        # S2S data, origin='ecmf', param='tp', step='24', number='0', date=['20201203','20200702']
        # the 'md5GridSection' are different
        # This is because one has "shapeOfTheEarth" set to 0, the other to 6.
        # This is only impacting the metadata.
        # Since this has no impact on the data itself,
        # this is unlikely to be fixed. Therefore this hacky patch.
        #
        # Obviously, the patch causes an inconsistency between the value of md5GridSection
        # read by this code, and the value read by another code without this patch.

        save = eccodes.codes_get_long(self._handle, "shapeOfTheEarth")
        eccodes.codes_set_long(self._handle, "shapeOfTheEarth", 255)
        result = eccodes.codes_get_string(self._handle, "md5GridSection")
        eccodes.codes_set_long(self._handle, "shapeOfTheEarth", save)
        return result

    def as_namespace(self, namespace, param="shortName"):
        r = {}
        ignore = {
            "distinctLatitudes",
            "distinctLongitudes",
            "distinctLatitudes",
            "latLonValues",
            "latitudes",
            "longitudes",
            "values",
            "bitmap",
        }
        for key in self.keys(namespace=namespace):
            if key not in ignore:
                r[key] = self.get(param if key == "param" else key)
        return r

    # TODO: once missing value handling is implemented in the base class this method
    # can be removed
    def get_values(self, dtype=None):
        eccodes.codes_set(self._handle, "missingValue", CodesHandle.MISSING_VALUE)
        vals = VALUE_ACCESSOR.get(self._handle, dtype=dtype)
        if self.get_long("bitmapPresent"):
            vals[vals == CodesHandle.MISSING_VALUE] = np.nan
        return vals

    def get_latitudes(self, dtype=None):
        return LATITUDE_ACCESSOR.get(self._handle, dtype=dtype)

    def get_longitudes(self, dtype=None):
        return LONGITUDE_ACCESSOR.get(self._handle, dtype=dtype)

    def get_data_points(self):
        return eccodes.codes_grib_get_data(self._handle)

    def set_values(self, values):
        try:
            assert self.path is None, "Only cloned handles can have values changed"
            eccodes.codes_set_values(self._handle, values.flatten())
        except Exception as e:
            LOG.error("Error setting values")
            LOG.exception(e)
            raise


class GribCodesReader(CodesReader):
    PRODUCT_ID = eccodes.CODES_PRODUCT_GRIB
    HANDLE_TYPE = GribCodesHandle


class GribHandle(metaclass=ABCMeta):
    @property
    @abstractmethod
    def handle(self):
        pass

    @abstractmethod
    def release(self):
        pass

    def __contains__(self, key):
        return self.handle.__contains__(key)

    def __getattr__(self, name):
        """Delegate attribute access to the underlying handle."""
        return getattr(self.handle, name)

    def deflate(self):
        """Shrink the memory used by the handle."""
        return DeflatedGribHandle.from_handle(self.handle)


class FileGribHandle(GribHandle):
    _handle = None

    def __init__(self, path, offset, length):
        self.path = path
        self.offset = offset
        self.length = length

    @property
    def handle(self):
        if self._handle is None:
            self._handle = self._create_handle()
        return self._handle

    def _create_handle(self):
        return GribCodesReader.from_cache(self.path).at_offset(self.offset)

    def release(self):
        self._handle = None


class ManagedGribHandle(FileGribHandle):
    """A GribHandle that is managed by a handle manager."""

    def __init__(self, path, offset, length, manager):
        super().__init__(path, offset, length)
        self.manager = manager
        assert manager is not None, "handle_manager must be provided for ManagedGribHandle"

    @property
    def handle(self):
        handle = self.manager.handle(self, self._create_handle)
        if handle is None:
            raise RuntimeError(f"Could not get a handle for offset={self.offset} in {self.path}")
        return handle

    def release(self):
        self.manager.remove(self)


class MemoryGribHandle(GribHandle):
    def __init__(self, handle):
        self._handle = handle

    @classmethod
    def from_raw_handle(cls, handle):
        """Create a MemoryGribHandle from an existing handle."""
        return cls(GribCodesHandle(handle, None, None))

    @property
    def handle(self):
        return self._handle

    def release(self):
        self._handle = None


class DeflatedGribHandle(MemoryGribHandle):
    """A GribHandle that has been shrunk to only contain the headers."""

    def __init__(self, handle, bits_per_value=None):
        super().__init__(handle)
        self.bits_per_value = bits_per_value

    @classmethod
    def from_handle(cls, handle, bits_per_value=None):
        handle_new = handle.clone(headers_only=True)
        key = "bitsPerValue"
        if bits_per_value is None:
            bits_per_value = handle.get(key, default=None)
        return cls(handle_new, bits_per_value=bits_per_value)

    def deflate(self):
        """Deflate the handle to only contain the headers."""
        # This method is a no-op for ShrunkGribHandle as it is already shrunk.
        return self


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
            key = (field.path, field.offset)
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

    def remove(self, field):
        if self.policy == "cache":
            key = (field.path, field.offset)
            with self.lock:
                self.cache.pop(key, None)

        elif self.policy == "persistent":
            with self.lock:
                field._handle = None

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
