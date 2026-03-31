# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.sources import Source

from .core import DEFAULT_XARRAY_KWARGS, GeoTIFFReaderBase


class GeoTIFFReader(Source, GeoTIFFReaderBase):
    def __init__(self, source, path):
        GeoTIFFReaderBase.__init__(self, source, path)

    def __repr__(self):
        return f"GeoTIFFReader({self.path})"

    def rioxarray_read(self, rioxarray_open_rasterio_kwargs=None, **kwargs):
        try:
            import rioxarray
        except ImportError:
            raise ImportError("geotiff handling requires 'rioxarray' to be installed")

        options = dict(DEFAULT_XARRAY_KWARGS)

        # Read options from dedicated kwarg if exists, otherwise use all kwargs
        if rioxarray_open_rasterio_kwargs is None:
            rioxarray_open_rasterio_kwargs = kwargs.copy()
        options.update(rioxarray_open_rasterio_kwargs)

        return rioxarray.open_rasterio(self.path, **options)

    def to_xarray(self, **kwargs):
        return self.rioxarray_read(**kwargs)

    def to_fieldlist(self, *args, **kwargs):
        from .fieldlist import GeoTIFFFieldList

        return GeoTIFFFieldList(self.path, **kwargs)

    def to_data_object(self):
        from earthkit.data.data.geotiff import GeoTIFFData

        return GeoTIFFData(self)

    def mutate_source(self):
        return self

    def _encode_default(self, encoder, *args, **kwargs):
        return encoder._encode_xarray(self.to_xarray(), *args, **kwargs)
