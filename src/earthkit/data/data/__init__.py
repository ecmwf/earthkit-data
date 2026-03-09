# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import abstractmethod
from typing import Any

from earthkit.data.core import Encodable


class Data(Encodable):
    _TYPE_NAME = None
    _FIELDLIST = "fieldlist"
    _XARRAY = "xarray"
    _PANDAS = "pandas"
    _GEOPANDAS = "geopandas"
    _FEATURELIST = "featurelist"
    _NUMPY = "numpy"
    _ARRAY = "array"
    _VALUE = "value"

    @property
    @abstractmethod
    def available_types(self):
        pass

    @abstractmethod
    def is_stream(self):
        pass

    @abstractmethod
    def describe(self):
        pass

    @abstractmethod
    def to(self, to_type: Any, *args, **kwargs):
        """Convert into another type"""
        pass

    @abstractmethod
    def to_fieldlist(self, *args, **kwargs):
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


class SimpleData(Data):
    @property
    def is_stream(self):
        return False

    def to(self, to_type, *args, **kwargs):
        """Convert into another type"""
        if isinstance(to_type, str):
            type_str = to_type.lower()
            method = getattr(self, f"to_{type_str}", None)
        else:
            from .wrappers import from_object

            data = from_object(to_type)
            type_str = data.available_types[0]
            method = getattr(data, f"to_{type_str}", None)

        if method is None:
            raise NotImplementedError(f"Conversion to {type_str} is not implemented")
        return method(*args, **kwargs)

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

    def to_values(self, *args, **kwargs):
        self._conversion_not_implemented()

    def to_target(self, target, *args, **kwargs):
        from earthkit.data.targets import to_target

        if "data" in kwargs:
            raise ValueError("Cannot specify data in to_target when calling to_target on a data  object")
        to_target(target, *args, data=self._to_default(), **kwargs)

    def _default_encoder(self):
        return self._reader._default_encoder()

    def _encode(self, *args, **kwargs):
        return self._to_default()._encode(*args, **kwargs)

    def _conversion_not_implemented(self):
        import inspect

        func = inspect.stack()[1][3]
        if func.startswith("to_"):
            func = func[3:]
            txt = f"Conversion of {self._TYPE_NAME} to {func} is not implemented"
        else:
            txt = f"Conversion of {self._TYPE_NAME} with {func} is not implemented"

        raise NotImplementedError(txt)

    def _to_default(self, *args, **kwargs):
        return self.to(self.available_types[0], *args, **kwargs)
