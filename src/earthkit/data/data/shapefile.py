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
    pass  # type: ignore[import]


class ShapeFileData(SourceData):
    """Represent Shapefile data.

    Shapefile is a popular geospatial vector data format for geographic information
    system (GIS) software. This class provides methods to convert Shapefile data into various formats such as
    geopandas GeoDataFrames and Xarray datasets

    Shapefile data can be converted with the following methods:

    - :py:func:`to_geopandas`
    - :py:func:`to_pandas`
    - :py:func:`to_xarray`
    - :py:func:`to_featurelist`

    """

    _TYPE_NAME = "Shapefile"

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._GEOPANDAS, self._PANDAS, self._XARRAY, self._NUMPY, self._FEATURELIST]

    def describe(self) -> Any:
        """Provide a description of the Shapefile data.

        Returns
        -------
        :py:class:`earthkit.data.utils.summary.DataDescriber`
            A DataDescriber object containing a description of the Shapefile data.
        """
        from earthkit.data.utils.summary import DataDescriber

        return DataDescriber(title="Shapefile", path=self._reader.path, types=self.available_types)

    def __repr__(self) -> str:
        return f"ShapeFileData(path={self._reader.path})"

    def _repr_html_(self) -> str:
        return self.describe()._repr_html_()

    def to_pandas(self, **kwargs):
        """Convert into an geopandas GeoDataFrame.

        This conversion is the same as :func:`to_geopandas` and is
        provided for convenience.

        See Also
        --------
        :func:`to_geopandas`
        """
        return self._reader.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
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
            An Xarray dataset containing the Shapefile data.
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
            A GeoPandas GeoDataFrame containing the Shapefile data.
        """
        return self._reader.to_geopandas(**kwargs)

    def to_numpy(self, flatten=False):
        """Convert into a NumPy array.

        The conversion is done by converting into a geopandas GeoDataFrame first and then using
        :py:func:`geopandas.GeoDataFrame.to_numpy`.

        Parameters
        ----------
        flatten: bool, optional
            Whether to flatten the resulting NumPy array. If True, the resulting array will be 1D.
            Default is False.

        Returns
        -------
        :py:class:`numpy.ndarray`
            A NumPy array containing the Shapefile data.
        """
        return self._reader.to_numpy(flatten=flatten)

    def to_featurelist(self):
        """Convert into a FeatureList.

        Returns
        -------
        :py:class:`earthkit.data.readers.shapefile.file.ShapeFileList`
            A ShapeFileList containing the Shapefile data.
        """
        from earthkit.data.readers.shapefile.file import ShapeFileList

        return ShapeFileList(self._reader.path)
