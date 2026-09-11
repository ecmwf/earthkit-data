# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import inspect
import logging
from abc import ABCMeta, abstractmethod

import deprecation
from earthkit.utils.decorators import thread_safe_cached_property

from earthkit.data.data import Data
from earthkit.data.readers import Reader
from earthkit.data.sources import Source
from earthkit.data.sources.file import FileSource
from earthkit.data.utils import string_to_args

LOG = logging.getLogger(__name__)

FORWARDS = (
    "to_xarray",
    "to_pandas",
)


def _nearest_common_class(objects):
    """Find the most specific class shared by all ``objects`` in their inheritance hierarchy.

    Parameters
    ----------
    objects : list
        The objects (or classes) whose types' method resolution orders are compared.

    Returns
    -------
    type
        The nearest common ancestor class of ``type(o)`` for each ``o`` in ``objects``.
    """
    # mro() is "method resolution order"
    mros = [type(o).mro() for o in objects]

    first = mros[0]
    rest = mros[1:]
    for c in first:
        if all(c in m for m in rest):
            return c

    assert False


def _flatten(items):
    """Recursively expand MultiSources with no explicit merger into a flat iterator of leaf items.

    A :class:`earthkit.data.sources.multi.MultiSource` whose ``merger`` is None or False is expanded into
    its own items, since it has no merging behaviour of its own to preserve. A MultiSource with an
    explicit merger, by contrast, is left as a single unit, since it will use its own merger rather than
    being merged together with its siblings. Items that are not a ``MultiSource`` at all -- including a
    :class:`~earthkit.data.data.Data` object -- are yielded unchanged either way.

    Parameters
    ----------
    items : iterable of :class:`earthkit.data.sources.Source` or :ref:`Data object <data-object>`
        The items to flatten.

    Yields
    ------
    :class:`earthkit.data.sources.Source` or :ref:`Data object <data-object>`
        Each leaf item, or an unresolved ``MultiSource``.
    """
    from earthkit.data.sources.multi import MultiSource

    for s in items:
        if isinstance(s, MultiSource) and (s.merger is None or s.merger is False):
            yield from _flatten(s.sources)
        else:
            yield s


def merge_by_class(sources):
    """Merge ``sources`` using the ``merge`` classmethod of their nearest common class.

    Parameters
    ----------
    sources : list of :class:`earthkit.data.sources.Source`
        The sources to merge. Must share a common class that implements a ``merge`` classmethod.

    Returns
    -------
    object
        The result of calling ``merge`` on the nearest common class of ``sources``.

    Notes
    -----
    Elsewhere in the code any exception raised by this method is handled appropriately, ensuring that the
    calling code can respond to merge failures gracefully. The existence of a valid common class and the
    existence of a ``merge`` classmethod are not checked here explicitly.
    """
    common = _nearest_common_class(sources)
    return common.merge(sources)


class Merger(metaclass=ABCMeta):
    """Abstract base class providing ``to_fieldlist``/``to_xarray``/``to_pandas`` for a list of items.

    A Merger does not merge its items itself; it holds a list of them and exposes conversion methods
    (implemented by subclasses) that each build a single object of the requested target type
    (:class:`FieldList`, ``xarray.Dataset``, or ``pandas.DataFrame``) out of them.

    ``to_fieldlist``, ``to_xarray`` and ``to_pandas`` are abstract methods: a subclass that does not
    override all three cannot be instantiated (``TypeError``). :class:`DefaultMerger` is the concrete
    subclass providing a default implementation for all of them; most other subclasses build on it rather
    than on ``Merger`` directly.

    On construction, the items are flattened (see :func:`_flatten`) and their nearest common class is
    resolved (:obj:`common`); :obj:`sources`, :obj:`reader_class` and :obj:`paths` are then computed lazily
    (and cached) from that, on first access, rather than eagerly in ``__init__``, so subclasses can operate
    directly on file paths instead of the higher-level items only when they actually need to.

    Attributes
    ----------
    items : list of :class:`earthkit.data.sources.Source` or :ref:`Data object <data-object>`
        The flattened items to convert -- a mix of ``Source`` and ``Data`` objects is allowed.
    common : type
        The nearest common class of the (flattened) items.
    sources : list of :class:`earthkit.data.sources.Source`
        The underlying source of each item. If :obj:`common` is a :class:`FileSource` or :class:`Reader`
        subclass, this is simply :obj:`items` itself (they already are sources). If it is a :class:`Data`
        subclass, this is the ``_source`` of each item, but only if every item has one -- an empty list is
        returned instead as soon as one does not. In every other case this is an empty list.
    reader_class : type or None
        The nearest common :class:`Reader` class of the items, if it could be resolved; None (for a
        :class:`Data` :obj:`common`, an empty list) otherwise.
    paths : list of str or None
        The file paths of the items, if they could be resolved for every one of them; None otherwise.
    """

    def __init__(self, items):
        """Initialize the Merger.

        Parameters
        ----------
        items : list of :class:`earthkit.data.sources.Source` or :ref:`Data object <data-object>`
            The inputs to convert, as a list or tuple. Must not be empty (nor become empty once
            flattened).
        """
        assert items
        assert isinstance(items, (list, tuple))

        self.items = list(_flatten(items))
        assert self.items

        self.common = _nearest_common_class(self.items)

        LOG.debug("nearest_common_class %s", self.common)

    @thread_safe_cached_property
    def sources(self):
        """List of :class:`earthkit.data.sources.Source`: The underlying source of each item in :obj:`items`.

        See the class docstring for exactly how this is derived from :obj:`common`.
        """
        if issubclass(self.common, (FileSource, Reader)):
            return self.items
        elif issubclass(self.common, Data):
            result = []
            for d in self.items:
                if isinstance(d, Data) and hasattr(d, "_source"):
                    result.append(d._source)
                else:
                    return []
            return result

        return []

    @thread_safe_cached_property
    def reader_class(self):
        """Type or None: The nearest common :class:`Reader` class of :obj:`items`, if resolvable."""
        if issubclass(self.common, FileSource):
            readers = [s._reader for s in self.items]
            return _nearest_common_class(readers)
        elif issubclass(self.common, Reader):
            return self.common
        elif issubclass(self.common, Source):
            # to enable the merging of a FieldList and a FileSource
            # needed for test_netcdf_wrong_concat_var
            readers = []
            for s in self.items:
                if isinstance(s, FileSource):
                    readers.append(s._reader)
                elif isinstance(s, Reader):
                    readers.append(s)
                else:
                    return []

            return _nearest_common_class(readers)

        return None

    @thread_safe_cached_property
    def paths(self):
        """List of str or None: The file path of each item in :obj:`items`, if resolvable for all of them."""
        if issubclass(self.common, (FileSource, Reader)):
            return [s.path for s in self.items]
        elif issubclass(self.common, Source):
            # to enable the merging of a FieldList and a FileSource
            # needed for test_netcdf_wrong_concat_var
            result = []
            for s in self.items:
                if isinstance(s, FileSource):
                    result.append(s.path)
                elif isinstance(s, Reader):
                    result.append(s.path)
                else:
                    return None

            return result

        elif issubclass(self.common, Data):
            result = []
            for d in self.items:
                if isinstance(d, Data) and hasattr(d, "_source") and d._source is not None:
                    p = d.path
                    if isinstance(p, list) and all(isinstance(x, str) for x in p):
                        result.extend(p)
                    elif isinstance(p, str):
                        result.append(p)
                    else:
                        return None
                else:
                    return None

            return result

        return None

    @property
    @deprecation.deprecated(deprecated_in="1.3", removed_in=None, details="Deprecated.")
    def paths_or_sources(self):
        """Return the file paths of the sources, or the sources themselves if paths are unavailable.

        Returns
        -------
        list
            :obj:`paths` if it was resolved, otherwise :obj:`sources`.
        """
        if self.paths is not None:
            return self.paths
        return self.sources

    @abstractmethod
    def to_xarray(self, *args, **kwargs):
        """Convert the sources to a single xarray object.

        Parameters
        ----------
        *args
            Unused.
        **kwargs
            Keyword arguments passed to the subclass implementation.

        Returns
        -------
        xarray.Dataset
        """
        pass

    @abstractmethod
    def to_pandas(self, *args, **kwargs):
        """Convert the sources to a single pandas DataFrame.

        Parameters
        ----------
        *args
            Unused.
        **kwargs
            Keyword arguments passed to the subclass implementation.

        Returns
        -------
        pandas.DataFrame
        """
        pass

    @abstractmethod
    def to_fieldlist(self, *args, **kwargs):
        """Convert the sources to a single fieldlist.

        Parameters
        ----------
        *args
            Unused.
        **kwargs
            Keyword arguments passed to the subclass implementation.

        Returns
        -------
        :class:`earthkit.data.core.fieldlist.FieldList`
        """
        pass


class DefaultMerger(Merger):
    """Merger used when no explicit merger is requested.

    Delegates each conversion to :obj:`Merger.items` directly, via the corresponding ``merge`` function in
    :mod:`earthkit.data.mergers.fieldlist`/:mod:`earthkit.data.mergers.pandas`/:mod:`earthkit.data.mergers.xarray`:
    fieldlist conversion turns each item into its own fieldlist and merges those by nearest common class
    (see :func:`earthkit.data.mergers.fieldlist.merge`); pandas conversion concatenates each item's own
    ``to_pandas()`` result; xarray conversion opens the items (or their resolved :obj:`Merger.paths`) with
    ``xarray.open_mfdataset``.
    """

    def to_fieldlist(self, *args, **kwargs):
        """Merge the items into a single fieldlist.

        Parameters
        ----------
        *args
            Unused.
        **kwargs
            Keyword arguments passed to :func:`earthkit.data.mergers.fieldlist.merge`, forwarded from
            there to each item's own ``to_fieldlist()`` call where applicable.

        Returns
        -------
        :class:`earthkit.data.core.fieldlist.FieldList` or None
            The result of :func:`earthkit.data.mergers.fieldlist.merge`, which merges the ``to_fieldlist()``
            output of each item by their nearest common class (see :func:`merge_by_class`).
        """
        from .fieldlist import merge

        return merge(items=self.items, paths=None, reader_class=None, **kwargs)

    def to_pandas(self, *args, **kwargs):
        """Merge the items into a single pandas object.

        Parameters
        ----------
        *args
            Unused.
        **kwargs
            Keyword arguments passed to :func:`earthkit.data.mergers.pandas.merge`.

        Returns
        -------
        pandas.DataFrame
        """
        from .pandas import merge

        return merge(
            items=self.items,
            paths=None,
            reader_class=None,
            **kwargs,
        )

    def to_xarray(self, *args, **kwargs):
        """Merge the items into a single xarray object.

        Parameters
        ----------
        *args
            Unused.
        **kwargs
            Keyword arguments passed to :func:`earthkit.data.mergers.xarray.merge`.

        Returns
        -------
        xarray.Dataset
        """
        from .xarray import merge

        return merge(
            items=self.items,
            paths=self.paths,
            reader_class=self.reader_class,
            **kwargs,
        )


class ObjMerger(DefaultMerger):
    """Merger that delegates ``to_xarray``/``to_pandas`` to a user-supplied object.

    ``obj`` is selected as the merger (see :func:`make_merger`) when it exposes at least one of
    ``to_xarray``/``to_pandas`` (the methods listed in :data:`FORWARDS`). Once selected, ``to_xarray``/
    ``to_pandas`` each call the matching method on ``obj`` directly -- there is no fallback if ``obj`` does
    not actually implement the one being called (calling it then raises ``AttributeError``). ``to_fieldlist``
    calls ``obj.to_fieldlist`` if ``obj`` has one; otherwise it delegates to :class:`DefaultMerger`, which
    ``ObjMerger`` subclasses.

    How ``obj.to_xarray``/``obj.to_pandas`` is called depends on its signature (see :obj:`_forward`): if it
    accepts ``items`` and ``paths`` keyword arguments, it is called as ``obj.to_xarray(items=self.items,
    paths=self.paths, **kwargs)`` (and likewise for ``to_pandas``); otherwise it is called with the
    single-positional-argument form, ``obj.to_xarray(paths_or_sources, **kwargs)``, where
    ``paths_or_sources`` is :obj:`Merger.paths_or_sources` -- the list of file paths of the items being
    merged, or their underlying sources (:obj:`Merger.sources`) when paths could not be resolved. In both
    cases ``**kwargs`` are the keyword arguments given to the corresponding
    ``MultiSource.to_xarray``/``to_pandas`` call, forwarded unchanged.

    The single-positional-argument form is the older calling convention, kept only for backwards
    compatibility -- it relies on :obj:`Merger.paths_or_sources`, which is itself already deprecated (it
    cannot distinguish "no paths" from "no sources" the way separate ``items``/``paths`` arguments can).
    It is expected to be deprecated and eventually removed once user code has had a chance to migrate to
    the ``items``/``paths`` signature; new ``obj`` implementations should prefer that form.
    """

    def __init__(self, obj, items, *args, **kwargs):
        """Initialize the ObjMerger.

        Parameters
        ----------
        obj : object
            An object with ``to_xarray`` and/or ``to_pandas`` methods (see :obj:`_forward` for how each is
            called). Calling a conversion that ``obj`` does not implement raises ``AttributeError`` (see
            the class docstring). A ``to_fieldlist`` method, if present, is called the same way; otherwise
            ``to_fieldlist`` falls back to :class:`DefaultMerger`.
        items : list of :class:`earthkit.data.sources.Source` or :ref:`Data object <data-object>`
            The items to merge.
        *args
            Unused.
        **kwargs
            Unused.
        """
        super().__init__(items)
        self.obj = obj

    def _forward(self, method, **kwargs):
        """Call ``method`` with the arguments matching its signature.

        If ``method`` accepts ``items`` and ``paths`` keyword arguments, they are passed as such
        (:obj:`Merger.items` and :obj:`Merger.paths`, respectively) -- this is the preferred, forward-looking
        signature. Otherwise ``method`` is called with :obj:`Merger.paths_or_sources` as its single
        positional argument, as before -- this fallback exists only for backwards compatibility with
        ``obj`` implementations predating the ``items``/``paths`` signature, and is expected to be
        deprecated once :obj:`Merger.paths_or_sources` itself is removed.

        Parameters
        ----------
        method : callable
            ``obj.to_xarray`` or ``obj.to_pandas``.
        **kwargs
            Keyword arguments passed on to ``method``.

        Returns
        -------
        object
            Whatever ``method`` returns.
        """
        try:
            params = inspect.signature(method).parameters
        except (TypeError, ValueError):
            params = {}

        if "items" in params and "paths" in params:
            return method(items=self.items, paths=self.paths, **kwargs)

        return method(self.paths_or_sources, **kwargs)

    def to_fieldlist(self, *args, **kwargs):
        """Convert the items to a single fieldlist.

        If ``obj`` has a ``to_fieldlist`` method, it is called (see :obj:`_forward`); otherwise the call
        is delegated to :class:`DefaultMerger`.

        Parameters
        ----------
        *args
            Unused.
        **kwargs
            Keyword arguments passed to ``obj.to_fieldlist`` or to :meth:`DefaultMerger.to_fieldlist`.

        Returns
        -------
        object
        """
        if callable(getattr(self.obj, "to_fieldlist", None)):
            return self._forward(self.obj.to_fieldlist, **kwargs)

        return super().to_fieldlist(*args, **kwargs)

    def to_xarray(self, *args, **kwargs):
        """Call ``obj.to_xarray`` with the appropriate arguments (see :obj:`_forward`).

        Parameters
        ----------
        *args
            Unused.
        **kwargs
            Keyword arguments passed to ``obj.to_xarray``.

        Returns
        -------
        object
            Whatever ``obj.to_xarray`` returns.

        Raises
        ------
        AttributeError
            If ``obj`` has no ``to_xarray`` method.
        """
        return self._forward(self.obj.to_xarray, **kwargs)

    def to_pandas(self, *args, **kwargs):
        """Call ``obj.to_pandas`` with the appropriate arguments (see :obj:`_forward`).

        Parameters
        ----------
        *args
            Unused.
        **kwargs
            Keyword arguments passed to ``obj.to_pandas``.

        Returns
        -------
        object
            Whatever ``obj.to_pandas`` returns.

        Raises
        ------
        AttributeError
            If ``obj`` has no ``to_pandas`` method.
        """
        return self._forward(self.obj.to_pandas, **kwargs)


class CallableMerger(Merger):
    """Merger that delegates ``to_xarray`` and ``to_pandas`` to a single callable.

    ``func`` is selected as the merger (see :func:`make_merger`) whenever it is callable and does not
    match one of the other merger forms; ``to_xarray``/``to_pandas`` (both aliases of :obj:`_call_func`)
    then call it the same way, passing the merged paths-or-sources as their first (positional) argument.
    ``to_fieldlist`` is not implemented at all -- it always raises ``NotImplementedError``.
    """

    def __init__(self, func, items, *args, **kwargs):
        """Initialize the CallableMerger.

        Parameters
        ----------
        func : callable
            A callable accepting the merged paths-or-sources as its first argument.
        items : list of :class:`earthkit.data.sources.Source` or :ref:`Data object <data-object>`
            The items to merge.
        *args
            Unused.
        **kwargs
            Unused.
        """
        super().__init__(items)
        self.func = func

    def _call_func(self, *args, **kwargs):
        """Call :obj:`func` with the merged paths-or-sources, plus any extra arguments.

        Parameters
        ----------
        *args
            Additional positional arguments passed to :obj:`func`, after the paths-or-sources.
        **kwargs
            Keyword arguments passed to :obj:`func`.

        Returns
        -------
        object
            Whatever :obj:`func` returns.
        """
        return self.func(self.paths_or_sources, *args, **kwargs)

    def to_fieldlist(self, **kwargs):
        """Not implemented for CallableMerger.

        Raises
        ------
        NotImplementedError
            Always.
        """
        raise NotImplementedError("to_fieldlist is not implemented in CallableMerger")

    to_xarray = _call_func
    to_pandas = _call_func


class XarrayGenericMerger(DefaultMerger):
    """Merger that combines the items' file paths using ``xarray.open_mfdataset``.

    ``to_xarray`` is overridden to do so; ``to_fieldlist``/``to_pandas`` are not overridden at all, so they
    fall back to :class:`DefaultMerger`'s implementation, converting each item individually rather than
    using ``open_mfdataset``.

    This is a base class, not directly reachable through :func:`make_merger`/:data:`MERGERS` — it factors
    out the ``open_mfdataset`` call shared by its subclasses, which supply :obj:`default_options` and are
    themselves looked up by name. See :class:`XarrayConcatMerger` (``"concat"`` in :data:`MERGERS`) for a
    usable example.

    Subclasses can be instantiated directly, bypassing :func:`make_merger`, when finer control over
    ``xarray.open_mfdataset`` options is needed than a merger string allows:

    >>> merger = XarrayConcatMerger(items, concat_dim="time", combine="by_coords")
    >>> ds = merger.to_xarray()
    """

    def __init__(self, items, **options):
        """Initialize the XarrayGenericMerger.

        Parameters
        ----------
        items : list of :class:`earthkit.data.sources.Source` or :ref:`Data object <data-object>`
            The items to merge. Must resolve to file paths (see :obj:`Merger.paths`).
        **options
            Keyword arguments to pass to ``xarray.open_mfdataset``, overriding :obj:`default_options`.
        """
        super().__init__(items)
        self.options = options

    def to_xarray(self, *args, **kwargs):
        """Open and combine the items' file paths with ``xarray.open_mfdataset``.

        Delegates to :func:`earthkit.data.mergers.xarray.merge`, passing :obj:`Merger.items`/
        :obj:`Merger.paths` and the combined options as ``xarray_open_mfdataset_kwargs``.

        Parameters
        ----------
        *args
            Unused.
        **kwargs
            Keyword arguments to pass to ``xarray.open_mfdataset``, taking precedence over both
            :obj:`default_options` and :obj:`options`.

        Returns
        -------
        xarray.Dataset
        """
        options = {}
        options.update(self.default_options)
        options.update(self.options)
        options.update(kwargs)
        options = {"xarray_open_mfdataset_kwargs": options}

        from .xarray import merge

        return merge(items=self.items, paths=self.paths, reader_class=None, **options)


class XarrayConcatMerger(XarrayGenericMerger):
    """XarrayGenericMerger that concatenates items along a dimension, using nested combination by default.

    This is the merger built by :func:`make_merger` for the ``"concat"`` name in :data:`MERGERS`, i.e. it
    is what ``merger="concat(...)"`` on :class:`earthkit.data.sources.multi.MultiSource` resolves to.

    Examples
    --------
    >>> ds = from_source("multi", [s1, s2], merger="concat(dim=time)").to_xarray()

    ``dim`` is renamed to ``concat_dim`` for ``xarray.open_mfdataset``; any other keyword accepted by it
    can be passed the same way, parsed by :func:`earthkit.data.utils.string_to_args`:

    >>> ds = from_source("multi", [s1, s2], merger="concat(dim=time,combine=nested)").to_xarray()
    """

    def __init__(self, items, **options):
        """Initialize the XarrayConcatMerger.

        Parameters
        ----------
        items : list of :class:`earthkit.data.sources.Source` or :ref:`Data object <data-object>`
            The items to merge.
        **options
            Keyword arguments to pass to ``xarray.open_mfdataset``. If ``dim`` is given, it is renamed to
            ``concat_dim``, as expected by ``open_mfdataset``.
        """
        if "dim" in options:
            dim = options.pop("dim")
            options["concat_dim"] = dim
        super().__init__(items, **options)

    default_options = {"combine": "nested"}


class XarrayMerger(XarrayGenericMerger):
    """XarrayGenericMerger with no default options, i.e. using xarray's own defaults for combination."""

    default_options = {}


MERGERS = {
    "concat": XarrayConcatMerger,
    "merge": DefaultMerger,
}


def add_default_values_and_kwargs(args):
    """Parse a list of ``key=value`` strings into a keyword-argument dict.

    Parameters
    ----------
    args : list of str
        Strings of the form ``"key=value"``.

    Returns
    -------
    dict
        Mapping of each ``key`` to its (string) ``value``.
    """
    kwargs = dict()
    for a in args:
        k, v = a.split("=")
        kwargs[k] = v
    return kwargs


def make_merger(merger, items):
    """Build the :class:`Merger` instance appropriate for ``merger``.

    Parameters
    ----------
    merger : object, str, tuple, or None
        The merger specification. Must not already be a :class:`Merger` instance (see Raises below). See
        :class:`earthkit.data.sources.multi.MultiSource` for the accepted values: an object exposing
        ``to_xarray``/``to_pandas`` becomes an :class:`ObjMerger`; a callable becomes a
        :class:`CallableMerger`; a string (optionally with ``key=value`` arguments, parsed by
        :func:`earthkit.data.utils.string_to_args`) or a ``(name, ...)``/``(name, {...})`` tuple is looked
        up in :data:`MERGERS`; None yields a :class:`DefaultMerger`.
    items : list of :class:`earthkit.data.sources.Source` or :ref:`Data object <data-object>`
        The items to merge.

    Returns
    -------
    :class:`Merger`

    Raises
    ------
    ValueError
        If ``merger`` is already a :class:`Merger` instance, or does not match any of the supported forms.

    Examples
    --------
    None always yields a :class:`DefaultMerger`, regardless of ``items``:

    >>> make_merger(None, items)  # doctest: +SKIP
    <DefaultMerger ...>

    A string is split into a name and ``key=value`` arguments by
    :func:`earthkit.data.utils.string_to_args`, and the name is looked up in :data:`MERGERS`. ``"concat"``
    resolves to :class:`XarrayConcatMerger`, so this passes ``dim="time"`` to its constructor -- note that
    this merger only supports ``to_xarray()`` (see that class's docstring):

    >>> make_merger("concat(dim=time)", items)  # doctest: +SKIP
    <XarrayConcatMerger ...>

    A bare name with no ``(...)`` part is equivalent to no arguments at all. ``"merge"`` resolves to
    :class:`DefaultMerger` — the same class None yields, but reached explicitly by name rather than by the
    automatic-merging default:

    >>> make_merger("merge", items)  # doctest: +SKIP
    <DefaultMerger ...>

    A ``(name, {...})`` tuple is a non-string alternative to the string form above, useful when an
    argument value cannot be represented as a plain string (e.g. it must stay an ``int`` rather than being
    parsed back out of text) — here it is equivalent to ``"concat(dim=time)"``:

    >>> make_merger(("concat", {"dim": "time"}), items)  # doctest: +SKIP
    <XarrayConcatMerger ...>

    Anything else that is callable — a plain function here — becomes a :class:`CallableMerger`, which
    calls it the same way for ``to_xarray``/``to_pandas``, passing the merged paths-or-sources positionally
    (``to_fieldlist`` is not supported and always raises ``NotImplementedError``):

    >>> make_merger(lambda paths_or_sources: xr.open_mfdataset(paths_or_sources), items)  # doctest: +SKIP
    <CallableMerger ...>

    An object is checked first, before the plain-callable check above: if it exposes a ``to_xarray`` or
    ``to_pandas`` method (the names in :data:`FORWARDS`), it becomes an :class:`ObjMerger`, which forwards
    each of those conversions to the matching method on the object instead of calling the object itself
    (there is no fallback for whichever of the two it does not implement -- calling it then raises
    ``AttributeError``). ``to_fieldlist`` is forwarded to the object too, if it has one; otherwise it
    falls back to :class:`DefaultMerger`, which ``ObjMerger`` subclasses:

    >>> make_merger(some_obj_with_to_xarray, items)  # doctest: +SKIP
    <ObjMerger ...>
    """
    if isinstance(merger, Merger):
        raise ValueError(f"Merger is already an instance of Merger: {merger}")

    for fwd in FORWARDS:
        if hasattr(merger, fwd) and callable(getattr(merger, fwd)):
            LOG.debug("Merger %s has method in %s()", merger, fwd)
            return ObjMerger(merger, items)

    if callable(merger):
        LOG.debug("Merger %s is callable", merger)
        return CallableMerger(merger, items)

    if isinstance(merger, str):
        name, args, kwargs = string_to_args(merger)
        return MERGERS[name](items, *args, **kwargs)

    if isinstance(merger, tuple):
        if len(merger) == 2 and isinstance(merger[1], dict):
            return MERGERS[merger[0]](items, **merger[1])
        return MERGERS[merger[0]](items, *merger[1:])

    if merger is None:
        LOG.debug("Using DefaultMerger")
        return DefaultMerger(items)

    raise ValueError(f"Unsupported merger {merger} ({type(merger)})")
