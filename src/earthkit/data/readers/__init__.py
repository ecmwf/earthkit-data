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
from collections.abc import Callable
from dataclasses import dataclass
from importlib.metadata import entry_points

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


# Priority of the plugins not setting one
DEFAULT_PLUGIN_PRIORITY = 700

# The entry point group of the reader plugins
PLUGIN_GROUP = "earthkit.data.readers"


@dataclass(frozen=True)
class ReaderPlugin:
    """The functions matching each kind of input to a reader.

    Each function checks whether the data is in its format and returns the object to use
    for it, otherwise None. A kind of input without a function is not supported. A plugin
    is registered as an entry point in the ``earthkit.data.readers`` group, e.g.
    ``new-thing = "package.module:plugin"``, where ``plugin`` is a :class:`ReaderPlugin`.

    The readers are tried from the highest to the lowest ``priority``, and in alphabetical
    order of their names when the priorities are the same. The priorities used by the
    built-in readers are:

    - 900-999: core formats identified by magic bytes (e.g. GRIB, NetCDF)
    - 800-899: other formats identified by magic bytes or directory layout
    - 500-599: formats identified by file extension
    - 100-399: checks reading the file (archives, csv and text sniffing), text is last
    """

    file: Callable | None = None
    memory: Callable | None = None
    stream: Callable | None = None
    priority: int = DEFAULT_PLUGIN_PRIORITY


def _load_plugins():
    """Return the reader plugins registered in the entry point group, by name.

    A plugin failing to load is skipped.
    """
    plugins = {}
    for ep in entry_points(group=PLUGIN_GROUP):
        try:
            plugin = ep.load()
            if not isinstance(plugin, ReaderPlugin):
                raise TypeError(f"{ep.value} is not a ReaderPlugin")
            plugins[ep.name] = plugin
        except Exception:
            LOG.exception("Cannot load reader plugin '%s'", ep.name)
    return plugins


@functools.cache
def _readers():
    """Return the built-in readers and the plugins by name, in the order they are tried.

    A plugin with the name of a built-in reader is skipped. The dict is built once, so
    plugins installed later are only found after a restart.
    """
    # imported on first use since the modules depend on this one
    from . import (
        bufr,
        covjson,
        csv,
        directory,
        geojson,
        geotiff,
        grib,
        netcdf,
        numpy,
        odb,
        pcraster,
        pp,
        shapefile,
        tar,
        text,
        zarr,
        zip,
    )

    readers = {
        "bufr": bufr.plugin,
        "covjson": covjson.plugin,
        "csv": csv.plugin,
        "directory": directory.plugin,
        "geojson": geojson.plugin,
        "geotiff": geotiff.plugin,
        "grib": grib.plugin,
        "netcdf": netcdf.plugin,
        "numpy": numpy.plugin,
        "odb": odb.plugin,
        "pcraster": pcraster.plugin,
        "pp": pp.plugin,
        "shapefile": shapefile.plugin,
        "tar": tar.plugin,
        "text": text.plugin,
        "zarr": zarr.plugin,
        "zip": zip.plugin,
    }

    for name, plugin in _load_plugins().items():
        if name in readers:
            LOG.warning("Reader plugin '%s' has the name of a built-in reader, skipped", name)
        else:
            readers[name] = plugin

    return dict(sorted(readers.items(), key=lambda item: (-item[1].priority, item[0])))


def _match(kind, source, data, **kwargs):
    """Return the object created by the first reader matching the ``kind`` of ``data``, or None."""
    matchers = [m for m in (getattr(r, kind) for r in _readers().values()) if m is not None]
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

    found = _match("file", source, path, magic=magic, **kwargs)
    if found is None:
        from .unknown import UnknownReader

        found = UnknownReader(source, path, magic=magic, **kwargs)
    return found


def match_memory(source, buffer, **kwargs):
    """Return the object reading the data held in a memory buffer."""
    assert isinstance(buffer, (bytes, bytearray)), source
    n_bytes = CONFIG.get("reader-type-check-bytes")
    magic = buffer[: min(n_bytes, len(buffer) - 1)]

    found = _match("memory", source, buffer, magic=magic, **kwargs)
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

    found = _match("stream", source, stream, magic=magic, memory=memory, **kwargs)
    if found is None:
        from .unknown import UnknownStreamReader

        found = UnknownStreamReader(source, stream, magic=magic, memory=memory, **kwargs)
    return found
