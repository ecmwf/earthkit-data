# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import typing
from abc import abstractmethod

from earthkit.data.core import Base


class Data(Base):
    _TYPE_NAME = None
    _FIELDLIST = "fieldlist"
    _XARRAY = "xarray"
    _PANDAS = "pandas"
    _GEOPANDAS = "geopandas"
    _GEOJSON = "geojson"
    _FEATURELIST = "featurelist"
    _NUMPY = "numpy"
    _ARRAY = "array"

    @property
    @abstractmethod
    def available_types(self):
        pass

    @abstractmethod
    def describe():
        pass

    def to(self, target_type, *args, **kwargs):
        """Convert into another type"""
        method = getattr(self, f"to_{target_type}", None)
        if method is None:
            raise NotImplementedError(f"Conversion to {target_type} is not implemented")
        return method(*args, **kwargs)

    @abstractmethod
    def to_fieldlist(self, *args, **kwargs) -> typing.Any:
        pass

    @abstractmethod
    def to_xarray(self, *args, **kwargs):
        """Convert into an xarray dataset"""
        pass

    @abstractmethod
    def to_pandas(self, *args, **kwargs):
        """Convert into a pandas dataframe"""
        pass

    @abstractmethod
    def to_geopandas(self, **kwargs):
        """Convert into a GeoPandas dataframe"""
        pass

    @abstractmethod
    def to_geojson(self, **kwargs):
        """Convert into a GeoJSON object"""
        pass

    @abstractmethod
    def to_featurelist(self, *args, **kwargs):
        """Convert into a list of feature messages"""
        pass

    @abstractmethod
    def to_numpy(self, *args, **kwargs):
        """Convert into a numpy array"""
        pass

    @abstractmethod
    def to_array(self, *args, **kwargs):
        """Convert into an array (numpy or xarray)"""
        pass

    def _conversion_not_implemented(self):
        import inspect

        func = inspect.stack()[1][3]
        if func.startswith("to_"):
            func = func[3:]
            txt = f"Conversion of {self._TYPE_NAME} to {func} is not implemented"
        else:
            txt = f"Conversion of {self._TYPE_NAME} with {func} is not implemented"

        raise NotImplementedError(txt)


class SimpleData(Data):
    def __init__(self, reader):
        self._reader = reader

    def to_fieldlist(self, *args, **kwargs):
        self._conversion_not_implemented()

    def to_xarray(self, *args, **kwargs):
        self._conversion_not_implemented()

    def to_pandas(self, *args, **kwargs):
        self._conversion_not_implemented()

    def to_geopandas(self, **kwargs):
        self._conversion_not_implemented()

    def to_geojson(self, **kwargs):
        self._conversion_not_implemented()

    def to_featurelist(self, *args, **kwargs):
        self._conversion_not_implemented()

    def to_numpy(self, *args, **kwargs):
        self._conversion_not_implemented()

    def to_array(self, *args, **kwargs):
        self._conversion_not_implemented()
