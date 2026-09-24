# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import re
import weakref
from functools import partial
from importlib.metadata import entry_points
from typing import TYPE_CHECKING

from earthkit.data.core import Loader
from earthkit.data.core.caching import cache_file
from earthkit.data.sources.utils import _from_source, _preprocess_name

if TYPE_CHECKING:
    from earthkit.data.data import Data  # type: ignore[import]


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

    def to_data_object(self):
        """Convert this source into a data object, if possible."""
        from earthkit.data.data.source import DefaultSourceData

        return DefaultSourceData(self)


POSSIBLE_SOURCES = {
    "file": partial(_from_source, "file"),
    "file-pattern": partial(_from_source, "file-pattern"),
    "url": partial(_from_source, "url"),
    "url-pattern": partial(_from_source, "url-pattern"),
    "sample": partial(_from_source, "sample"),
    "stream": partial(_from_source, "stream"),
    "memory": partial(_from_source, "memory"),
    "forcings": partial(_from_source, "forcings"),
    "list-of-dicts": partial(_from_source, "list-of-dicts"),
    "multi": partial(_from_source, "multi"),
    "empty": partial(_from_source, "empty"),
    "dummy-source": partial(_from_source, "dummy-source"),
    "virtual": partial(_from_source, "virtual"),
    "virtual-directory": partial(_from_source, "virtual-directory"),
    "ads": partial(_from_source, "ads"),
    "cds": partial(_from_source, "cds"),
    "ecfs": partial(_from_source, "ecfs"),
    "ecmwf-open-data": partial(_from_source, "ecmwf-open-data"),
    "fdb": partial(_from_source, "fdb"),
    "gribjump": partial(_from_source, "gribjump"),
    "mars": partial(_from_source, "mars"),
    "opendap": partial(_from_source, "opendap"),
    "polytope": partial(_from_source, "polytope"),
    "s3": partial(_from_source, "s3"),
    "wekeo": partial(_from_source, "wekeo"),
    "wekeo-cds": partial(_from_source, "wekeo-cds"),
    "zarr": partial(_from_source, "zarr"),
}


def from_source(name: str, *args, lazily=False, **kwargs) -> "Data":
    name = _preprocess_name(name)

    if lazily:
        return from_source_lazily(name, *args, **kwargs)

    # Plugins take priority over built-in sources
    plugins = entry_points(group="earthkit.data.sources")
    if name in plugins.names:
        return _from_source_instance(plugins[name].load()(*args, **kwargs))

    if name in POSSIBLE_SOURCES:
        return POSSIBLE_SOURCES[name](*args, **kwargs)

    raise NameError(f"Source '{name}' does not exist.")


def _from_source_instance(src: Source) -> "Data":
    prev = None
    while src is not prev:
        prev = src
        src = src.mutate()

    if hasattr(src, "to_data_object"):
        data = src.to_data_object()
        if data is not None:
            return data

    raise ValueError(f"Source {src} cannot be converted into a data object")


def from_source_lazily(name, *args, **kwargs):
    from earthkit.data.utils.lazy import LazySource

    return LazySource(name, *args, **kwargs)
