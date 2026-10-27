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

from .. import Reader

LOG = logging.getLogger(__name__)


class GeopointsReader(Reader):
    """Reader for Metview geopoints (``#GEO``) and geopointset (``#GEOPOINTSET``) files.

    The file is parsed once, on first use, and the result is cached.
    """

    _format = "geopoints"
    _binary = False
    _appendable = False

    def __init__(self, source, path, **kwargs):
        if kwargs:
            names = ", ".join(repr(name) for name in kwargs)
            warnings.warn(
                f"Arguments {names} have no effect for the geopoints reader.",
                UserWarning,
                stacklevel=2,
            )

        super().__init__(source, path)
        self._parsed = None

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

    def to_data_object(self):
        from earthkit.data.data.geopoints import GeopointsData

        return GeopointsData(self)

    def _encode_default(self, encoder, *args, **kwargs):
        return None
