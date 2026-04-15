# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import re
import weakref
from importlib import import_module

from earthkit.data.core import Encodable as Encodable
from earthkit.data.core import Loader
from earthkit.data.core.caching import cache_file
from earthkit.data.core.plugins import find_plugin
from earthkit.data.core.plugins import register as register_plugin
from earthkit.data.data.source import DefaultSourceData


class Source(Loader):
    """Base class for all sources."""

    name = None
    source_filename = None

    def __init__(self, **kwargs):
        self._kwargs = kwargs
        self._parent = None

    def _cache_file(self, create, args, **kwargs):
        owner = self.name
        if owner is None:
            owner = re.sub(r"(?!^)([A-Z]+)", r"-\1", self.__class__.__name__).lower()

        return cache_file(owner, create, args, **kwargs)

    @property
    def parent(self):
        """The parent source, if any."""
        if self._parent is None:
            return None
        return self._parent()

    @parent.setter
    def parent(self, parent):
        self._set_parent(weakref.ref(parent))

    def _set_parent(self, parent):
        self._parent = parent

    def _repr_html_(self):
        return self.__repr__()

    def graph(self, depth=0):
        print(" " * depth, self)

    # def _encode(self, encoder, **kwargs):
    #     return encoder._encode(self, **kwargs)

    # def _default_encoder(self):
    #     return None

    def to_data_object(self):
        """Convert this source into a data object, if possible."""
        return DefaultSourceData(self)


class SourceLoader:
    kind = "source"

    def load_module(self, module):
        return import_module(module, package=__name__).source

    def load_entry(self, entry):
        entry = entry.load()
        if callable(entry):
            return entry
        return entry.source

    def load_remote(self, name):
        return None


class SourceMaker:
    SOURCES = {}

    def __call__(self, name, *args, **kwargs):
        loader = SourceLoader()

        if name in self.SOURCES:
            klass = self.SOURCES[name]
        else:
            klass = find_plugin(os.path.dirname(__file__), name, loader)
            self.SOURCES[name] = klass

        source = klass(*args, **kwargs)

        if getattr(source, "name", None) is None:
            source.name = name

        return source

    def __getattr__(self, name):
        return self(name.replace("_", "-"))


get_source = SourceMaker()


def from_source(name: str, *args, lazily=False, **kwargs) -> Source:
    if lazily:
        return from_source_lazily(name, *args, **kwargs)

    src = from_source_internal(name, *args, **kwargs)

    if hasattr(src, "to_data_object"):
        data = src.to_data_object()
        if data is not None:
            return data

    raise ValueError(f"Source {src} cannot be converted into a data object")


def from_source_internal(name: str, *args, lazily=False, **kwargs) -> Source:
    if lazily:
        return from_source_lazily(name, *args, **kwargs)

    prev = None
    src = get_source(name, *args, **kwargs)
    while src is not prev:
        prev = src
        src = src.mutate()

    return src


def from_source_lazily(name, *args, **kwargs):
    from earthkit.data.utils.lazy import LazySource

    return LazySource(name, *args, **kwargs)


def register(name, proc):
    register_plugin("source", name, proc)
