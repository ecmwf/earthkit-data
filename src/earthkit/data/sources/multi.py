# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import itertools
import logging

import deprecation

from earthkit.data.mergers import make_merger, merge_by_class
from earthkit.data.sources.empty import EmptySource
from earthkit.data.utils.bbox import BoundingBox

from . import Source

LOG = logging.getLogger(__name__)


class MultiSource(Source):
    """Combine multiple sources or data objects into a single source.

    .. note::

        Users do not normally create or interact with a ``MultiSource`` directly -- it is mostly an
        internal implementation detail, used e.g. by :func:`from_source` itself when a source is given
        several inputs (a list of files, say). The supported, user-facing way to combine several objects
        is :func:`earthkit.data.concat`.

    A MultiSource holds a flat list of sub-items and behaves as their concatenation: iterating over it or
    indexing it yields the items of the sub-items in order. Each sub-item is stored internally as a
    :ref:`Data object <data-object>` (see :obj:`data`), not as a raw ``Source``: any ``Source`` passed in
    (or produced by a callable) is mutated and converted with ``to_data_object()`` during construction,
    while a ``Data`` object passed in directly is kept as is.

    Accepting ``Data`` objects as inputs, alongside ``Source``, is a consequence of :func:`from_source`
    itself returning a ``Data`` object rather than a ``Source`` since version 1.0: user code combining
    several results of :func:`from_source` therefore normally has ``Data`` objects on hand, not ``Source``
    objects, so ``MultiSource`` has to accept both. This introduces a complication, though: not every
    ``Data`` object has an underlying ``Source`` to fall back on -- one created by
    :func:`earthkit.data.from_object` typically does not, since it never came from reading a source in the
    first place. Such a ``Data`` item is accepted as a sub-item like any other, but cannot be converted
    back into a ``Source`` (see :obj:`mutate`).

    Whether the sub-items are actually merged into a single object is decided when :obj:`mutate` is called,
    and is controlled by the ``merger`` parameter. See :obj:`__init__` for details.

    Attributes
    ----------
    data : list of :ref:`Data object <data-object>`
        The flattened list of sub-items, each normalized to a ``Data`` object as described above. Nested
        MultiSources/:class:`~earthkit.data.data.multi.MultiData` are expanded when possible (see
        :obj:`_flatten`), so this list does not normally contain one of those. Items that earthkit-data
        could not recognise the format of are dropped from this list, unless ``merger=False`` was passed
        to :obj:`__init__`, in which case they are kept.
    sources : list of :class:`Source`
        Deprecated. The underlying ``Source`` of each item in :obj:`data` that has one (via its
        ``_source`` attribute); items without one are silently omitted, so this list can be shorter than
        :obj:`data`. Kept only for backward compatibility -- prefer :obj:`data`.
    filter : object or None
        The filter passed to the constructor. Currently stored but not applied.
    merger : object, str, tuple, or None
        The effective merger -- anything accepted as the ``merger`` argument of
        :func:`earthkit.data.mergers.make_merger` (never a :class:`Merger` instance itself), including the
        special value None (automatic merging). Note that this is never False, even when ``merger=False``
        was passed to :obj:`__init__`: that only changes which sub-items end up in :obj:`data`, and is
        normalized to None here, so later conversions can still merge the surviving sub-items by nearest
        common class, exactly as the None default does (see :obj:`__init__`). This attribute is never
        replaced with a built :class:`Merger` instance: :obj:`mutate` only ever consults it (together with
        whether merging was disabled at construction) to decide whether to attempt automatic merging.
        Building the actual ``Merger`` for an explicit (non-None) value is not done by ``MultiSource``
        itself: it is the responsibility of the :ref:`Data object <data-object>` returned by
        :func:`from_source` (e.g. :class:`~earthkit.data.data.multi.MultiData`), which reads this
        attribute directly and calls :func:`~earthkit.data.mergers.make_merger` itself for each
        conversion, rather than through :obj:`to_fieldlist`/:obj:`to_xarray`/:obj:`to_pandas`/
        :obj:`statistics` below -- those methods remain for backward compatibility only and are
        deprecated.
    """

    def __init__(self, *items, filter=None, merger=None, **kwargs):
        """Initialize the MultiSource.

        Parameters
        ----------
        *items
            The sources or :ref:`Data objects <data-object>` to combine. Either a single list of items or
            the items as positional arguments. Once any callables have been evaluated (see below), each
            item must be a :class:`Source` or a ``Data`` object -- checked with ``isinstance``, so passing
            a ``Data`` object directly (e.g. one already returned by :func:`from_source`) is supported
            natively, without relying on a ``_source`` attribute. Accepting ``Data`` objects here, and not
            just ``Source`` objects, matters because :func:`from_source` itself has returned a ``Data``
            object rather than a ``Source`` since version 1.0, so that is normally what callers have on
            hand to combine. A ``Source`` item is mutated and converted with ``to_data_object()``; a
            ``Data`` item is kept as is (see :obj:`data`) -- note that some ``Data`` objects, e.g. ones
            created by :func:`earthkit.data.from_object` rather than read from a source, have no
            underlying source at all, which :obj:`mutate` cannot always work around (see there). Items can
            also be callables returning a ``Source`` or ``Data`` object; these are evaluated here, in
            parallel when there is more than one of them.
        filter : optional
            The filter to apply to the sources.
        merger : object, str, tuple, None, or False
            The merger to use for combining the sub-items. This is never a :class:`Merger` instance itself —
            it is any value accepted as the ``merger`` argument of :func:`earthkit.data.mergers.make_merger`,
            which is called to build the actual :class:`Merger` on demand. The values are interpreted as
            follows:

            - None (the default) requests automatic merging: when the MultiSource is mutated, it tries to
              merge the underlying sources of the sub-items (see :obj:`data`) by their nearest common
              class. If that succeeds, the MultiSource mutates itself into the single merged object —
              e.g. when all the input files are of the same type. If it fails, no merger is built and the
              MultiSource remains a collection of its sub-items.
            - False keeps every sub-item, including ones that would otherwise be silently dropped when a
              MultiSource is created — typically ones earthkit-data assigns an UnknownReader, e.g.
              unsupported file types (see :obj:`data`). This does not, however, disable merging for later
              conversions: :obj:`merger` is normalized to None once construction is complete, so a
              conversion on the surviving sub-items still merges by nearest common class, exactly as with
              the None default. What False actually skips is the *automatic* merge attempt made while
              mutating (see :obj:`mutate`) — which is why a MultiSource created with ``merger=False``
              surfaces as a :class:`~earthkit.data.data.multi.MultiData` rather than mutating into a
              single, type-specific object.
            - Any other value is passed to :func:`make_merger` to build a :class:`Merger` instance. Unlike
              the None case, this Merger is not built while mutating, nor by ``MultiSource`` at all: it is
              built lazily, on demand, by the :ref:`Data object <data-object>` returned by
              :func:`from_source` (e.g. :class:`~earthkit.data.data.multi.MultiData`), which reads
              ``merger`` directly and calls :func:`make_merger` itself for each conversion the user
              requests. ``MultiSource`` also exposes :obj:`to_fieldlist`/:obj:`to_xarray`/:obj:`to_pandas`
              methods that do the same thing, but calling them directly is deprecated — convert through
              the Data object instead. :obj:`statistics` is also deprecated, but is currently non-functional.
        **kwargs
            Additional keyword arguments passed to :class:`Source`.

        Raises
        ------
        ValueError
            If an item in ``items``, once any callables have been evaluated, is neither a :class:`Source`
            nor a ``Data`` object.

        Examples
        --------
        These examples use ``from_source("multi", ...)``/``from_source("file", [...], ...)`` to illustrate
        the ``merger`` values, since that is how a ``MultiSource`` ends up being created; for combining
        objects you already have on hand, e.g. two results of :func:`from_source`, prefer
        :func:`earthkit.data.concat` instead of constructing a ``MultiSource`` or calling
        ``from_source("multi", ...)`` directly. In all the examples below, ``ds`` is the :ref:`Data object
        <data-object>` returned by :func:`from_source` (e.g. :class:`~earthkit.data.data.multi.MultiData`),
        not the underlying ``MultiSource`` -- its ``to_xarray``/``to_pandas``/``to_fieldlist`` methods,
        unlike the deprecated ones on ``MultiSource``, are the supported way to trigger the merger
        described here.

        Keep every file as a separate source, including ones earthkit-data would otherwise ignore:

        >>> ds = from_source("file", ["a.grib", "unsupported.bin"], merger=False)

        Concatenate NetCDF/xarray sources along a dimension, using the ``"concat"`` builtin merger
        (``dim`` is passed through :func:`earthkit.data.utils.string_to_args` as a ``key=value`` argument):

        >>> ds = from_source("multi", [s1, s2], merger="concat(dim=time)")
        >>> ds.to_xarray()

        Force merging by nearest common class rather than the default concatenation, using the
        ``"merge"`` builtin merger:

        >>> ds = from_source("multi", [s1, s2], merger="merge")

        Supply a custom merger as a plain callable, receiving the merged file paths (or sources, if paths
        could not be resolved) as its only positional argument:

        >>> def merger_func(paths_or_sources):
        ...     return xr.open_mfdataset(paths_or_sources)
        >>> ds = from_source("multi", [s1, s2], merger=merger_func).to_xarray()

        Supply a custom merger as an object, implementing only the conversions it needs to support:
        ``to_xarray``/``to_pandas`` each take the merged paths-or-sources positionally, while
        ``to_fieldlist`` instead takes the raw sources; all three also accept whatever keyword arguments
        are forwarded from the call site:

        >>> class MyMerger:
        ...     def to_xarray(self, paths_or_sources, **kwargs):
        ...         return xr.open_mfdataset(paths_or_sources, **kwargs)
        >>> ds = from_source("multi", [s1, s2], merger=MyMerger()).to_xarray()
        """
        super().__init__(**kwargs)
        if len(items) == 1 and isinstance(items[0], list):
            items = items[0]

        self._merge_in_mutate = True
        remove_ignored = True
        self.merger = merger
        if self.merger is False:
            self._merge_in_mutate = False
            remove_ignored = False
            self.merger = None
        elif self.merger is not None:
            self._merge_in_mutate = False

        # print("MultiSource merger:", self.merger)

        # print("MultiSource 1")
        # for d in items:
        #     print("  item:", d)

        items = self._evaluate(items)
        self.data = self._prepare(items, remove_ignored=remove_ignored)

        # print(" ---> ")
        # for d in self.data:
        #     print("  item:", d, "source:", getattr(d, "_source", None))

        # print(" merger:", self.merger)
        # print(" merge_in_mutate:", self._merge_in_mutate)
        # print(" remove_ignored:", remove_ignored)

        # for backward compatibility, store the original sources separately
        self._sources = [d._source for d in self.data if hasattr(d, "_source")]

        # print("Original sources stored in _sources:", self._sources)

        self.filter = filter
        self._lengths = [None] * len(items)

    @property
    @deprecation.deprecated(deprecated_in="1.3", removed_in=None, details="Deprecated.")
    def sources(self):
        """List of :class:`Source`: Deprecated. See the class-level :obj:`sources` docs.

        Note that most of the other methods below (:obj:`__iter__`, :obj:`__getitem__`, :obj:`__len__`,
        :obj:`__repr__`, :obj:`graph`, :obj:`paths`, :obj:`datetime`, :obj:`bounding_box`) still read this
        property internally rather than :obj:`data`, so using them also triggers this deprecation warning.
        """
        return self._sources

    def ignore(self):
        """Report whether this source should be ignored when building a parent MultiSource.

        Returns
        -------
        bool
            True if this MultiSource has no sub-items left after filtering (see :obj:`data`).
        """
        return len(self.data) == 0

    def mutate(self):
        """Attempt to collapse this MultiSource into a simpler object.

        Unlike the rest of this class, ``mutate`` must return a :class:`Source`, never a ``Data`` object:
        it is part of the same ``mutate``-until-fixed-point machinery :func:`from_source` itself uses, and
        that machinery only ever deals in ``Source`` objects, converting the final result to a ``Data``
        object (via ``to_data_object()``) only once mutation has settled. This is where the complication
        of :ref:`Data objects without an underlying source <data-object>` (see the class docstring) bites:
        a sub-item like that has nothing for ``mutate`` to fall back on.

        With a single sub-item (see :obj:`data`), mutates into that item's underlying source directly: if
        the item is itself a :class:`Source`, its own :obj:`mutate` is called; if it is a ``Data`` object
        with a ``_source`` attribute, that source is returned as is (it was already mutated when the
        ``Data`` object was built, see :obj:`__init__`); a ``Data`` object with no ``_source`` (typically
        one created by :func:`earthkit.data.from_object`) cannot be converted this way and raises
        ``RuntimeError``. With no sub-items, returns an :class:`EmptySource`.

        Otherwise, automatic merging by nearest common class is attempted, but only when :obj:`merger` is
        None *and* ``merger=False`` was not passed to :obj:`__init__` (merging having been disabled at
        construction is remembered even though it also normalizes :obj:`merger` to None, see :obj:`merger`)
        *and* every sub-item has an underlying source to merge (see :obj:`sources`). In every other case --
        an explicit merger, merging having been disabled, or a sub-item with no underlying source -- this
        leaves ``self`` unchanged: an explicit merger is only ever built later, lazily, by the :ref:`Data
        object <data-object>` returned by :func:`from_source`.

        Returns
        -------
        :class:`Source`
            The mutated object, which may be ``self``.

        Raises
        ------
        RuntimeError
            If there is a single sub-item and it is a ``Data`` object with no underlying source.
        """
        if len(self.data) == 1:
            if isinstance(self.data[0], Source):
                return self.data[0].mutate()
            elif hasattr(self.data[0], "_source"):
                return self.data[0]._source
            else:
                raise RuntimeError("Cannot convert the single data object into a source.")

        if len(self.data) == 0:
            return EmptySource()

        # when merger is None, attempt to merge the sources using the default merger.
        if self._merge_in_mutate:
            if len(self.data) == len(self._sources):
                try:
                    merged = merge_by_class(self._sources)
                    if merged is not None:
                        return merged.mutate()
                except Exception:
                    pass

        return self

    def __iter__(self):
        """Iterate over the items of all sub-items' underlying sources, in order, as a flat sequence.

        Note: like :obj:`__getitem__`/:obj:`__len__`/:obj:`_length` below, this relies on the deprecated
        :obj:`sources` property rather than :obj:`data`, and so also raises its deprecation warning.
        """
        return itertools.chain(*self.sources)

    def __getitem__(self, n):
        """Get the ``n``-th item across all sub-items' underlying sources.

        Parameters
        ----------
        n : int
            The index of the item, treating the underlying sources (see :obj:`sources`) as one
            concatenated sequence. Negative indices are supported and count from the end.

        Returns
        -------
        object
            The item at index ``n``, taken from the source it falls into.
        """
        if n < 0:
            n = len(self) + n

        i = 0
        while n >= self._length(i):
            n -= self._length(i)
            i += 1
        return self.sources[i][n]

    @deprecation.deprecated(
        deprecated_in="1.3",
        removed_in=None,
        details="Deprecated.",
    )
    def sel(self, *args, **kwargs):
        """Not implemented for MultiSource.

        Deprecated.
        """
        self._not_implemented()

    @deprecation.deprecated(
        deprecated_in="1.3",
        removed_in=None,
        details="Deprecated.",
    )
    def order_by(self, *args, **kwargs):
        """Not implemented for MultiSource.

        Deprecated.
        """
        self._not_implemented()

    @deprecation.deprecated(
        deprecated_in="1.3",
        removed_in=None,
        details="Deprecated.",
    )
    def metadata(self, *args, **kwargs):
        """Not implemented for MultiSource.

        Deprecated.
        """
        self._not_implemented()

    @deprecation.deprecated(
        deprecated_in="1.3",
        removed_in=None,
        details="Deprecated.",
    )
    def __len__(self):
        """Return the total number of items across all sub-items' underlying sources (see :obj:`sources`).

        Deprecated.
        """
        return sum(self._length(i) for i, _ in enumerate(self.sources))

    def _length(self, i):
        """Return the (cached) length of the ``i``-th underlying source.

        Parameters
        ----------
        i : int
            Index into :obj:`sources`.

        Returns
        -------
        int
            The number of items in ``self.sources[i]``.
        """
        if self._lengths[i] is None:
            self._lengths[i] = len(self.sources[i])
        return self._lengths[i]

    def __repr__(self) -> str:
        """Return a repr listing the reprs of all sub-items' underlying sources (see :obj:`sources`)."""
        string = ",".join(repr(s) for s in self.sources)
        return f"{self.__class__.__name__}({string})"

    def to_target(self, target, *args, **kwargs):
        """Write this source's data to a target.

        Parameters
        ----------
        target : str or object
            The target to write to. See :func:`earthkit.data.targets.to_target`.
        *args
            Additional positional arguments passed to :func:`earthkit.data.targets.to_target`.
        **kwargs
            Additional keyword arguments passed to :func:`earthkit.data.targets.to_target`.
        """
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self, **kwargs)

    def paths(self):
        """Return a list of paths, one per underlying source (see :obj:`sources`).

        For a source exposing a callable ``paths()`` method (e.g. a nested MultiSource), its own paths are
        extended into the result instead of a single entry.

        Returns
        -------
        list
            The collected paths.
        """
        paths = []
        for s in self.sources:
            if hasattr(s, "paths") and callable(s.paths):
                paths.extend(s.paths())
            elif hasattr(s, "path"):
                paths.append(s.path)
            else:
                paths.append(s.path)
        return paths

    def graph(self, depth=0):
        """Print a tree representation of this source and its sub-items' underlying sources.

        Parameters
        ----------
        depth : int
            The current indentation level, in characters. Each underlying source (see :obj:`sources`) is
            printed with an increased indentation.
        """
        print(" " * depth, self.__class__.__name__, self.merger)
        for s in self.sources:
            s.graph(depth + 3)

    @deprecation.deprecated(
        deprecated_in="1.3",
        removed_in=None,
        details=(
            "Calling to_fieldlist() directly on the Source is deprecated. Use the to_fieldlist() method of "
            "the Data object returned by from_source() instead."
        ),
    )
    def to_fieldlist(self, **kwargs):
        """Convert the sub-items into a :class:`FieldList` using :obj:`merger`.

        Deprecated: kept only for backward compatibility. The :ref:`Data object <data-object>` returned by
        :func:`from_source` never calls this method -- it builds and uses its own :class:`Merger` directly
        from :obj:`merger`. Call ``to_fieldlist()`` on that Data object instead of on this ``MultiSource``.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to the merger's ``to_fieldlist`` method.

        Returns
        -------
        :class:`FieldList`
        """
        return make_merger(self.merger, self.data).to_fieldlist(**kwargs)

    @deprecation.deprecated(
        deprecated_in="1.3",
        removed_in=None,
        details=(
            "Calling to_xarray() directly on the Source is deprecated. Use the to_xarray() method of the "
            "Data object returned by from_source() instead."
        ),
    )
    def to_xarray(self, **kwargs):
        """Convert the sub-items into an xarray object using :obj:`merger`.

        Deprecated: kept only for backward compatibility. The :ref:`Data object <data-object>` returned by
        :func:`from_source` never calls this method -- it builds and uses its own :class:`Merger` directly
        from :obj:`merger`. Call ``to_xarray()`` on that Data object instead of on this ``MultiSource``.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to the merger's ``to_xarray`` method.

        Returns
        -------
        xarray.Dataset or xarray.DataArray
        """
        return make_merger(self.merger, self.data).to_xarray(**kwargs)

    @deprecation.deprecated(
        deprecated_in="1.3",
        removed_in=None,
        details=(
            "Calling to_pandas() directly on the Source is deprecated. Use the to_pandas() method of the "
            "Data object returned by from_source() instead."
        ),
    )
    def to_pandas(self, **kwargs):
        """Convert the sub-items into a pandas object using :obj:`merger`.

        Deprecated: kept only for backward compatibility. The :ref:`Data object <data-object>` returned by
        :func:`from_source` never calls this method -- it builds and uses its own :class:`Merger` directly
        from :obj:`merger`. Call ``to_pandas()`` on that Data object instead of on this ``MultiSource``.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to the merger's ``to_pandas`` method.

        Returns
        -------
        pandas.DataFrame
        """
        return make_merger(self.merger, self.data).to_pandas(**kwargs)

    @deprecation.deprecated(
        deprecated_in="1.3",
        removed_in=None,
        details="Deprecated, and currently non-functional.",
    )
    def statistics(self, **kwargs):
        """Compute statistics over the sub-items using :obj:`merger`.

        Deprecated and currently non-functional.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to the merger's ``statistics`` method.

        Returns
        -------
        object
            The statistics, as returned by the merger.
        """
        return make_merger(self.merger, self.data).statistics(**kwargs)

    @deprecation.deprecated(
        deprecated_in="1.3",
        removed_in=None,
        details="Deprecated.",
    )
    def datetime(self, **kwargs):
        """Return the combined datetime information of all sub-items' underlying sources.

        Deprecated.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to each sub-source's ``datetime`` method.

        Returns
        -------
        dict
            Mapping of datetime kind (e.g. "base_time", "valid_time") to a sorted list of the values found
            across all underlying sources.
        """
        result = dict()
        for s in self.sources:
            result.update(s.datetime(**kwargs))
        return {k: sorted(v) for k, v in result.items()}

    @deprecation.deprecated(
        deprecated_in="1.3",
        removed_in=None,
        details="Deprecated.",
    )
    def bounding_box(self):
        """Return the bounding box covering all sub-items' underlying sources.

        Deprecated.

        Returns
        -------
        :class:`earthkit.data.utils.bbox.BoundingBox`
            The union of the bounding boxes of all underlying sources.
        """
        return BoundingBox.union([s.bounding_box() for s in self.sources])

    def to_data_object(self):
        """Convert this source into a :class:`MultiData` object.

        Passes :obj:`data` and :obj:`merger` straight through to the constructor, so the resulting
        ``MultiData`` sees the same sub-items and effective merger as this ``MultiSource``.

        Returns
        -------
        :class:`earthkit.data.data.multi.MultiData`
        """
        from earthkit.data.data.multi import MultiData

        return MultiData(self.data, merger=self.merger)

    def _evaluate(self, items):
        """Evaluate any callables in ``items``, leaving every other item untouched.

        Non-callable items (:class:`Source`, ``Data`` objects, or anything else) are passed through as is;
        type validation happens later, in :obj:`_prepare`. Callable items are called to produce their
        result; when there is more than one callable, they are evaluated concurrently using a thread pool,
        with the number of threads capped by the ``number-of-download-threads`` config setting.

        Parameters
        ----------
        items : iterable
            The raw inputs passed to :obj:`__init__`.

        Returns
        -------
        list
            ``items``, with every callable item replaced by its result.
        """
        callables = []
        has_callables = False
        items_in = items
        items = []
        for d in items_in:
            if callable(d):
                has_callables = True
                callables.append(d)
                items.append(d)
            else:
                items.append(d)
                callables.append(lambda *args, **kwargs: d)

        assert len(items) == len(callables)

        if not has_callables:
            return items

        from earthkit.data.core.config import CONFIG

        nthreads = min(CONFIG.get("number-of-download-threads"), len(callables))

        if nthreads < 2:
            return [s() for s in callables]

        def _call(s, *args, **kwargs):
            return s(*args, **kwargs)

        from earthkit.data.core.thread import SoftThreadPool
        from earthkit.data.utils.progbar import tqdm

        with SoftThreadPool(nthreads=nthreads) as pool:
            futures = [pool.submit(_call, s) for s in callables]
            iterator = (f.result() for f in futures)
            items = list(tqdm(iterator, leave=False, total=len(futures)))

        return items

    def _prepare(self, items, remove_ignored=False):
        """Flatten ``items`` (see :obj:`_flatten`) and normalize each one into a ``Data`` object.

        A :class:`Source` item is mutated (:obj:`Source.mutate`) and converted with ``to_data_object()``;
        a ``Data`` item is kept as is. When ``remove_ignored`` is True, an item is dropped instead if its
        underlying source reports itself as ignorable (:obj:`Source.ignore`) -- this is what implements
        the ``merger=False`` behaviour described in :obj:`__init__`.

        Parameters
        ----------
        items : iterable of :class:`Source` or :ref:`Data object <data-object>`
            The (already flattened-eligible) items to normalize, typically the result of :obj:`_evaluate`.
        remove_ignored : bool, default False
            Whether to drop items whose underlying source is ignorable.

        Returns
        -------
        list of :ref:`Data object <data-object>`
            The normalized items, to be stored in :obj:`data`.

        Raises
        ------
        ValueError
            If an item is neither a :class:`Source` nor a ``Data`` object.
        """
        from earthkit.data.data import Data

        items_in = self._flatten(items)
        items = []
        for d in items_in:
            if isinstance(d, Source):
                if remove_ignored and d.ignore():
                    continue
                d = d.mutate()
                items.append(d.to_data_object())
            elif isinstance(d, Data):
                if remove_ignored:
                    if hasattr(d, "_source") and d._source is not None and d._source.ignore():
                        continue
                items.append(d)
            else:
                raise ValueError(f"MultiSource: expected Source or Data, got {type(d)}")

        return items

    def _flatten(self, items):
        """Recursively expand nested MultiSources/MultiData into a flat iterator of leaf items.

        Expansion only happens while ``self`` itself requests automatic merging (:obj:`merger` is None);
        if ``self`` has an explicit merger (or merging was disabled, which also normalizes :obj:`merger` to
        None -- see :obj:`__init__`), nothing here is expanded at all, since every item is then merged
        (or not) by ``self`` as a single unit regardless of its own nested structure. When expansion is
        attempted, a nested :class:`MultiSource` or :class:`~earthkit.data.data.multi.MultiData` is only
        expanded into its own items if it likewise has no explicit merger of its own (checked via its
        ``merger``/``_merger`` attribute); otherwise it is left as a single unit, since it will use its own
        merger rather than being merged together with its siblings.

        Parameters
        ----------
        items : iterable of :class:`Source` or :ref:`Data object <data-object>`
            The items to flatten.

        Yields
        ------
        :class:`Source` or :ref:`Data object <data-object>`
            Each leaf item, or an unexpanded nested MultiSource/MultiData.
        """
        from earthkit.data.data.multi import MultiData

        for s in items:
            if self.merger is None:
                if isinstance(s, (MultiSource)) and s.merger is None:
                    yield from self._flatten(s.data)
                elif isinstance(s, (MultiData)) and s._merger is None:
                    yield from self._flatten(s._data)
                else:
                    yield s
            else:
                yield s


source = MultiSource
