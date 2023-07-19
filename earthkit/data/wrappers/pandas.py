# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


from earthkit.data.wrappers import Wrapper


class PandasSeriesWrapper(Wrapper):
    """Wrapper around a `pandas.DataFrame`, offering polymorphism and
    convenience methods.
    """

    def __init__(self, data):
        self.data = data
    
    def __iter__(self):
        return iter(self.data)

    def to_pandas(self):
        """
        Return a `pandas.Series` representation of the data.

        Returns
        -------
        pandas.Series
        """
        return self.data
   
    def to_numpy(self, **kwargs):
        """
        Return a `numpy.array` representation of the data.

        Returns
        -------
        numpy.array
        """
        return self.data.to_numpy(**kwargs) 
    
    def to_xarray(self, **kwargs):
        """
        Return a `xarray.DataArray` representation of the data.

        Returns
        -------
        numpy.array
        """
        return self.data.to_xarray(**kwargs)
    
    def to_netcdf(self, *args, **kwargs):
        """
        Return a `xarray.DataArray` representation of the data.

        Returns
        -------
        numpy.array
        """
        return self.data.to_xarray().to_netcdf(*args, **kwargs)

    def describe(self):
        """
        A pandas is tabular, therefore return itself

        Returns
        -------
        numpy.array
        """
        return self.data

class PandasDataFrameWrapper(PandasSeriesWrapper):
    """Wrapper around a `pandas.DataFrame`, offering polymorphism and
    convenience methods.
    """

    def __init__(self, data):
        self.data = data

    def to_pandas(self):
        """
        Return a `pandas.DataFrame` representation of the data.

        Returns
        -------
        pandas.DataFrame
        """
        return self.data

    def to_xarray(self, **kwargs):
        """
        Return a `xarray.Dataset` representation of the data.

        Returns
        -------
        numpy.array
        """
        return self.data.to_xarray(**kwargs) 


class GeoPandasDataFrameWrapper(PandasDataFrameWrapper):
    """Wrapper around a `geopandas.DataFrame`, offering polymorphism and
    convenience methods.

    Key difference to a pandas dataframe wrapper, we iterate of rows (features) not coloums
    """

    def __init__(self, data):
        self.data = data


def wrapper(data, *args, **kwargs):
    import pandas as pd

    try:
        import geopandas as gpd
        l_gpd = True
    except ImportError:
        l_gpd = False    

    if l_gpd and isinstance(data, gpd.geodataframe.GeoDataFrame):
        return GeoPandasDataFrameWrapper(data, *args, **kwargs)
    if isinstance(data, pd.DataFrame):
        return PandasDataFrameWrapper(data, *args, **kwargs)
    elif isinstance(data, pd.Series):
        return PandasSeriesWrapper(data, *args, **kwargs)

    return None
