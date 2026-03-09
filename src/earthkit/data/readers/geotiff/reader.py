# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.sources import Source

from .. import Reader


class GeoTIFFReader(Source, Reader):
    DEFAULT_XARRAY_KWARGS = {
        # Splitting bands into individual variables preserves band-specific metadata.
        "band_as_variable": True,
        # Mask and scale values by default to match xarray's default behaviour.
        # Note: masked values are set to NaN, so all values are returned as floats.
        "mask_and_scale": True,
        "decode_times": True,
    }

    def __init__(self, source, path):
        Reader.__init__(self, source, path)
        # GeoTIFFFieldList.__init__(self, path)

    def __repr__(self):
        return f"GeoTIFFReader({self.path})"

    # def mutate_source(self):
    #     return self

    def rioxarray_read(self, **kwargs):
        try:
            import rioxarray
        except ImportError:
            raise ImportError("geotiff handling requires 'rioxarray' to be installed")

        options = dict(**self.DEFAULT_XARRAY_KWARGS)
        # Read options from dedicated kwarg if exists, otherwise use all kwargs
        options.update(kwargs.get("rioxarray_open_rasterio_kwargs", kwargs))

        return rioxarray.open_rasterio(self.path, **options)

    def to_xarray(self, **kwargs):
        return self.rioxarray_read(**kwargs)

    def to_fieldlist(self, *args, **kwargs):
        from .fieldlist import GeoTIFFFieldList

        return GeoTIFFFieldList(self.path, **kwargs)

    def to_data_object(self):
        from earthkit.data.data.geotiff import GeoTIFFData

        return GeoTIFFData(self)

    def mutate(self):
        return self

    def _default_encoder(self):
        return Reader._default_encoder(self)
