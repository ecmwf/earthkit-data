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
import warnings
import weakref
from importlib import import_module
from typing import TYPE_CHECKING

from earthkit.data.core import Loader
from earthkit.data.core.caching import cache_file
from earthkit.data.core.plugins import find_plugin
from earthkit.data.core.plugins import register as register_plugin

if TYPE_CHECKING:
    import numpy.array

    from earthkit.data.core.fieldlist import FieldList
    from earthkit.data.data import Data  # type: ignore[import]
    from earthkit.data.sources import Source

from typing import Any, Callable, Literal, Union, overload


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
    """Create :class:`Source` objects by name.

    A source is implemented either as a module in this package or as a plugin. Calling
    the maker resolves the source class by name (:meth:`_lookup`) and instantiates it.
    The lookup itself is performed by :func:`find_plugin` and its result is cached in
    :attr:`_SOURCES`, so each source is only looked up once per session.

    The single instance created at module level is used by :func:`from_source`, which is
    the public entry point. Direct use is not needed in user code.

    Attributes
    ----------
    _SOURCES : dict of str to class
        Cache of the source classes already looked up, keyed by the resolved (i.e.
        non-aliased) source name. Shared by all the instances of :class:`SourceMaker`
        and populated on demand by :meth:`_lookup`.
    _ALIASES : dict of str to str
        Maps alternative source names to the name the source is registered under. Used to
        resolve the name before the lookup, so both the alias and the resolved name yield
        the same source class.
    _DEPRECATED : set of str
        The source names that are deprecated. Using one of them emits a ``FutureWarning``.
        When the deprecated name is also a key in :attr:`_ALIASES`, the warning names the
        alias target as the preferred name to use instead.

    """

    _SOURCES = {}

    _ALIASES = {
        "wekeocds": "wekeo-cds",
    }

    _DEPRECATED = {"wekeocds"}

    def __call__(self, name, *args, **kwargs):
        """Create the source called ``name``.

        Parameters
        ----------
        name : str
            The name of the source. Can be an alias, see :attr:`_ALIASES`.
        *args : tuple
            Positional arguments passed to the source class.
        **kwargs : dict, optional
            Keyword arguments passed to the source class.

        Returns
        -------
        :class:`Source`
            The new source. Its ``name`` is set to ``name`` (i.e. to the alias, when an
            alias was used) unless the source class already defines one.

        Raises
        ------
        NameError
            If no source or plugin called ``name`` can be found.

        Warns
        -----
        FutureWarning
            If ``name`` is deprecated, see :attr:`_DEPRECATED`.

        """
        klass = self._lookup(name)

        source = klass(*args, **kwargs)

        if getattr(source, "name", None) is None:
            source.name = name

        return source

    def _lookup(self, name):
        """Resolve a source name to the source class implementing it.

        The name is first mapped through :attr:`_ALIASES`, then looked up in
        :attr:`_SOURCES`. On a cache miss the source is located by :func:`find_plugin`,
        which searches the modules of this package as well as the registered plugins,
        and the result is added to :attr:`_SOURCES`.

        Parameters
        ----------
        name : str
            The name of the source. Can be an alias, see :attr:`_ALIASES`.

        Returns
        -------
        class
            The source class registered under the resolved name. Not instantiated.

        Raises
        ------
        NameError
            If no source or plugin called ``name`` can be found.

        Warns
        -----
        FutureWarning
            If ``name`` is deprecated, see :attr:`_DEPRECATED`.

        """
        loader = SourceLoader()

        if name in self._DEPRECATED:
            if name in self._ALIASES:
                preferred = self._ALIASES.get(name)
                warnings.warn(
                    f"Source name '{name}' is deprecated, use '{preferred}' instead",
                    FutureWarning,
                )
            else:
                warnings.warn(f"Source name '{name}' is deprecated", FutureWarning)

        lookup_name = self._ALIASES.get(name, name)
        if lookup_name in self._SOURCES:
            klass = self._SOURCES[lookup_name]
        else:
            klass = find_plugin(os.path.dirname(__file__), lookup_name, loader)
            self._SOURCES[lookup_name] = klass

        return klass

    def __getattr__(self, name: str):
        """Create a source using attribute access.

        Allows ``get_source.file_pattern`` as a shorthand for ``get_source("file-pattern")``.
        Underscores in ``name`` are replaced by dashes, since source names are dash-separated.
        The source is created without any arguments.

        Parameters
        ----------
        name : str
            The name of the source, with dashes optionally written as underscores.

        Returns
        -------
        :class:`Source`
            The new source.

        Raises
        ------
        NameError
            If no source or plugin called ``name`` can be found.

        """
        return self(name.replace("_", "-"))


get_source = SourceMaker()


@overload
def from_source(
    name: Literal["file"],
    path: str,
    expand_user: Union[bool, list, tuple] = True,
    expand_vars: bool = False,
    unix_glob: bool = True,
    recursive_glob: bool = True,
    filter: Union[str, Callable] = None,
    parts: list = None,
    stream: bool = False,
) -> "Data": ...


@overload
def from_source(
    name: Literal["file-pattern"], pattern: str, *args, hive_partitioning: bool = False, **kwargs
) -> "Data": ...


@overload
def from_source(
    name: Literal["url"],
    url: str,
    unpack: bool = True,
    parts: Union[list, tuple] = None,
    stream: bool = False,
    **kwargs,
) -> "Data": ...


@overload
def from_source(name: Literal["url-pattern"], url: str, unpack: bool = True, **kwargs) -> "Data": ...


@overload
def from_source(name: Literal["sample"], name_or_path: str) -> "Data": ...


@overload
def from_source(name: Literal["stream"], stream: Union[list, tuple]) -> "Data": ...


@overload
def from_source(name: Literal["memory"], buffer) -> "Data": ...


@overload
def from_source(
    name: Literal["forcings"], source_or_dataset=Union["Source", "FieldList"], *, request: dict = {}, **kwargs
) -> "Data": ...


@overload
def from_source(name: Literal["list-of-dicts"], list_of_dicts: list[dict]) -> "Data": ...


@overload
def from_source(
    name: Literal["multi"], *sources, merger: Union[str, Callable, tuple[str, dict], Any], **kwargs
) -> "Data": ...


@overload
def from_source(
    name: Literal["ads"], dataset: str, *args, request: Union[dict, list[dict], tuple[dict]] = None, **kwargs
) -> "Data": ...


@overload
def from_source(
    name: Literal["cds"],
    dataset: str,
    *args,
    request: Union[dict, list[dict], tuple[dict]] = None,
    prompt: bool = True,
    **kwargs,
) -> "Data": ...


@overload
def from_source(name: Literal["ecfs"], path: str) -> "Data": ...


@overload
def from_source(
    name: Literal["ecmwf-open-data"],
    *args,
    source: Literal["azure", "ecmwf"] = "ecmwf",
    model: Literal["ifs", "aifs"] = "ifs",
    request: Union[dict, list[dict], tuple[dict]] = None,
    **kwargs,
) -> "Data": ...


@overload
def from_source(
    name: Literal["fdb"],
    *args,
    config: Union[dict, str] = None,
    userconfig: Union[dict, str] = None,
    request: Union[dict, list[dict], tuple[dict]] = None,
    stream: bool = True,
    lazy: bool = False,
    **kwargs,
) -> "Data": ...


@overload
def from_source(
    name: Literal["gribjump"],
    request: Union[dict, list[dict], tuple[dict]] = None,
    *,
    ranges: list[tuple[int, int]] = None,
    mask: "numpy.array" = None,
    indices: "numpy.array" = None,
    fetch_coords_from_fdb: bool = False,
    fdb_kwargs: dict = None,
    **kwargs,
) -> "Data": ...


@overload
def from_source(
    name: Literal["mars"],
    *args,
    request: Union[dict, list[dict], tuple[dict]] = None,
    prompt: bool = True,
    log: Union[str, Callable, dict, None] = "default",
    **kwargs,
) -> "Data": ...


@overload
def from_source(name: Literal["opendap"], url: str) -> "Data": ...


@overload
def from_source(
    name: Literal["polytope"],
    collection: str,
    *args,
    address: str = None,
    user_email: str = None,
    user_key: str = None,
    request: Union[dict, list[dict], tuple[dict]] = None,
    stream: bool = True,
    **kwargs,
) -> "Data": ...


@overload
def from_source(
    name: Literal["s3"],
    *args,
    anon: bool = True,
    aws_access_key: str = None,
    aws_secret_access_key: str = None,
    aws_token: str = None,
    stream: bool = True,
) -> "Data": ...


@overload
def from_source(
    name: Literal["wekeo"],
    dataset: str,
    *args,
    request: Union[dict, list[dict], tuple[dict]] = None,
    prompt: bool = True,
    **kwargs,
) -> "Data": ...


@overload
def from_source(
    name: Literal["wekeocds"],
    dataset: str,
    *args,
    request: Union[dict, list[dict], tuple[dict]] = None,
    prompt: bool = True,
    **kwargs,
) -> "Data": ...


@overload
def from_source(
    name: Literal["wekeo-cds"],
    dataset: str,
    *args,
    request: Union[dict, list[dict], tuple[dict]] = None,
    prompt: bool = True,
    **kwargs,
) -> "Data": ...


@overload
def from_source(
    name: Literal["zarr"],
    path: str,
) -> "Data": ...


@overload
def from_source(
    name: Literal["zenodo"],
    identifier: str | int,
    only: str | list[str],
    **kwargs,
) -> "Data": ...


def from_source(name: str, *args, lazily=False, **kwargs) -> "Data":
    if lazily:
        return from_source_lazily(name, *args, **kwargs)

    src = _from_source_internal(name, *args, **kwargs)

    if hasattr(src, "to_data_object"):
        data = src.to_data_object()
        if data is not None:
            return data

    raise ValueError(f"Source {src} cannot be converted into a data object")


def _from_source_internal(name: str, *args, lazily=False, **kwargs) -> Source:
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
