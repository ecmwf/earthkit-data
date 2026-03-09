# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging

from . import ObjectWrapperData

logger = logging.getLogger(__name__)


class PandasSeriesData(ObjectWrapperData):
    _TYPE_NAME = "pandas.Series"

    @property
    def available_types(self):
        return [self._PANDAS, self._XARRAY, self._NUMPY]

    def describe():
        pass

    def to_xarray(self, *args, **kwargs):
        return self._data.to_xarray(**kwargs)

    def to_pandas(self, *args, **kwargs):
        """Return a pandas `series` representation of the data.

        Returns
        -------
        pandas.core.series.Series
        """
        return self._data

    def to_numpy(self, **kwargs):
        """
        Return a `numpy.array` representation of the data.

        Returns
        -------
        numpy.array
        """
        return self._data.to_numpy(**kwargs)


class PandasDataFrameData(PandasSeriesData):
    _TYPE_NAME = "pandas.DataFrame"

    def describe():
        pass

    def to_pandas(self, *args, **kwargs):
        """Return a pandas `dataframe` representation of the data.

        Returns
        -------
        pandas.core.frame.DataFrame
        """
        return self._data


class GeoPandasDataFrameData(ObjectWrapperData):
    _TYPE_NAME = "geopandas.GeoDataFrame"

    @property
    def available_types(self):
        return [self._GEOPANDAS, self._PANDAS, self._XARRAY]

    def describe():
        pass

    def to_xarray(self, *args, **kwargs):
        return self._data.to_xarray(**kwargs)

    def to_pandas(self, *args, **kwargs):
        """Return a pandas `dataframe` representation of the data.

        Returns
        -------
        pandas.core.frame.DataFrame
        """
        return self._data

    def to_geopandas(self, **kwargs):
        return self._data

    def to_featurelist(self, *args, **kwargs):
        from earthkit.data.readers.geojson.file import GeoPandasList

        return GeoPandasList(self._data)

    def to_numpy(self, **kwargs):
        """
        Return a `numpy.array` representation of the data.

        Returns
        -------
        numpy.array
        """
        return self._data.to_numpy(**kwargs)


def wrapper(data, *args, **kwargs):
    from earthkit.data.utils import is_module_loaded

    if not is_module_loaded("pandas"):
        return None

    import pandas as pd

    if is_module_loaded("geopandas"):
        import geopandas as gpd

        if isinstance(data, gpd.geodataframe.GeoDataFrame):
            return GeoPandasDataFrameData(data, *args, **kwargs)

    if isinstance(data, pd.DataFrame):
        return PandasDataFrameData(data, *args, **kwargs)
    if isinstance(data, pd.Series):
        return PandasSeriesData(data, *args, **kwargs)

    return None
