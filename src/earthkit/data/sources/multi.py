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

from earthkit.data.mergers import make_merger, merge_by_class
from earthkit.data.sources.empty import EmptySource
from earthkit.data.utils.bbox import BoundingBox

from . import Source

LOG = logging.getLogger(__name__)


class MultiSource(Source):
    """Combine multiple sources into a single source.

    A MultiSource holds a flat list of sub-sources and behaves as their concatenation: iterating over it or
    indexing it yields the items of the sub-sources in order.

    Whether the sub-sources are actually merged into a single object is decided when :obj:`mutate` is called,
    and is controlled by the ``merger`` parameter. See :obj:`__init__` for details.

    Attributes
    ----------
    sources : list of :class:`Source`
        The flattened list of the mutated sub-sources. Nested MultiSources are expanded, so this list never
        contains a MultiSource itself.
    filter : object or None
        The filter passed to the constructor. Currently stored but not applied.
    merger : object, str, tuple, None or False
        The merger specification passed to the constructor — anything accepted as the ``merger`` argument
        of :func:`earthkit.data.mergers.make_merger` (never a :class:`Merger` instance itself), including
        the special values None (automatic merging) and False (no merging). When a merger has to be built,
        this attribute is replaced by the resulting :class:`Merger` object in :obj:`mutate`.
    """

    def __init__(self, *sources, filter=None, merger=None, **kwargs):
        """Initialize the MultiSource.

        Parameters
        ----------
        *sources
            The sources to combine. Either a single list of sources or the sources as positional arguments.
            Each item must be a :class:`Source`, an object with a ``_source`` attribute holding a
            :class:`Source`, or a callable returning a source. Callables are evaluated here, in parallel when
            there is more than one of them.
        filter : optional
            The filter to apply to the sources.
        merger : object, str, tuple, None, or False
            The merger to use for combining the sources. This is never a :class:`Merger` instance itself —
            it is any value accepted as the ``merger`` argument of :func:`earthkit.data.mergers.make_merger`,
            which is called to build the actual :class:`Merger` on demand. The values are interpreted as
            follows:

            - None (the default) requests automatic merging: when the MultiSource is mutated, it tries to
              merge the sources by their nearest common class. If that succeeds, the MultiSource mutates
              itself into the single merged object — e.g. when all the input files are of the same type.
              If it fails, no merger is built and the MultiSource remains a collection of its sources.
            - False disables merging entirely. It also means that sources which are otherwise ignored when
              a MultiSource is created — typically ones earthkit-data assigns an UnknownReader, e.g.
              unsupported file types — are included instead.
            - Any other value is passed to :func:`make_merger` to build a :class:`Merger` instance. Unlike
              the None case, this Merger is not used while mutating; it is only used later, lazily, when
              one of the conversion routines :obj:`to_fieldlist`, :obj:`to_xarray` or :obj:`to_pandas` is
              called.
        **kwargs
            Additional keyword arguments passed to :class:`Source`.

        Raises
        ------
        ValueError
            If an item in ``sources`` is neither a :class:`Source`, an object wrapping one, nor a callable.

        Examples
        --------
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

        Supply a custom merger as an object, implementing only the conversions it needs to support
        (``to_fieldlist``/``to_xarray``/``to_pandas``, each taking the merged paths-or-sources positionally
        plus any keyword arguments forwarded from the call site):

        >>> class MyMerger:
        ...     def to_xarray(self, paths_or_sources, **kwargs):
        ...         return xr.open_mfdataset(paths_or_sources, **kwargs)
        >>> ds = from_source("multi", [s1, s2], merger=MyMerger()).to_xarray()
        """
        super().__init__(**kwargs)
        if len(sources) == 1 and isinstance(sources[0], list):
            sources = sources[0]

        sources = self._from_sources(sources)

        for s in sources:
            print(f"1 {s} type={type(s)}")  # --- IGNORE ---

        # when merger is False, all sources are included without ignoring any of them
        if merger is False:
            self.sources = [s.mutate() for s in self._flatten(sources)]
        # otherwise, include all sources that are not ignored
        else:
            self.sources = [s.mutate() for s in self._flatten(sources) if not s.ignore()]

        for s in self.sources:
            print(f"2 {s} type={type(s)}")  # --- IGNORE ---

        self.filter = filter
        self.merger = merger
        self._lengths = [None] * len(self.sources)

    def _flatten(self, sources):
        """Recursively expand nested MultiSources into a flat iterator of leaf sources.

        Parameters
        ----------
        sources : iterable of :class:`Source`
            The sources to flatten.

        Yields
        ------
        :class:`Source`
            Each leaf source, i.e. a source that is not itself a MultiSource.
        """
        for s in sources:
            if isinstance(s, MultiSource):
                yield from self._flatten(s.sources)
            else:
                yield s

    def ignore(self):
        """Report whether this source should be ignored when building a parent MultiSource.

        Returns
        -------
        bool
            True if this MultiSource has no sub-sources left after filtering.
        """
        return len(self.sources) == 0

    def mutate(self):
        """Attempt to collapse this MultiSource into a simpler object.

        Depending on :obj:`merger` and the number of sub-sources, this either returns a single merged
        object, an :class:`EmptySource`, one of the sub-sources, or ``self`` unchanged when no merging is
        possible or requested.

        Returns
        -------
        :class:`Source`
            The mutated object, which may be ``self``.
        """
        print(f"MultiSource: mutate: {len(self.sources)} sources")  # --- IGNORE ---
        if len(self.sources) == 1:
            return self.sources[0].mutate()

        if len(self.sources) == 0:
            return EmptySource()

        # when merger is None, attempt to merge the sources using the default merger.
        if self.merger is None:
            print(f"MultiSource: trying to merge {len(self.sources)} sources")  # --- IGNORE ---
            try:
                merged = merge_by_class(self.sources)
                if merged is not None:
                    return merged.mutate()
            except Exception:
                pass

        # Otherwise, it will use the specified merger for merging the sources.
        elif self.merger is not False:
            self.merger = make_merger(self.merger, self.sources)

        print(f"MultiSource: could not merge {len(self.sources)} sources")  # --- IGNORE ---
        return self

    # def _set_dataset(self, dataset):
    #     super()._set_dataset(dataset)
    #     for s in self.sources:
    #         s._set_dataset(dataset)

    def __iter__(self):
        """Iterate over the items of all sub-sources, in order, as a single flat sequence."""
        return itertools.chain(*self.sources)

    def __getitem__(self, n):
        """Get the ``n``-th item across all sub-sources.

        Parameters
        ----------
        n : int
            The index of the item, treating the sub-sources as one concatenated sequence. Negative indices
            are supported and count from the end.

        Returns
        -------
        object
            The item at index ``n``, taken from the sub-source it falls into.
        """
        if n < 0:
            n = len(self) + n

        i = 0
        while n >= self._length(i):
            n -= self._length(i)
            i += 1
        return self.sources[i][n]

    def sel(self, *args, **kwargs):
        """Not implemented for MultiSource."""
        self._not_implemented()

    def order_by(self, *args, **kwargs):
        """Not implemented for MultiSource."""
        self._not_implemented()

    def metadata(self, *args, **kwargs):
        """Not implemented for MultiSource."""
        self._not_implemented()

    def __len__(self):
        """Return the total number of items across all sub-sources."""
        return sum(self._length(i) for i, _ in enumerate(self.sources))

    def _length(self, i):
        """Return the (cached) length of the ``i``-th sub-source.

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
        """Return a repr listing the reprs of all sub-sources."""
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

    def graph(self, depth=0):
        """Print a tree representation of this source and its sub-sources.

        Parameters
        ----------
        depth : int
            The current indentation level, in characters. Each sub-source is printed with an
            increased indentation.
        """
        print(" " * depth, self.__class__.__name__, self.merger)
        for s in self.sources:
            s.graph(depth + 3)

    def to_fieldlist(self, **kwargs):
        """Convert the sub-sources into a :class:`FieldList` using :obj:`merger`.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to the merger's ``to_fieldlist`` method.

        Returns
        -------
        :class:`FieldList`
        """
        return make_merger(self.merger, self.sources).to_fieldlist(**kwargs)

    def to_xarray(self, **kwargs):
        """Convert the sub-sources into an xarray object using :obj:`merger`.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to the merger's ``to_xarray`` method.

        Returns
        -------
        xarray.Dataset or xarray.DataArray
        """
        return make_merger(self.merger, self.sources).to_xarray(**kwargs)

    def to_pandas(self, **kwargs):
        """Convert the sub-sources into a pandas object using :obj:`merger`.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to the merger's ``to_pandas`` method.

        Returns
        -------
        pandas.DataFrame
        """
        return make_merger(self.merger, self.sources).to_pandas(**kwargs)

    def statistics(self, **kwargs):
        """Compute statistics over the sub-sources using :obj:`merger`.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to the merger's ``statistics`` method.

        Returns
        -------
        object
            The statistics, as returned by the merger.
        """
        return make_merger(self.merger, self.sources).statistics(**kwargs)

    def _from_sources(self, sources):
        """Resolve ``sources`` into a list of :class:`Source` instances.

        Items that are already a :class:`Source` (or wrap one in a ``_source`` attribute) are used as is.
        Callable items are called to produce a source; when there is more than one callable, they are
        evaluated concurrently using a thread pool, with the number of threads capped by the
        ``number-of-download-threads`` config setting.

        Parameters
        ----------
        sources : iterable
            The raw sources passed to :obj:`__init__`.

        Returns
        -------
        list of :class:`Source`

        Raises
        ------
        ValueError
            If an item is neither a :class:`Source`, an object wrapping one, nor a callable.
        """
        callables = []
        has_callables = False
        sources_in = sources
        sources = []
        for s in sources_in:
            if callable(s):
                has_callables = True
                callables.append(s)
                sources.append(s)
            else:
                if not isinstance(s, Source):
                    if hasattr(s, "_source"):
                        s = s._source
                    if s is None or not isinstance(s, Source):
                        raise ValueError(f"MultiSource: expected Source or callable, got {type(s)}")

                sources.append(s)
                callables.append(lambda *args, **kwargs: s)

        assert len(sources) == len(callables)

        if not has_callables:
            return sources

        from earthkit.data.core.config import CONFIG

        nthreads = min(CONFIG.get("number-of-download-threads"), len(callables))

        if nthreads < 2:
            return [s() for s in callables]

        def _call(s, *args, **kwargs):
            return s(*args, **kwargs)

        from earthkit.data.core.thread import SoftThreadPool
        from earthkit.data.utils.progbar import tqdm

        with SoftThreadPool(nthreads=nthreads) as pool:
            futures = [pool.submit(_call, s, observer=pool) for s in callables]
            iterator = (f.result() for f in futures)
            sources = list(tqdm(iterator, leave=False, total=len(futures)))

        return sources

    def datetime(self, **kwargs):
        """Return the combined datetime information of all sub-sources.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to each sub-source's ``datetime`` method.

        Returns
        -------
        dict
            Mapping of datetime kind (e.g. "base_time", "valid_time") to a sorted list of the values found
            across all sub-sources.
        """
        result = dict()
        for s in self.sources:
            result.update(s.datetime(**kwargs))
        return {k: sorted(v) for k, v in result.items()}

    def bounding_box(self):
        """Return the bounding box covering all sub-sources.

        Returns
        -------
        :class:`earthkit.data.utils.bbox.BoundingBox`
            The union of the bounding boxes of all sub-sources.
        """
        return BoundingBox.union([s.bounding_box() for s in self.sources])

    def to_data_object(self):
        """Convert this source into a :class:`MultiData` object.

        Returns
        -------
        :class:`earthkit.data.data.multi.MultiData`
        """
        from earthkit.data.data.multi import MultiData

        return MultiData(self)


source = MultiSource
