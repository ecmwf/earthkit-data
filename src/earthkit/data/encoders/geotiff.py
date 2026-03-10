# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data import from_object

from . import EncodedData
from . import Encoder
from . import FilePathEncodedData

LOG = logging.getLogger(__name__)


class GeoTIFFEncodedData(EncodedData):
    _GDAL_DRIVER = "GTiff"

    def __init__(self, ds):
        self.ds = ds

    def to_bytes(self, **kwargs):
        import rasterio.io

        m = rasterio.io.MemoryFile()
        self._to_raster(m, **kwargs)
        return m.getbuffer()

    def to_file(self, f, **kwargs):
        self._to_raster(f, **kwargs)

    def _to_raster(self, dst, **kwargs):
        options = {"driver": self._GDAL_DRIVER}
        options.update(kwargs)
        self.ds.rio.to_raster(dst, **options)

    def get(self, key, default=None):
        raise NotImplementedError


class GeoTIFFEncoder(Encoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(self, data, target=None, **kwargs):
        if data is None:
            raise ValueError("No data to encode")

        path_allowed = target is not None and target._name == "file"
        hints = {"path_allowed": path_allowed}

        from earthkit.data.data.wrappers import from_object

        data = from_object(data)
        return data._encode(self, hints=hints, target=target, **kwargs)

    def _encode(self, data, *, target=None, **kwargs):
        return self._encode_xarray(data, target=target, **kwargs)

    def _encode_field(self, field, *, target=None, **kwargs):
        return self._encode(field, target=target, **kwargs)

    def _encode_fieldlist(self, fieldlist, *, target=None, **kwargs):
        return self._encode(fieldlist, target=target, **kwargs)

    def _encode_xarray(self, data, *, target=None, **kwargs):
        ds = from_object(data).to_xarray()
        if ds.rio.crs is None:
            crs = data.geography.projection().to_cartopy_crs()
            ds.rio.write_crs(crs, inplace=True)
        for var in ds.data_vars:
            if "_earthkit" in ds[var].attrs:
                del ds[var].attrs["_earthkit"]
        return GeoTIFFEncodedData(ds)

    def _encode_featurelist(self, data, *, target=None, **kwargs):
        raise NotImplementedError

    def _encode_path(self, path_info=None, *, target=None, **kwargs):
        # Write file as is if target is file and path is provided.
        if (
            path_info is not None
            and path_info.path is not None
            and path_info.default_encoder == "geotiff"
            and target is not None
            and target._name == "file"
        ):
            return FilePathEncodedData(path_info.path, binary=path_info.binary)
        else:
            return None


encoder = GeoTIFFEncoder
