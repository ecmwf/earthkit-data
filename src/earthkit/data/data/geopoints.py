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
    columns and metadata. The blocks of a geopointset can be accessed individually through the
    featurelist (see :py:func:`to_featurelist`); they are stacked when the data is converted into
    pandas or xarray.

    When several geopoints files are read at once (a list, a glob, a folder, or the "multi"
    source), the result is one :py:class:`GeopointsData` whose ``path`` is a list. The files are
    stacked in order by :py:func:`to_pandas` and :py:func:`to_xarray`, and the featurelist holds
    the features of all the files in order. The same holds for the fieldlist.

    Geopoints data can be converted with the following methods:

    - :py:func:`to_pandas`
    - :py:func:`to_xarray`
    - :py:func:`to_featurelist`
    - :py:func:`to_fieldlist`

    """

    _TYPE_NAME = "Geopoints"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._PANDAS, self._XARRAY, self._FEATURELIST, self._FIELDLIST]

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
        if r.is_multi:
            n = r.num_blocks
            return (
                f"Geopoints files ({r.num_files} files, {n} block{'s' if n != 1 else ''}"
                f"{', format: ' + formats if formats else ''})"
            )
        if r.is_set:
            n = r.num_blocks
            if n == 0:
                return "Geopointset file (0 blocks)"
            return f"Geopointset file ({n} block{'s' if n != 1 else ''}, format: {formats})"
        return f"Geopoints file (format: {formats})"

    def __repr__(self) -> str:
        r = self._reader
        formats = ",".join(r.formats)
        s = f"GeopointsData(path={self.path}, "
        if r.is_multi:
            s += f"files={r.num_files}, "
        s += f"blocks={r.num_blocks}"
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

    def to_featurelist(self, mode="block"):
        """Convert into a FeatureList.

        Parameters
        ----------
        mode: str
            - "block" (default): one feature per geopoints block. The metadata of a feature is the
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
            The features of the geopoints data: a
            :py:class:`earthkit.data.readers.geopoints.featurelist.GeopointsFeatureList` for "block"
            and a :py:class:`earthkit.data.readers.geopoints.featurelist.GeopointsRowFeatureList` for
            "row". A geopointset without blocks gives an empty list.
        """
        return self._reader.to_featurelist(mode=mode)

    def to_fieldlist(self, mode="block", group_by=None):
        """Convert into a FieldList of point fields.

        Parameters
        ----------
        mode: str
            - "block" (default): one field per geopoints block and value column. The values,
              latitudes and longitudes of a field are the rows of the block; the time and the
              level are taken from the first row of the block.
            - "group": each block is split into groups of rows that share the same date/time and
              level (or the same values in the ``group_by`` columns). There is one field per group
              and value column, with the rows of the group as values, latitudes and longitudes. The
              groups are in order of first appearance in the block, and the time and the level of a
              field are taken from the first row of its group. Rows with a missing (NaT/NaN) key
              form a group of their own, whose field has no time or no level. A block without
              grouping columns is one group, so it gives the same fields as mode "block".

            Any other mode raises ValueError.
        group_by: list of str, optional
            Only for mode "group" (ValueError with "block"): the columns of the block whose values
            define the groups, instead of the default ``date`` and ``level`` columns (those that
            exist). Any column can be used, e.g. ``["stnid"]`` or ``["elevation"]``; a single name
            is accepted, too. The values of the keys other than ``date`` and ``level`` become labels
            of the fields (e.g. ``labels.stnid``). An empty list means no grouping: one group per
            block. A column the block does not have raises ValueError.

        Returns
        -------
        :py:class:`earthkit.data.indexing.simple.SimpleFieldList`
            The fields of the geopoints data in order (block, then group, then value column). The
            value columns are ``value``
            (traditional and XYV), ``x-comp`` and ``y-comp`` (XY_VECTOR), ``magnitude`` and
            ``angle`` (POLAR_VECTOR) and the non-coordinate columns of NCOLS. A block without rows
            and a non-numeric value column give no field. The ``#METADATA`` pairs of the block are
            the labels of its fields.

        Notes
        -----
        The valid time of a field is the date/time of the first row of the block (or of the group
        in mode "group"). If the
        ``#METADATA`` has a ``step``, the base time is the valid time minus the step, otherwise the
        step is 0. A block without ``date`` column uses the ``#METADATA`` ``date`` (YYYYMMDD) and
        ``time`` (HHMM), if present. The level is the ``level`` of the first row, or the
        ``#METADATA`` ``level``. ``#METADATA`` ``param`` (or ``shortName``), ``units`` and
        ``levtype`` (or ``level_type``, ``typeOfLevel``) give ``parameter.variable``,
        ``parameter.units`` and ``vertical.level_type``.
        """
        return self._reader.to_fieldlist(mode=mode, group_by=group_by)
