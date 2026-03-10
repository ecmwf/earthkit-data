# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
import weakref
from abc import abstractmethod
from importlib import import_module

from earthkit.data.core import Encodable
from earthkit.data.core import FileLoaderMixin
from earthkit.data.core import Loader
from earthkit.data.core.config import CONFIG
from earthkit.data.decorators import detect_out_filename
from earthkit.data.decorators import locked

LOG = logging.getLogger(__name__)


class Reader(Loader, Encodable, os.PathLike):
    _format = None
    _binary = True
    _appendable = True

    def __init__(self, source, path, **kwargs):
        LOG.debug("Reader for %s is %s", path, self.__class__.__name__)
        self._source = weakref.ref(source)
        self.path = path
        self.source_filename = self.source.source_filename
        # self._binary = binary
        # self._appendable = appendable  # Set to True if the data can be appended to and existing file

    @property
    def source(self):
        return self._source()

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

    def cache_file(self, *args, **kwargs):
        return self.source.cache_file(*args, **kwargs)

    def to_target(self, target, *args, **kwargs):
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self, **kwargs)

    # def _default_encoder(self):
    #     return self._format

    # def _encode(self, encoder, *args, **kwargs):
    #     result = self._encode_path(encoder, *args, **kwargs)
    #     if result is not None:
    #         return result
    #     return self._default_encoder(encoder, *args, **kwargs)

    # def _encode_path(self, encoder, *args, **kwargs):
    #     path_info = self._path_info()
    #     if path_info is not None:
    #         target = kwargs.get("target", None)
    #         if target is not None and target._name == "file":
    #             path_info = self._path_info()
    #             return encoder._encode_path(path_info, **kwargs)
    #     return None

    # @abstractmethod
    # def _encode_default(self, encoder, *args, **kwargs):
    #     pass

    def __fspath__(self):
        return self.path

    def to_data_object(self):
        return None

    def _default_encoder(self):
        return self._format

    def _encode(self, encoder, hints=None, **kwargs):
        print("Reader._encode", encoder, kwargs)
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
        print("Reader._encode_path", path_info, encoder, target, kwargs)
        if path_info is not None:
            print("target", target)
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


class Reader1(Loader, os.PathLike):
    _format = None
    _binary = True
    _appendable = True

    def __init__(self, source, path, **kwargs):
        LOG.debug("Reader for %s is %s", path, self.__class__.__name__)
        self._source = weakref.ref(source)
        self.path = path
        self.source_filename = self.source.source_filename
        # self._binary = binary
        # self._appendable = appendable  # Set to True if the data can be appended to and existing file

    @property
    def source(self):
        return self._source()

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

    def cache_file(self, *args, **kwargs):
        return self.source.cache_file(*args, **kwargs)

    def _default_encoder(self):
        return self._format

    def _encode(self, encoder, *args, **kwargs):
        result = self._encode_path(encoder, *args, **kwargs)
        if result is not None:
            return result
        return self._default_encoder(encoder, *args, **kwargs)

    def _encode_path(self, encoder, *args, **kwargs):
        path_info = self._path_info()
        if path_info is not None:
            target = kwargs.get("target", None)
            if target is not None and target._name == "file":
                path_info = self._path_info()
                return encoder._encode_path(path_info, **kwargs)
        return None

    @abstractmethod
    def _encode_default(self, encoder, *args, **kwargs):
        pass

    def __fspath__(self):
        return self.path

    def to_data_object(self):
        return None

    def path_info(self):
        return PathInfo(
            self.path,
            binary=self.binary,
            appendable=self.appendable,
            default_encoder=self._default_encoder(),
        )


_READERS = {}


# TODO: Add plugins
@locked
def _readers(method_name):
    if not _READERS:
        here = os.path.dirname(__file__)
        for path in sorted(os.listdir(here)):
            if path[0] in ("_", "."):
                continue

            if path.endswith(".py") or os.path.isdir(os.path.join(here, path)):
                name, _ = os.path.splitext(path)
                try:
                    for method in ["reader", "memory_reader", "stream_reader"]:
                        module = import_module(f".{name}", package=__name__)
                        if hasattr(module, method):
                            _READERS[(name, method)] = getattr(module, method)
                            if hasattr(module, "aliases"):
                                for a in module.aliases:
                                    assert a not in _READERS
                                    _READERS[(a, method_name)] = getattr(module, method)
                except Exception:
                    LOG.exception("Error loading reader %s", name)

    return {k[0]: v for k, v in _READERS.items() if k[1] == method_name}


def _find_reader(method_name, source, path_or_data, **kwargs):
    """Helper function to create a reader.

    Tries all the registered methods stored in _READERS.
    """
    for deeper_check in (False, True):
        # We do two passes, the second one
        # allow the plugin to look deeper in the buffer
        for name, r in _readers(method_name).items():
            reader = r(source, path_or_data, deeper_check=deeper_check, **kwargs)
            if reader is not None:
                return reader.mutate()

    return _unknown(method_name, source, path_or_data, **kwargs)


def _unknown(method_name, source, path_or_data, **kwargs):
    from .unknown import UnknownMemoryReader
    from .unknown import UnknownReader
    from .unknown import UnknownStreamReader

    unknowns = {
        "reader": UnknownReader,
        "stream_reader": UnknownStreamReader,
        "memory_reader": UnknownMemoryReader,
    }
    return unknowns[method_name](source, path_or_data, **kwargs)


def _non_existing(source, path, **kwargs):
    if hasattr(source, "empty_reader"):
        return source.empty_reader(path, **kwargs)


def _empty(source, path, **kwargs):
    if hasattr(source, "empty_reader"):
        return source.empty_reader(path, **kwargs)


def reader(source, path, **kwargs):
    """Create the reader for a file/directory specified by path"""
    assert isinstance(path, str), source

    if hasattr(source, "reader"):
        reader = source.reader
        LOG.debug("Looking for a reader for %s (%s)", path, reader)
        if callable(reader):
            return reader(source, path)
        if isinstance(reader, str):
            return _readers()[reader.replace("-", "_")](source, path, magic=None, deeper_check=False)

        raise TypeError("Provided reader must be a callable or a string, not %s" % type(reader))

    if not os.path.exists(path):
        r = _non_existing(source, path, **kwargs)
        if r is not None:
            return r
        raise FileNotFoundError(f"No such file exists: '{path}'")

    LOG.debug("Reader for %s", path)

    if os.path.isdir(path):
        magic = None
    else:
        if os.path.getsize(path) == 0:
            r = _empty(source, path, **kwargs)
            if r is not None:
                return r
            raise Exception(f"File is empty: '{path}'")

        n_bytes = CONFIG.get("reader-type-check-bytes")
        with open(path, "rb") as f:
            magic = f.read(n_bytes)

    LOG.debug("Looking for a reader for %s (%s)", path, magic)

    return _find_reader(
        "reader",
        source,
        path,
        magic=magic,
        **kwargs,
    )


def memory_reader(source, buffer, **kwargs):
    """Create a reader for data held in a memory buffer"""
    assert isinstance(buffer, (bytes, bytearray)), source
    n_bytes = CONFIG.get("reader-type-check-bytes")
    magic = buffer[: min(n_bytes, len(buffer) - 1)]

    return _find_reader("memory_reader", source, buffer, magic=magic, **kwargs)


def stream_reader(source, stream, memory, **kwargs):
    """Create a reader for a stream"""
    magic = None
    if hasattr(stream, "peek") and callable(stream.peek):
        try:
            n_bytes = CONFIG.get("reader-type-check-bytes")
            magic = stream.peek(n_bytes)
            if len(magic) > n_bytes:
                magic = magic[:n_bytes]
        except Exception:
            pass

    return _find_reader(
        "stream_reader",
        source,
        stream,
        magic=magic,
        memory=memory,
        **kwargs,
    )
