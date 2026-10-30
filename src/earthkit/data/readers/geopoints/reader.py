# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import warnings

from earthkit.data.sources import Source

from .. import Reader

LOG = logging.getLogger(__name__)


class GeopointsReaderBase(Source):
    """Common base of :class:`GeopointsReader` and :class:`MultiGeopointsReader`.

    It defines :meth:`merge`, which is looked up on the nearest common class of the sources when
    several of them are merged, so that single and multi-file readers can be combined in any
    order.
    """

    @classmethod
    def merge(cls, sources):
        """Merge geopoints readers into one :class:`MultiGeopointsReader`.

        Parameters
        ----------
        sources: list
            Single (:class:`GeopointsReader`) and multi-file (:class:`MultiGeopointsReader`)
            readers, in any order. The files are flattened in order. Sources whose ``ignore()`` is
            True are skipped.

        Raises
        ------
        ValueError
            When a source is not a geopoints reader (and not ignored) or when there is nothing to
            merge.
        """
        r = []
        for source in sources:
            if isinstance(source, MultiGeopointsReader):
                r.extend(source.sources)
            elif isinstance(source, GeopointsReader):
                r.append(source)
            elif not source.ignore():
                raise ValueError(f"Cannot merge source of type {type(source)} in GeopointsReader.merge")

        if not r:
            raise ValueError("No geopoints reader found in sources to merge")

        return MultiGeopointsReader(r)


class GeopointsReader(GeopointsReaderBase, Reader):
    """Reader for Metview geopoints (``#GEO``) and geopointset (``#GEOPOINTSET``) files.

    The file is parsed once, on first use, and the result is cached.
    """

    _format = "geopoints"
    _binary = False
    _appendable = False

    is_multi = False

    def __init__(self, source, path, **kwargs):
        if kwargs:
            names = ", ".join(repr(name) for name in kwargs)
            warnings.warn(
                f"Arguments {names} have no effect for the geopoints reader.",
                UserWarning,
                stacklevel=2,
            )

        # The reader is a source itself. Keep the originating source alive, since the reader only
        # holds a weak reference to it.
        self._ori_source = source
        Source.__init__(self)
        Reader.__init__(self, source, path)
        self._parsed = None

    def mutate_source(self):
        # A GeopointsReader is a source itself
        return self

    def _cache_file(self, *args, **kwargs):
        return Reader._cache_file(self, *args, **kwargs)

    @property
    def num_files(self):
        """int: The number of files (always 1 for a single reader)."""
        return 1

    @property
    def parsed(self):
        """:class:`earthkit.data.readers.geopoints.parser.GeopointsFile`: The parsed file (cached)."""
        if self._parsed is None:
            from .parser import parse_geopoints

            LOG.debug("Parsing geopoints file %s", self.path)
            self._parsed = parse_geopoints(self.path)
        return self._parsed

    @property
    def blocks(self):
        """list: The geopoints blocks of the file."""
        return list(self.parsed.blocks)

    @property
    def num_blocks(self):
        """int: The number of blocks (1 for a geopoints file, 0 or more for a geopointset)."""
        return len(self.parsed.blocks)

    @property
    def is_set(self):
        """bool: True for a ``#GEOPOINTSET`` file."""
        return self.parsed.is_set

    @property
    def formats(self):
        """The distinct formats (list of str) of the blocks, in order of appearance."""
        return list(dict.fromkeys(b.format for b in self.blocks))

    def to_pandas(self):
        """Convert the blocks into a :py:class:`pandas.DataFrame`.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            For a geopointset all the blocks are stacked (``ignore_index=True``). Columns missing
            in a block are filled with NaN. A geopointset without blocks gives an empty DataFrame.
        """
        import pandas

        frames = [b.to_pandas() for b in self.blocks]
        if not frames:
            return pandas.DataFrame()
        if len(frames) == 1:
            return frames[0]
        return pandas.concat(frames, ignore_index=True)

    def to_xarray(self, **kwargs):
        """Convert the blocks into an xarray object.

        First the data is converted into a :py:class:`pandas.DataFrame` with :meth:`to_pandas`,
        then :py:meth:`pandas.DataFrame.to_xarray` is called.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to :py:meth:`pandas.DataFrame.to_xarray`.

        Returns
        -------
        :py:class:`xarray.Dataset`
        """
        return self.to_pandas().to_xarray(**kwargs)

    def to_featurelist(self, mode="block"):
        """Convert into a featurelist.

        Parameters
        ----------
        mode: str
            - "block" (default): one feature per geopoints block, i.e. one for a ``#GEO`` file and
              one for each member of a ``#GEOPOINTSET``. The metadata of a feature is the
              ``#METADATA`` section of its block.
            - "row": one feature per data row of all the blocks, in file order. The metadata of a
              feature is the ``#METADATA`` section of its block plus the columns of the row
              (``latitude``, ``longitude``, ``level``, ``date``, ``value``, ``stnid``, ...); the
              value of the row wins when a name is in both. The features are created when they
              are accessed, so the list is cheap to create even for a large file. Blocks without
              rows add no feature.

            Any other mode raises ValueError.

        Returns
        -------
        GeopointsFeatureList, GeopointsRowFeatureList
            A :class:`~earthkit.data.readers.geopoints.featurelist.GeopointsFeatureList` for "block"
            and a :class:`~earthkit.data.readers.geopoints.featurelist.GeopointsRowFeatureList` for
            "row". A geopointset without blocks gives an empty list.
        """
        from .featurelist import make_featurelist

        return make_featurelist(self.blocks, mode=mode)

    def to_data_object(self):
        from earthkit.data.data.geopoints import GeopointsData

        return GeopointsData(self)

    def _encode_default(self, encoder, *args, **kwargs):
        return None


class MultiGeopointsReader(GeopointsReaderBase):
    """Several geopoints files seen as one.

    It is built by :meth:`GeopointsReaderBase.merge`, e.g. when a list, a glob or a folder of
    geopoints files is read. The blocks of all the files are kept in the order of the files.
    """

    is_multi = True

    def __init__(self, sources):
        super().__init__()
        self.sources = list(self._flatten(sources))

    @staticmethod
    def _flatten(sources):
        for s in sources:
            if isinstance(s, MultiGeopointsReader):
                yield from s.sources
            else:
                yield s

    @property
    def path(self):
        """list[str]: The paths of the files, in order."""
        return [s.path for s in self.sources]

    @property
    def num_files(self):
        """int: The number of files."""
        return len(self.sources)

    @property
    def blocks(self):
        """list: The geopoints blocks of all the files, in order."""
        return [b for s in self.sources for b in s.blocks]

    @property
    def num_blocks(self):
        """int: The total number of blocks."""
        return sum(s.num_blocks for s in self.sources)

    @property
    def formats(self):
        """The distinct formats (list of str) of the blocks of all the files, in order of appearance."""
        return list(dict.fromkeys(f for s in self.sources for f in s.formats))

    def to_pandas(self):
        """Stack the data of all the files into a :py:class:`pandas.DataFrame`.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            The data of the files, in order, stacked with ``ignore_index=True``. Columns missing in
            some files are filled with NaN. Files without any column (an empty geopointset) are
            skipped.
        """
        import pandas

        frames = [s.to_pandas() for s in self.sources]
        frames = [f for f in frames if len(f.columns) > 0]
        if not frames:
            return pandas.DataFrame()
        return pandas.concat(frames, ignore_index=True)

    def to_xarray(self, **kwargs):
        """Convert the data of all the files into an xarray object.

        The data is first converted with :meth:`to_pandas`, then
        :py:meth:`pandas.DataFrame.to_xarray` is called.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to :py:meth:`pandas.DataFrame.to_xarray`.

        Returns
        -------
        :py:class:`xarray.Dataset`
        """
        return self.to_pandas().to_xarray(**kwargs)

    def to_featurelist(self, mode="block"):
        """Convert into a featurelist holding the features of all the files in order.

        Parameters
        ----------
        mode: str
            "block" (default) or "row". See :meth:`GeopointsReader.to_featurelist`.
        """
        from .featurelist import make_featurelist

        return make_featurelist(self.blocks, mode=mode)

    def to_data_object(self):
        from earthkit.data.data.geopoints import GeopointsData

        return GeopointsData(self)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.sources})"

    def _encode(self, encoder, hints=None, **kwargs):
        return self._encode_default(encoder, hints=hints, **kwargs)

    def _encode_default(self, encoder, *args, **kwargs):
        return None
