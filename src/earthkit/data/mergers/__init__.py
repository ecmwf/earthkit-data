# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.readers import Reader
from earthkit.data.sources import Source
from earthkit.data.sources.file import FileSource
from earthkit.data.utils import string_to_args

LOG = logging.getLogger(__name__)

FORWARDS = ("to_xarray", "to_pandas")


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


def _flatten(sources):
    """Recursively expand MultiSources that have no merger into a flat iterator of leaf sources.

    A :class:`earthkit.data.sources.multi.MultiSource` whose ``merger`` is not None is left as a single
    unit, since it will use its own merger rather than being merged together with its siblings.

    Parameters
    ----------
    sources : iterable of :class:`earthkit.data.sources.Source`
        The sources to flatten.

    Yields
    ------
    :class:`earthkit.data.sources.Source`
        Each leaf source or unresolved MultiSource.
    """
    from earthkit.data.sources.multi import MultiSource

    for s in sources:
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
    """
    common = _nearest_common_class(sources)
    return common.merge(sources)


class Merger:
    """Base class providing ``to_fieldlist``/``to_xarray``/``to_pandas`` for a list of sources.

    A Merger does not merge sources itself; it holds a list of sources and exposes conversion methods
    (implemented by subclasses) that each build a single object of the requested target type
    (:class:`FieldList`, ``xarray.Dataset``, or ``pandas.DataFrame``) out of them.

    On construction, the sources are flattened (see :func:`_flatten`) and, when they share a common
    :class:`FileSource`, :class:`Reader`, or :class:`Source` class, their file paths and reader class are
    resolved so that subclasses can operate directly on file paths instead of the higher-level sources.

    Attributes
    ----------
    sources : list of :class:`earthkit.data.sources.Source`
        The flattened sources to convert.
    paths : list of str or None
        The file paths of the sources, if they could be resolved; None otherwise.
    reader_class : type or None
        The nearest common :class:`Reader` class of the sources, if it could be resolved; None otherwise.
    common : type
        The nearest common class of the (unflattened) input sources.
    """

    def __init__(self, sources):
        """Initialize the Merger.

        Parameters
        ----------
        sources : list of :class:`earthkit.data.sources.Source`
            The sources to convert. Must not be empty.
        """
        assert sources

        self.sources = list(_flatten(sources))
        assert self.sources, sources

        self.paths = None
        self.reader_class = None
        self.common = _nearest_common_class(sources)
        LOG.debug("nearest_common_class %s", self.common)

        if issubclass(self.common, FileSource):
            # TODO: avoid calling _ methods
            readers = [s._reader for s in self.sources]
            self.reader_class = _nearest_common_class(readers)
            LOG.debug("nearest_common_class %s", self.reader_class)
            self.paths = [s.path for s in self.sources]
        elif issubclass(self.common, Reader):
            self.reader_class = self.common
            self.paths = [s.path for s in self.sources]
        elif issubclass(self.common, Source):
            # to enable the merging of a FieldList and a FileSource
            # needed for test_netcdf_wrong_concat_var
            readers = []
            paths = []
            for s in self.sources:
                if isinstance(s, FileSource):
                    readers.append(s._reader)
                    paths.append(s.path)
                elif isinstance(s, Reader):
                    readers.append(s)
                    paths.append(s.path)

            if len(readers) == len(self.sources):
                self.reader_class = _nearest_common_class(readers)
                self.paths = paths

    @property
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

    def to_xarray(self, **kwargs):
        """Convert the sources to a single xarray object.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to the subclass implementation.

        Returns
        -------
        xarray.Dataset
        """
        raise NotImplementedError("Subclasses must implement to_xarray()")

    def to_pandas(self, **kwargs):
        """Convert the sources to a single pandas DataFrame.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to the subclass implementation.

        Returns
        -------
        pandas.DataFrame
        """
        raise NotImplementedError("Subclasses must implement to_pandas()")

    def to_fieldlist(self, **kwargs):
        """Convert the sources to a single fieldlist.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to the subclass implementation.

        Returns
        -------
        :class:`earthkit.data.core.fieldlist.FieldList`
        """
        raise NotImplementedError("Subclasses must implement to_fieldlist()")


class DefaultMerger(Merger):
    """Merger used when no explicit merger is requested.

    Delegates each conversion to the merged sources: fieldlist conversion merges the sources' own
    fieldlists by their nearest common class, while pandas/xarray conversion defers to the corresponding
    ``merge`` function in :mod:`earthkit.data.mergers.pandas` / :mod:`earthkit.data.mergers.xarray`.
    """

    def to_fieldlist(self, **kwargs):
        """Merge the sources' fieldlists.

        Parameters
        ----------
        **kwargs
            Currently unused.

        Returns
        -------
        :class:`earthkit.data.core.fieldlist.FieldList`
            The result of merging the ``to_fieldlist()`` output of each source by their nearest common
            class (see :func:`merge_by_class`).
        """
        fs = [s.to_fieldlist() for s in self.sources]
        merged = merge_by_class(fs)
        return merged

    def to_pandas(self, **kwargs):
        """Merge the sources into a single pandas object.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to :func:`earthkit.data.mergers.pandas.merge`.

        Returns
        -------
        pandas.DataFrame
        """
        from .pandas import merge

        return merge(
            sources=self.sources,
            paths=self.paths,
            reader_class=self.reader_class,
            **kwargs,
        )

    def to_xarray(self, **kwargs):
        """Merge the sources into a single xarray object.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to :func:`earthkit.data.mergers.xarray.merge`.

        Returns
        -------
        xarray.Dataset
        """
        from .xarray import merge

        return merge(
            sources=self.sources,
            paths=self.paths,
            reader_class=self.reader_class,
            **kwargs,
        )


class ObjMerger(Merger):
    """Merger that delegates conversion to a user-supplied object.

    ``obj`` is selected as the merger (see :func:`make_merger`) when it exposes at least one of
    ``to_xarray``/``to_pandas`` (the methods listed in :data:`FORWARDS`); once selected, its
    ``to_fieldlist``/``to_xarray``/``to_pandas`` methods are all forwarded to as needed.

    Each of these methods on ``obj`` is called with the same signature: ``obj.to_xarray(paths_or_sources,
    **kwargs)`` (and likewise for ``to_fieldlist``/``to_pandas``), where:

    - ``paths_or_sources`` is passed positionally and is :obj:`Merger.paths_or_sources` — the list of file
      paths of the sources being merged, or the sources themselves when paths could not be resolved. The
      method must accept this single positional argument, whichever form it takes.
    - ``**kwargs`` are the keyword arguments given to the corresponding ``MultiSource.to_fieldlist`` /
      ``to_xarray`` / ``to_pandas`` call, forwarded unchanged. The method only needs to accept the keyword
      arguments it actually expects to receive.
    """

    def __init__(self, obj, sources, *args, **kwargs):
        """Initialize the ObjMerger.

        Parameters
        ----------
        obj : object
            An object with ``to_fieldlist``, ``to_xarray`` and/or ``to_pandas`` methods. Each such method
            must accept :obj:`Merger.paths_or_sources` as its single positional argument, plus whatever
            keyword arguments it wants to support (see the class docstring).
        sources : list of :class:`earthkit.data.sources.Source`
            The sources to merge.
        *args
            Unused.
        **kwargs
            Unused.
        """
        super().__init__(sources)
        self.obj = obj

    def to_fieldlist(self, **kwargs):
        """Call ``obj.to_fieldlist`` with the merged paths-or-sources.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to ``obj.to_fieldlist``.

        Returns
        -------
        object
            Whatever ``obj.to_fieldlist`` returns.
        """
        return self.obj.to_fieldlist(self.paths_or_sources, **kwargs)

    def to_xarray(self, *args, **kwargs):
        """Call ``obj.to_xarray`` with the merged paths-or-sources.

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
        """
        return self.obj.to_xarray(self.paths_or_sources, **kwargs)

    def to_pandas(self, *args, **kwargs):
        """Call ``obj.to_pandas`` with the merged paths-or-sources.

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
        """
        return self.obj.to_pandas(self.paths_or_sources, **kwargs)


class CallableMerger(Merger):
    """Merger that delegates ``to_fieldlist``, ``to_xarray`` and ``to_pandas`` to a single callable.

    ``func`` is selected as the merger (see :func:`make_merger`) whenever it is callable and does not
    match one of the other merger forms; all three conversion methods then call it the same way, passing
    the merged paths-or-sources as its first (positional) argument.
    """

    def __init__(self, func, sources, *args, **kwargs):
        """Initialize the CallableMerger.

        Parameters
        ----------
        func : callable
            A callable accepting the merged paths-or-sources as its first argument.
        sources : list of :class:`earthkit.data.sources.Source`
            The sources to merge.
        *args
            Unused.
        **kwargs
            Unused.
        """
        super().__init__(sources)
        self.func = func

    def _call_func(self, *args, **kwargs):
        """Call :obj:`func` with the merged paths-or-sources.

        Parameters
        ----------
        *args
            Unused.
        **kwargs
            Keyword arguments passed to :obj:`func`.

        Returns
        -------
        object
            Whatever :obj:`func` returns.
        """
        return self.func(self.paths_or_sources, **kwargs)

    to_fieldlist = _call_func
    to_xarray = _call_func
    to_pandas = _call_func


class XarrayGenericMerger(Merger):
    """Merger that combines the sources' file paths using ``xarray.open_mfdataset``.

    This is a base class, not directly reachable through :func:`make_merger`/:data:`MERGERS` — it factors
    out the ``open_mfdataset`` call shared by its subclasses, which supply :obj:`default_options` and are
    themselves looked up by name. See :class:`XarrayConcatMerger` (``"concat"`` in :data:`MERGERS`) for a
    usable example.

    Subclasses can be instantiated directly, bypassing :func:`make_merger`, when finer control over
    ``xarray.open_mfdataset`` options is needed than a merger string allows:

    >>> merger = XarrayConcatMerger(sources, concat_dim="time", combine="by_coords")
    >>> ds = merger.to_xarray()
    """

    def __init__(self, sources, **options):
        """Initialize the XarrayGenericMerger.

        Parameters
        ----------
        sources : list of :class:`earthkit.data.sources.Source`
            The sources to merge. Must resolve to file paths (see :obj:`Merger.paths`).
        **options
            Keyword arguments to pass to ``xarray.open_mfdataset``, overriding :obj:`default_options`.
        """
        super().__init__(sources)
        self.options = options

    def to_xarray(self, *args, **kwargs):
        """Open and combine the sources' file paths with ``xarray.open_mfdataset``.

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
        assert self.paths is not None, self.paths
        import xarray as xr

        options = {}
        options.update(self.default_options)
        options.update(self.options)
        options.update(kwargs)
        LOG.debug(f"xr.open_mfdataset with options = {options}")
        return xr.open_mfdataset(
            self.paths,
            **options,
        )


class XarrayConcatMerger(XarrayGenericMerger):
    """XarrayGenericMerger that concatenates sources along a dimension, using nested combination by default.

    This is the merger built by :func:`make_merger` for the ``"concat"`` name in :data:`MERGERS`, i.e. it
    is what ``merger="concat(...)"`` on :class:`earthkit.data.sources.multi.MultiSource` resolves to.

    Examples
    --------
    >>> ds = from_source("multi", [s1, s2], merger="concat(dim=time)").to_xarray()

    ``dim`` is renamed to ``concat_dim`` for ``xarray.open_mfdataset``; any other keyword accepted by it
    can be passed the same way, parsed by :func:`earthkit.data.utils.string_to_args`:

    >>> ds = from_source("multi", [s1, s2], merger="concat(dim=time,combine=nested)").to_xarray()
    """

    def __init__(self, sources, **options):
        """Initialize the XarrayConcatMerger.

        Parameters
        ----------
        sources : list of :class:`earthkit.data.sources.Source`
            The sources to merge.
        **options
            Keyword arguments to pass to ``xarray.open_mfdataset``. If ``dim`` is given, it is renamed to
            ``concat_dim``, as expected by ``open_mfdataset``.
        """
        if "dim" in options:
            dim = options.pop("dim")
            options["concat_dim"] = dim
        super().__init__(sources, **options)

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


def make_merger(merger, sources):
    """Build the :class:`Merger` instance appropriate for ``merger``.

    Parameters
    ----------
    merger : object, str, tuple, or None
        The merger specification. See :class:`earthkit.data.sources.multi.MultiSource` for the accepted
        values: an object exposing ``to_xarray``/``to_pandas`` becomes an :class:`ObjMerger`; a callable
        becomes a :class:`CallableMerger`; a string (optionally with ``key=value`` arguments, parsed by
        :func:`earthkit.data.utils.string_to_args`) or a ``(name, ...)``/``(name, {...})`` tuple is looked
        up in :data:`MERGERS`; None yields a :class:`DefaultMerger`.
    sources : list of :class:`earthkit.data.sources.Source`
        The sources to merge.

    Returns
    -------
    :class:`Merger`

    Raises
    ------
    ValueError
        If ``merger`` does not match any of the supported forms.

    Examples
    --------
    None always yields a :class:`DefaultMerger`, regardless of ``sources``:

    >>> make_merger(None, sources)  # doctest: +SKIP
    <DefaultMerger ...>

    A string is split into a name and ``key=value`` arguments by
    :func:`earthkit.data.utils.string_to_args`, and the name is looked up in :data:`MERGERS`. ``"concat"``
    resolves to :class:`XarrayConcatMerger`, so this passes ``dim="time"`` to its constructor:

    >>> make_merger("concat(dim=time)", sources)  # doctest: +SKIP
    <XarrayConcatMerger ...>

    A bare name with no ``(...)`` part is equivalent to no arguments at all. ``"merge"`` resolves to
    :class:`DefaultMerger` — the same class None yields, but reached explicitly by name rather than by the
    automatic-merging default:

    >>> make_merger("merge", sources)  # doctest: +SKIP
    <DefaultMerger ...>

    A ``(name, {...})`` tuple is a non-string alternative to the string form above, useful when an
    argument value cannot be represented as a plain string (e.g. it must stay an ``int`` rather than being
    parsed back out of text) — here it is equivalent to ``"concat(dim=time)"``:

    >>> make_merger(("concat", {"dim": "time"}), sources)  # doctest: +SKIP
    <XarrayConcatMerger ...>

    Anything else that is callable — a plain function here — becomes a :class:`CallableMerger`, which
    calls it the same way for every conversion, passing the merged paths-or-sources positionally:

    >>> make_merger(lambda paths_or_sources: xr.open_mfdataset(paths_or_sources), sources)  # doctest: +SKIP
    <CallableMerger ...>

    An object is checked first, before the plain-callable check above: if it exposes a ``to_xarray`` or
    ``to_pandas`` method (the names in :data:`FORWARDS`), it becomes an :class:`ObjMerger`, which forwards
    each conversion to the matching method on the object instead of calling the object itself:

    >>> make_merger(some_obj_with_to_xarray, sources)  # doctest: +SKIP
    <ObjMerger ...>
    """
    for fwd in FORWARDS:
        if hasattr(merger, fwd) and callable(getattr(merger, fwd)):
            LOG.debug("Merger %s has method in %s()", merger, fwd)
            return ObjMerger(merger, sources)

    if callable(merger):
        LOG.debug("Merger %s is callable", merger)
        return CallableMerger(merger, sources)

    if isinstance(merger, str):
        name, args, kwargs = string_to_args(merger)
        return MERGERS[name](sources, *args, **kwargs)

    if isinstance(merger, tuple):
        if len(merger) == 2 and isinstance(merger[1], dict):
            return MERGERS[merger[0]](sources, **merger[1])
        return MERGERS[merger[0]](sources, *merger[1:])

    if merger is None:
        LOG.debug("Using DefaultMerger")
        return DefaultMerger(sources)

    raise ValueError(f"Unsupported merger {merger} ({type(merger)})")
