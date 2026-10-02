# (C) Copyright 2026 ECMWF.
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
    import geopandas  # type: ignore[import]
    import pandas  # type: ignore[import]


class SQLData(SourceData):
    """Represent SQL data.

    The data is either an SQLite/GeoPackage file or the result of a query from the
    :ref:`data-sources-sql` source.

    SQL data can be converted with the following methods:

    - :py:func:`to_pandas`
    - :py:func:`to_geopandas`

    """

    _TYPE_NAME = "SQL"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._PANDAS, self._GEOPANDAS]

    def describe(self) -> Any:
        """Provide a description of the SQL data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the SQL data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="SQL", path=self.path, types=self.available_types)

    @property
    def path(self) -> str:
        """str: The path of the file, or the database url with the password masked."""
        from earthkit.data.sources.sql import SQLSource

        if isinstance(self._source, SQLSource):
            return self._source.masked_url
        return self._reader.path

    def __repr__(self) -> str:
        return f"SQLData(path={self.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_pandas(self, **kwargs) -> "pandas.DataFrame":
        """Convert into a Pandas DataFrame.

        Parameters
        ----------
        **kwargs
            For an SQLite file, ``table`` selects the table to read; it can be omitted
            when the file contains a single table. The other keyword arguments are passed to
            :py:func:`pandas.read_sql_query`. For the :ref:`data-sources-sql` source, all
            keyword arguments are passed to :py:func:`pandas.read_sql_query`. ``chunksize`` is not supported.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A Pandas DataFrame containing the SQL data.
        """
        if "chunksize" in kwargs:
            raise ValueError("chunksize is not supported")
        return self._reader.to_pandas(**kwargs)

    def to_geopandas(self, **kwargs) -> "geopandas.GeoDataFrame":
        """Convert into a GeoPandas GeoDataFrame.

        Parameters
        ----------
        **kwargs
            For a GeoPackage/SQLite file, ``table`` selects the layer to read. The other
            keyword arguments are passed to :py:func:`geopandas.read_file`. For the
            :ref:`data-sources-sql` source, ``geom_col`` (default ``"geom"``) names the geometry
            column, which must be in WKB format. The other keyword arguments are passed to
            :py:func:`geopandas.read_postgis`. ``chunksize`` is not supported.

        Returns
        -------
        :py:class:`geopandas.GeoDataFrame`
            A GeoPandas GeoDataFrame containing the SQL data.
        """
        if "chunksize" in kwargs:
            raise ValueError("chunksize is not supported")
        return self._reader.to_geopandas(**kwargs)
