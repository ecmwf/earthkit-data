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
    import xarray  # type: ignore[import]


class GeoJsonData(SourceData):
    """Represent GeoJSON data.

    GeoJSON is a format for encoding a variety of geographic data structures using JSON. This class provides
    methods to convert GeoJSON data into various formats such as geopandas GeoDataFrames and Xarray datasets.

    GeoJSON data can be converted with the following methods:

    - :py:func:`to_geopandas`
    - :py:func:`to_pandas`
    - :py:func:`to_xarray`
    - :py:func:`to_featurelist`

    """

    _TYPE_NAME = "GeoJSON"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._GEOPANDAS, self._PANDAS, self._XARRAY, self._FEATURELIST]

    def describe(self) -> Any:
        """Provide a description of the GeoJSON data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the GeoJSON data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="GeoJSON file", path=self._reader.path, types=self.available_types)

    def __repr__(self) -> str:
        return f"GeoJSONData(path={self._reader.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_pandas(self, **kwargs) -> "pandas.DataFrame":
        """Convert into an geopandas GeoDataFrame.

        This conversion is the same as :func:`to_geopandas` and is
        provided for convenience.

        See Also
        --------
        :func:`to_geopandas`
        """
        return self._reader.to_pandas(**kwargs)

    def to_xarray(self, **kwargs) -> "xarray.Dataset":
        """Convert into an Xarray dataset.

        The conversion is done by converting into a geopandas
        GeoDataFrame first and then using :py:func:`pandas.to_xarray`.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to :func:`geopandas.read_file`.

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing the GeoJSON data.
        """
        return self._reader.to_xarray(**kwargs)

    def to_geopandas(self, **kwargs):
        """Convert into an geopandas GeoDataFrame.

        The conversion is done by using :py:func:`geopandas.read_file`.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to :py:func:`geopandas.read_file`.

        Returns
        -------
        :py:class:`geopandas.GeoDataFrame`
            A GeoPandas GeoDataFrame containing the GeoJSON data.
        """
        return self._reader.to_geopandas(**kwargs)

    def to_featurelist(self):
        """Convert into a FeatureList.

        Returns
        -------
        :py:class:`earthkit.data.readers.geojson.file.GeoJsonList`
            A GeoJsonList containing the GeoJSON data.
        """
        from earthkit.data.readers.geojson.file import GeoJsonList

        return GeoJsonList(self._reader.path)
