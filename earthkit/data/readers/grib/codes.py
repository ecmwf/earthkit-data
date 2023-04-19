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
import os
import threading
import time

import eccodes
import numpy as np

from earthkit.data.core import Base
from earthkit.data.utils.bbox import BoundingBox

LOG = logging.getLogger(__name__)


GRIB_NAMESPACES = (
    None,
    "ls",
    "geography",
    "mars",
    "parameter",
    "statistics",
    "time",
    "vertical",
)


def missing_is_none(x):
    return None if x == 2147483647 else x


# This does not belong here, should be in the C library
def get_messages_positions(path):

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


class CodesHandle(eccodes.Message):
    MISSING_VALUE = np.finfo(np.float32).max
    KEY_TYPES = {"s": str, "l": int, "d": float}

    def __init__(self, handle, path, offset):
        super().__init__(handle)
        self.path = path
        self.offset = offset

    # TODO: just a wrapper around the base class implementation to handle the
    # s,l,d qualifiers. Once these are implemented in the base class this method can
    # be removed. md5GridSection is also handled!
    def get(self, name, default=None, ktype=None):

        if name == "values":
            return self.get_values()
        elif name == "md5GridSection":
            return self.get_md5GridSection()

        if ktype is None:
            name_part, _, key_type_str = name.partition(":")
            if key_type_str in CodesHandle.KEY_TYPES:
                return super().get(
                    name_part,
                    default=default,
                    ktype=CodesHandle.KEY_TYPES[key_type_str],
                )

        return super().get(name, default=default, ktype=ktype)

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

    def get_string(self, name):
        return self.get(name, ktype=str)

    def get_long(self, name):
        return self.get(name, ktype=int)

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
        }
        for key in self.keys(namespace=namespace):
            if key not in ignore:
                r[key] = self.get(param if key == "param" else key)
        return r

    # TODO: once missing value handling is implemented in the base class this method
    # can be removed
    def get_values(self):
        eccodes.codes_set(self._handle, "missingValue", CodesHandle.MISSING_VALUE)
        vals = eccodes.codes_get_values(self._handle)
        if self.get_long("bitmapPresent"):
            vals[vals == CodesHandle.MISSING_VALUE] = np.nan
        return vals

    def get_latitudes(self):
        return self.get("latitudes")

    def get_longitudes(self):
        return self.get("longitudes")

    def get_data_points(self):
        return eccodes.codes_grib_get_data(self._handle)

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

    def __getitem__(self, path):
        with self.lock:
            try:
                return super().__getitem__(path)
            except KeyError:
                pass

            c = self[path] = CodesReader(path)
            while len(self) >= self.size:
                oldest = min((v.last, v.path) for v in self.values())
                del self[oldest[1]]

            return c


cache = ReaderLRUCache(512)  # TODO: Add to config


class CodesReader:
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
        return cache[path]

    def at_offset(self, offset):
        with self.lock:
            self.last = time.time()
            self.file.seek(offset, 0)
            handle = eccodes.codes_new_from_file(
                self.file,
                eccodes.CODES_PRODUCT_GRIB,
            )
            assert handle is not None
            return CodesHandle(handle, self.path, offset)


class GribField(Base):
    def __init__(self, path, offset, length):
        self.path = path
        self._offset = offset
        self._length = length
        self._handle = None

    # def __enter__(self):
    #     return self

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     pass

    @property
    def handle(self):
        if self._handle is None:
            assert self._offset is not None
            self._handle = CodesReader.from_cache(self.path).at_offset(self._offset)
        return self._handle

    @property
    def values(self):
        return self.handle.get_values()

    @property
    def offset(self):
        if self._offset is None:
            self._offset = int(self.handle.get("offset"))
        return self._offset

    @property
    def shape(self):
        Nj = missing_is_none(self.handle.get("Nj"))
        Ni = missing_is_none(self.handle.get("Ni"))
        if Ni is None or Nj is None:
            return self.handle.get("numberOfDataPoints")
        return (Nj, Ni)

    def data(self, *args, flatten=False):
        keys = dict(
            lat=self.handle.get_latitudes,
            lon=self.handle.get_longitudes,
            value=self.handle.get_values,
        )
        for k in args:
            if k not in keys:
                raise ValueError(f"data: invalid argument: {k}")

        arg_keys = args if args else ("lat", "lon", "value")
        r = [keys[k]() for k in arg_keys]
        if not flatten:
            shape = self.shape
            r = [x.reshape(shape) for x in r]
        return r[0] if len(r) == 1 else tuple(r)

    def to_numpy(self, flatten=False):
        return self.values if flatten else self.values.reshape(self.shape)

    def to_points(self, flatten=True):
        lon, lat = self.data("lon", "lat", flatten=flatten)
        return dict(lon=lon, lat=lat)

    def __repr__(self):
        return "GribField(%s,%s,%s,%s,%s,%s)" % (
            self.handle.get("shortName"),
            self.handle.get("levelist"),
            self.handle.get("date"),
            self.handle.get("time"),
            self.handle.get("step"),
            self.handle.get("number"),
        )

    def datetime(self, **kwargs):
        return {
            "base_time": self._base_datetime(),
            "valid_time": self._valid_datetime(),
        }

    def _base_datetime(self):
        date = self.handle.get("date")
        time = self.handle.get("time")
        return datetime.datetime(
            date // 10000,
            date % 10000 // 100,
            date % 100,
            time // 100,
            time % 100,
        )

    def _valid_datetime(self):
        step = self.handle.get("endStep")
        return self._base_datetime() + datetime.timedelta(hours=step)

    def proj_string(self):
        return self.proj_target_string()

    def proj_source_string(self):
        return self.handle.get("projSourceString")

    def proj_target_string(self):
        return self.handle.get("projTargetString")

    def bounding_box(self):
        return BoundingBox(
            north=self.handle.get("latitudeOfFirstGridPointInDegrees"),
            south=self.handle.get("latitudeOfLastGridPointInDegrees"),
            west=self.handle.get("longitudeOfFirstGridPointInDegrees"),
            east=self.handle.get("longitudeOfLastGridPointInDegrees"),
        )

    def _attributes(self, names):
        result = {}
        for name in names:
            result[name] = self.handle.get(name)
        return result

    def _get(self, name):
        """Private, for testing only"""
        # paramId is renamed as param to get rid of the
        # additional '.128' (in earthkit/data/scripts/grib.py)
        if name == "param":
            name = "paramId"
        return self.handle.get(name)

    # TODO: move it into core or util
    @staticmethod
    def _parse_metadata_args(*args, namespace=None, astype=None):

        key = []
        for k in args:
            if isinstance(k, str):
                key.append(k)
            elif isinstance(k, (list, tuple)):
                key.extend(k)
            else:
                raise ValueError(f"metadata: invalid key argument={k}")

        if key:
            if namespace is not None:
                if not isinstance(namespace, str):
                    raise ValueError(
                        f"metadata: namespace={namespace} must be a str when key specified"
                    )

            if isinstance(astype, (list, tuple)):
                if len(astype) != len(key):
                    if len(astype) == 1:
                        astype = [astype[0]] * len(key)
                    else:
                        raise ValueError(
                            "metadata: astype must have the same number of items as key"
                        )
            else:
                astype = [astype] * len(key)

        if namespace is None:
            namespace = []
        elif isinstance(namespace, str):
            namespace = [namespace]

        return (key, namespace, astype)

    def metadata(self, *args, namespace=None, astype=None):
        def _key_name(key):
            if key == "param":
                key = "shortName"
            elif key == "_param_id":
                key = "paramId"
            return key

        key, namespace, astype = self._parse_metadata_args(
            *args, namespace=namespace, astype=astype
        )

        assert isinstance(key, list)
        assert isinstance(namespace, (list, tuple))

        if key:
            assert isinstance(astype, (list, tuple))
            if namespace:
                key = [namespace[0] + "." + k for k in key]

            r = [self.handle.get(_key_name(k), ktype=kt) for k, kt in zip(key, astype)]
            return tuple(r) if len(r) > 1 else r[0]
        else:
            if len(namespace) == 0:
                namespace = GRIB_NAMESPACES
            r = {ns: self.handle.as_namespace(ns) for ns in namespace}
            if len(r) == 1:
                return r[namespace[0]]
            else:
                if None in r:
                    r[""] = r.pop(None)
                return r

    def __getitem__(self, key):
        return self.metadata(key)

    def dump(self, namespace=None, **kwargs):
        from earthkit.data.utils.summary import format_info

        namespace = GRIB_NAMESPACES if namespace is None else [namespace]
        r = [
            {
                "title": ns if ns is not None else "default",
                "data": self.handle.as_namespace(ns),
                "tooltip": f"Keys in the ecCodes {ns} namespace",
            }
            for ns in namespace
        ]

        return format_info(
            r, selected="parameter", details=self.__class__.__name__, **kwargs
        )

    def write(self, f):
        """Write the message to a file object"""
        # assert isinstance(f, io.IOBase)
        self.handle.write_to(f)

    def message(self):
        """Return a buffer containing the encoded message"""
        return self.handle.get_buffer()
