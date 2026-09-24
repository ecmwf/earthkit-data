# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import functools
import logging
import os
import weakref
from abc import abstractmethod

from earthkit.data.core import Encodable, Loader
from earthkit.data.core.config import CONFIG
from earthkit.data.decorators import detect_out_filename as detect_out_filename

LOG = logging.getLogger(__name__)


class Reader(Loader, Encodable, os.PathLike):
    _format = None
    _binary = True
    _appendable = True

    def __init__(self, source, path, **kwargs):
        LOG.debug("Reader for %s is %s", path, self.__class__.__name__)
        self._source = weakref.ref(source)
        self._path = path
        self.source_filename = self.source.source_filename

    @property
    def source(self):
        return self._source()

    @property
    def path(self):
        return self._path

    @path.setter
    def path(self, value):
        self._path = value

    @property
    def filter(self):
        return self.source.filter

    @property
    def parts(self):
        if hasattr(self.source, "parts"):
            return self.source.parts

    @property
    def stream(self):
        if hasattr(self.source, "stream"):
            return self.source.stream
        return False

    @property
    def merger(self):
        return self.source.merger

    @property
    def appendable(self):
        return self._appendable

    @property
    def binary(self):
        return self._binary

    def _cache_file(self, *args, **kwargs):
        return self.source._cache_file(*args, **kwargs)

    def to_target(self, target, *args, **kwargs):
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self, **kwargs)

    def __fspath__(self):
        return self.path

    def to_data_object(self):
        return None

    def _default_encoder(self):
        return self._format

    def _encode(self, encoder, hints=None, **kwargs):
        if hints and hints.get("path_allowed", False):
            result = self._encode_path(encoder, **kwargs)
            if result is not None:
                return result
        return self._encode_default(encoder, **kwargs)

    @abstractmethod
    def _encode_default(self, encoder, **kwargs):
        pass

    def _encode_path(self, encoder, *, target=None, **kwargs):
        path_info = self._path_info()
        if path_info is not None:
            if target is not None and target._name == "file":
                path_info = self._path_info()
                return encoder._encode_path(path_info, target=target, **kwargs)
        return None

    def _path_info(self):
        if self.path and os.path.exists(self.path):
            from earthkit.data.utils.path_info import LoaderPathInfo

            return LoaderPathInfo(
                self.path,
                binary=self._binary,
                appendable=self._appendable,
                default_encoder=self._default_encoder(),
            )
        return None


@functools.cache
def _file_matchers():
    """Return the functions matching a file or directory to its reader, in the order they are tried.

    Each function checks whether the data is in its format and returns the object to use for
    it, otherwise None. The modules are imported on first use since they depend on this module.
    """
    from .bufr import match_bufr
    from .covjson import match_covjson
    from .csv import match_csv
    from .directory import match_directory
    from .geojson import match_geojson
    from .geotiff import match_geotiff
    from .grib import match_grib
    from .netcdf import match_netcdf
    from .numpy import match_numpy
    from .odb import match_odb
    from .pcraster import match_pcraster
    from .pp import match_pp
    from .shapefile import match_shapefile
    from .tar import match_tar
    from .text import match_text
    from .zarr import match_zarr
    from .zip import match_zip

    return [
        match_bufr,
        match_covjson,
        match_csv,
        match_directory,
        match_geojson,
        match_geotiff,
        match_grib,
        match_netcdf,
        match_numpy,
        match_odb,
        match_pcraster,
        match_pp,
        match_shapefile,
        match_tar,
        match_text,
        match_zarr,
        match_zip,
    ]


@functools.cache
def _memory_matchers():
    """Return the functions matching a memory buffer to its reader, in the order they are tried."""
    from .covjson import match_covjson_memory
    from .grib import match_grib_memory

    return [match_covjson_memory, match_grib_memory]


@functools.cache
def _stream_matchers():
    """Return the functions matching a stream to its reader, in the order they are tried."""
    from .covjson import match_covjson_stream
    from .grib import match_grib_stream

    return [match_covjson_stream, match_grib_stream]


def _match(matchers, source, data, **kwargs):
    """Return the object created by the first function in ``matchers`` matching ``data``, or None."""
    # The second pass allows the functions to look deeper into the data
    for deeper_check in (False, True):
        for match in matchers:
            found = match(source, data, deeper_check=deeper_check, **kwargs)
            if found is not None:
                return found.mutate()

    return None


def _non_existing(source, path, **kwargs):
    if hasattr(source, "empty_reader"):
        return source.empty_reader(path, **kwargs)
    raise FileNotFoundError(f"No such file exists: '{path}'")


def _empty(source, path, **kwargs):
    if hasattr(source, "empty_reader"):
        return source.empty_reader(path, **kwargs)
    from earthkit.data.utils.exceptions import EmptyFileError

    raise EmptyFileError(f"File is empty: '{path}'")


def match_file(source, path, **kwargs):
    """Return the object reading the file or directory at ``path``."""
    assert isinstance(path, str), source

    if not os.path.exists(path):
        return _non_existing(source, path, **kwargs)

    if os.path.isdir(path):
        magic = None
    else:
        if os.path.getsize(path) == 0:
            return _empty(source, path, **kwargs)

        n_bytes = CONFIG.get("reader-type-check-bytes")
        with open(path, "rb") as f:
            magic = f.read(n_bytes)

    LOG.debug("Looking for a reader for %s (%s)", path, magic)

    found = _match(_file_matchers(), source, path, magic=magic, **kwargs)
    if found is None:
        from .unknown import UnknownReader

        found = UnknownReader(source, path, magic=magic, **kwargs)
    return found


def match_memory(source, buffer, **kwargs):
    """Return the object reading the data held in a memory buffer."""
    assert isinstance(buffer, (bytes, bytearray)), source
    n_bytes = CONFIG.get("reader-type-check-bytes")
    magic = buffer[: min(n_bytes, len(buffer) - 1)]

    found = _match(_memory_matchers(), source, buffer, magic=magic, **kwargs)
    if found is None:
        from .unknown import UnknownMemoryReader

        found = UnknownMemoryReader(source, buffer, magic=magic, **kwargs)
    return found


def match_stream(source, stream, memory, **kwargs):
    """Return the object reading a stream."""
    magic = None
    if hasattr(stream, "peek") and callable(stream.peek):
        try:
            n_bytes = CONFIG.get("reader-type-check-bytes")
            magic = stream.peek(n_bytes)
            if len(magic) > n_bytes:
                magic = magic[:n_bytes]
        except Exception:
            pass

    found = _match(_stream_matchers(), source, stream, magic=magic, memory=memory, **kwargs)
    if found is None:
        from .unknown import UnknownStreamReader

        found = UnknownStreamReader(source, stream, magic=magic, memory=memory, **kwargs)
    return found
