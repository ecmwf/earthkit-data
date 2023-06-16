# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

# import datetime
import logging
import os
import threading
import time

import eccodes
import numpy as np

# from earthkit.data.core import Base
# from earthkit.data.utils.bbox import BoundingBox
# from earthkit.data.utils.projections import Projection

LOG = logging.getLogger(__name__)


# This does not belong here, should be in the C library
def get_bufr_messages_positions(path):
    fd = os.open(path, os.O_RDONLY)
    try:

        def get(count):
            buf = os.read(fd, count)
            assert len(buf) == count
            return int.from_bytes(
                buf,
                byteorder="big",
                signed=False,
            )

        offset = 0
        while True:
            code = os.read(fd, 4)
            if len(code) < 4:
                break

            if code != b"BUFR":
                offset = os.lseek(fd, offset + 1, os.SEEK_SET)
                continue

            length = get(3)
            edition = get(1)

            if edition in [3, 4]:
                yield offset, length
                offset = os.lseek(fd, offset + length, os.SEEK_SET)

    finally:
        os.close(fd)


# This does not belong here, should be in the C library
def get_grib_messages_positions(path):
    fd = os.open(path, os.O_RDONLY)
    try:

        def get(count):
            buf = os.read(fd, count)
            assert len(buf) == count
            return int.from_bytes(
                buf,
                byteorder="big",
                signed=False,
            )

        offset = 0
        while True:
            code = os.read(fd, 4)
            if len(code) < 4:
                break

            if code != b"GRIB":
                offset = os.lseek(fd, offset + 1, os.SEEK_SET)
                continue

            length = get(3)
            edition = get(1)

            if edition == 1:
                if length & 0x800000:
                    sec1len = get(3)
                    os.lseek(fd, 4, os.SEEK_CUR)
                    flags = get(1)
                    os.lseek(fd, sec1len - 8, os.SEEK_CUR)

                    if flags & (1 << 7):
                        sec2len = get(3)
                        os.lseek(fd, sec2len - 3, os.SEEK_CUR)

                    if flags & (1 << 6):
                        sec3len = get(3)
                        os.lseek(fd, sec3len - 3, os.SEEK_CUR)

                    sec4len = get(3)

                    if sec4len < 120:
                        length &= 0x7FFFFF
                        length *= 120
                        length -= sec4len
                        length += 4

            if edition == 2:
                length = get(8)

            yield offset, length
            offset = os.lseek(fd, offset + length, os.SEEK_SET)

    finally:
        os.close(fd)


# For some reason, cffi can ge stuck in the GC if that function
# needs to be called defined for the first time in a GC thread.
try:
    _h = eccodes.codes_new_from_samples(
        "regular_ll_pl_grib1", eccodes.CODES_PRODUCT_GRIB
    )
    eccodes.codes_release(_h)
except Exception:
    pass


class CodesHandle(eccodes.Message):
    MISSING_VALUE = np.finfo(np.float32).max
    KEY_TYPES = {"s": str, "l": int, "d": float}
    PRODUCT_ID = None

    def __init__(self, handle, path, offset):
        super().__init__(handle)
        self.path = path
        self.offset = offset

    @classmethod
    def from_sample(cls, name):
        return cls(eccodes.codes_new_from_samples(name, cls.PRODUCT_ID), None, None)

    # TODO: just a wrapper around the base class implementation to handle the
    # s,l,d qualifiers. Once these are implemented in the base class this method can
    # be removed. md5GridSection is also handled!
    def get(self, name, ktype=None, **kwargs):
        # if name == "values":
        #     return self.get_values()
        # elif name == "md5GridSection":
        #     return self.get_md5GridSection()

        # if ktype is None:
        #     name, _, key_type_str = name.partition(":")
        #     if key_type_str in CodesHandle.KEY_TYPES:
        #         ktype = CodesHandle.KEY_TYPES[key_type_str]

        if "default" in kwargs:
            return super().get(name, ktype=ktype, **kwargs)
        else:
            # this will throw if name is not available
            return super()._get(name, ktype=ktype)

    def get_string(self, name):
        return self.get(name, ktype=str)

    def get_long(self, name):
        return self.get(name, ktype=int)

    def clone(self):
        return CodesHandle(eccodes.codes_clone(self._handle), None, None)

    def set_multiple(self, values):
        assert self.path is None, "Only cloned handles can have values changed"
        eccodes.codes_set_key_vals(self._handle, values)

    def set_long(self, name, value):
        try:
            assert self.path is None, "Only cloned handles can have values changed"
            eccodes.codes_set_long(self._handle, name, value)
        except Exception as e:
            LOG.error("Error setting %s=%s", name, value)
            LOG.exception(e)

    def set_double(self, name, value):
        try:
            assert self.path is None, "Only cloned handles can have values changed"
            eccodes.codes_set_double(self._handle, name, value)
        except Exception as e:
            LOG.error("Error setting %s=%s", name, value)
            LOG.exception(e)

    def set_string(self, name, value):
        try:
            assert self.path is None, "Only cloned handles can have values changed"
            eccodes.codes_set_string(self._handle, name, value)
        except Exception as e:
            LOG.error("Error setting %s=%s", name, value)
            LOG.exception(e)

    def set(self, name, value):
        try:
            assert self.path is None, "Only cloned handles can have values changed"

            if isinstance(value, list):
                return eccodes.codes_set_array(self._handle, name, value)

            return eccodes.codes_set(self._handle, name, value)
        except Exception as e:
            LOG.error("Error setting %s=%s", name, value)
            LOG.exception(e)

    def write(self, f):
        eccodes.codes_write(self._handle, f)

    def save(self, path):
        with open(path, "wb") as f:
            self.write_to(f)
            self.path = path
            self.offset = 0

    def read_bytes(self, offset, length):
        if self.path is not None:
            with open(self.path, "rb") as f:
                f.seek(offset)
                return f.read(length)


class ReaderLRUCache(dict):
    def __init__(self, size):
        self.readers = dict()
        self.lock = threading.Lock()
        self.size = size

    def __getitem__(self, path_and_cls):
        path = path_and_cls[0]
        cls = path_and_cls[1]
        key = (path, os.getpid())
        with self.lock:
            try:
                return super().__getitem__(key)
            except KeyError:
                pass

            c = self[key] = cls(path)
            while len(self) >= self.size:
                _, oldest = min((v.last, k) for k, v in self.items())
                del self[oldest]

            return c


cache = ReaderLRUCache(32)  # TODO: Add to config


class CodesReader:
    PRODUCT_ID = None
    HANDLE_TYPE = None

    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        # print("OPEN", self.path)
        self.file = open(self.path, "rb")
        self.last = time.time()

    def __del__(self):
        try:
            # print("CLOSE", self.path)
            self.file.close()
        except Exception:
            pass

    @classmethod
    def from_cache(cls, path):
        return cache[(path, cls)]

    def at_offset(self, offset):
        with self.lock:
            self.last = time.time()
            self.file.seek(offset, 0)
            handle = eccodes.codes_new_from_file(
                self.file,
                self.PRODUCT_ID,
            )
            assert handle is not None
            return self.HANDLE_TYPE(handle, self.path, offset)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path}"
