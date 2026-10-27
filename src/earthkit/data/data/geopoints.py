# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from __future__ import annotations

from typing import (
    TYPE_CHECKING,
    Any,  # noqa: F401
)

from .source import SourceData

if TYPE_CHECKING:
    import pandas  # type: ignore[import]


class GeopointsData(SourceData):
    """Represent data in the Metview geopoints or geopointset format.

    A geopoints file (starting with ``#GEO``) has one block of points. A geopointset file
    (starting with ``#GEOPOINTSET``) holds any number of such blocks, each with its own format,
    columns and metadata. The blocks of a geopointset are not accessible individually; they are
    stacked when the data is converted.

    Geopoints data can be converted with the following methods:

    - :py:func:`to_pandas`
    - :py:func:`to_xarray`

    """

    _TYPE_NAME = "Geopoints"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._PANDAS, self._XARRAY]

    def describe(self) -> Any:
        """Provide a description of the geopoints data.

        The title tells whether the data is a geopoints file or a geopointset, and gives the
        format(s) and, for a geopointset, the number of blocks.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the geopoints data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title=self._title(), path=self.path, types=self.available_types)

    def _title(self) -> str:
        r = self._reader
        formats = ", ".join(r.formats)
        if r.is_set:
            n = r.num_blocks
            if n == 0:
                return "Geopointset file (0 blocks)"
            return f"Geopointset file ({n} block{'s' if n != 1 else ''}, format: {formats})"
        return f"Geopoints file (format: {formats})"

    def __repr__(self) -> str:
        r = self._reader
        formats = ",".join(r.formats)
        s = f"GeopointsData(path={self.path}, blocks={r.num_blocks}"
        if formats:
            s += f", format={formats}"
        return s + ")"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_pandas(self) -> "pandas.DataFrame":
        """Convert into a Pandas DataFrame.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A Pandas DataFrame with one row per point. For a geopointset all the blocks are
            stacked (the index is reset) and columns missing in a block are filled with NaN. An
            empty geopointset gives an empty DataFrame.
        """
        return self._reader.to_pandas()

    def to_xarray(self, **kwargs):
        """Convert into an Xarray dataset.

        First, the data is converted into a :py:class:`pandas.DataFrame` with :py:func:`to_pandas`,
        then :py:meth:`pandas.DataFrame.to_xarray` is called to generate the xarray object.

        Parameters
        ----------
        **kwargs
            Keyword arguments passed to :py:meth:`pandas.DataFrame.to_xarray`.

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing the geopoints data.
        """
        return self._reader.to_xarray(**kwargs)
