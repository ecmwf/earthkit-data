# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .source import SourceData


class NetCDFData(SourceData):
    _TYPE_NAME = "NetCDF"

    @property
    def available_types(self):
        return [self._XARRAY, self._PANDAS, self._FIELDLIST, self._NUMPY, self._ARRAY]

    def describe(self):
        pass

    def to_fieldlist(self, *args, **kwargs):
        """Convert into a field list"""
        return self._reader.to_fieldlist(*args, **kwargs)

    def to_xarray(self, *args, **kwargs):
        """Convert into an xarray dataset"""
        return self._reader.to_xarray(*args, **kwargs)

    def to_pandas(self, *args, **kwargs):
        """Convert into a pandas dataframe"""
        pass

    def to_numpy(self, *args, **kwargs):
        """Convert into a numpy array"""
        return self._reader.to_numpy(*args, **kwargs)

    def to_array(self, *args, **kwargs):
        """Convert into an array (other than numpy)"""
        return self._reader.to_array(*args, **kwargs)

    def _default_encoder(self):
        return self._source._default_encoder()
