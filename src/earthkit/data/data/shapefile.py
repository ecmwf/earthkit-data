# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from . import SimpleData


class ShapeFileData(SimpleData):
    _TYPE_NAME = "Shapefile"

    def __init__(self, reader):
        """Initialize a ShapeFileData object with a reader.

        Parameters
        ----------
        reader : ShapeFileReader
            The reader object that provides access to the Shapefile data.
        """
        self._reader = reader

    @property
    def available_types(self):
        """list[str]: Return the list of available types that this data object can be converted to."""
        return [self._GEOPANDAS, self._PANDAS, self._XARRAY, self._GEOJSON]

    def describe(self):
        """Provide a description of the Shapefile data.

        Returns
        -------
        str
            A description of the Shapefile data including the file path.
        """
        return f"GeoJSON data from {self._reader.path}"

    def to_pandas(self, **kwargs):
        """Convert into a Pandas DataFrame.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to the reader's to_pandas method.

        Returns
        -------
        :py:class:`pandas.DataFrame`
            A Pandas DataFrame containing the Shapefile data.
        """
        return self._reader.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        """Convert into an Xarray dataset.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to the reader's to_xarray method.

        Returns
        -------
        :py:class:`xarray.Dataset`
            An Xarray dataset containing the Shapefile data.
        """
        return self._reader.to_xarray(**kwargs)

    def to_geopandas(self, **kwargs):
        """Convert into a GeoPandas GeoDataFrame.

        Parameters
        ----------
        **kwargs
            Keyword arguments to pass to the reader's to_geopandas method.

        Returns
        -------
        :py:class:`geopandas.GeoDataFrame`
            A GeoPandas GeoDataFrame containing the Shapefile data.
        """
        return self._reader.to_geopandas(**kwargs)

    def to_featurelist(self, *args, **kwargs):
        """Convert into a FeatureList.

        Parameters
        ----------
        *args
            Positional arguments (unused).
        **kwargs
            Keyword arguments (unused).

        Returns
        -------
        ShapeFileList
            A ShapeFileList containing the Shapefile data.
        """
        from earthkit.data.readers.shapefile.file import ShapeFileList

        return ShapeFileList(self._reader.path)
