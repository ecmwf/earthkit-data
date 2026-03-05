# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.data import SimpleData
from earthkit.data.readers.netcdf.fieldlist import NetCDFFieldListFromFile


class NetCDFData(SimpleData):
    def __init__(self, reader, *args, **kwargs):
        self._reader = reader

    @property
    def available_types(self):
        return ["xarray", "pandas", "fieldlist", "numpy", "array"]

    def describe(self):
        pass

    def to_fieldlist(self):
        """Convert into a field list"""
        return NetCDFFieldListFromFile(self._reader._ori_source, self._reader.path)

    def to_xarray(self, *args, **kwargs):
        """Convert into an xarray dataset"""
        return type(self)._to_xarray_multi_from_paths([self._path], **kwargs)

    def to_pandas(self, *args, **kwargs):
        """Convert into a pandas dataframe"""
        pass

    def to_geopandas(self, *args, **kwargs):
        raise NotImplementedError("Conversion of GRIB data to geopandas is not implemented")

    def to_numpy(self, *args, **kwargs):
        """Convert into a numpy array"""
        self._reader.to_numpy(*args, **kwargs)

    def to_array(self, *args, **kwargs):
        """Convert into an array (other than numpy)"""
        self._reader.to_array(*args, **kwargs)

    def to_featurelist(self, *args, **kwargs):
        """Convert into a list of bufr messages"""
        raise NotImplementedError("Conversion of NetCDF data to bufr is not implemented")

    @classmethod
    def _to_xarray_multi_from_paths(cls, paths, **kwargs):
        import xarray as xr

        options = dict()
        options.update(kwargs.get("xarray_open_mfdataset_kwargs", {}))
        if not options:
            options = dict(**kwargs)

        return xr.open_mfdataset(
            paths,
            **options,
        )
