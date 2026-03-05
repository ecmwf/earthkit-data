# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.utils.decorators import thread_safe_cached_property

from earthkit.data.indexing.simple import SimpleFieldListBase


class GeoTIFFFieldList(SimpleFieldListBase):
    """A list of GeoTIFF bands"""

    DEFAULT_XARRAY_KWARGS = {
        # Splitting bands into individual variables preserves band-specific metadata.
        "band_as_variable": True,
        # Mask and scale values by default to match xarray's default behaviour.
        # Note: masked values are set to NaN, so all values are returned as floats.
        "mask_and_scale": True,
        "decode_times": True,
    }

    def __init__(self, path, **kwargs):
        self.path = path
        self._ds = self._rioxarray_read()
        # Shared geography instance for all fields/bands
        # self._geo = GeoTIFFGeography(self._ds)

    def _rioxarray_read(self, **kwargs):
        try:
            import rioxarray
        except ImportError:
            raise ImportError("geotiff handling requires 'rioxarray' to be installed")

        options = dict(**self.DEFAULT_XARRAY_KWARGS)
        # Read options from dedicated kwarg if exists, otherwise use all kwargs
        options.update(kwargs.get("rioxarray_open_rasterio_kwargs", kwargs))

        return rioxarray.open_rasterio(self.path, **options)

    def to_xarray(self, **kwargs):
        return self._rioxarray_read(**kwargs)

    def to_pandas(self):
        import pandas as pd

        series = [field.to_pandas() for field in self]
        return pd.concat(series, keys=[s.name for s in series])

    @thread_safe_cached_property
    def _fields(self):
        return self._get_fields(self._ds)

    def _get_fields(self, ds, names=None):
        """Must be called from _fields property to ensure thread safety of caching."""
        fields = []
        from earthkit.data.field.geotiff.create import create_geotiff_field

        # Follow GDAL convention and count GeoTIFF bands from 1
        for band, (name, da) in enumerate(ds.data_vars.items(), start=1):
            # Prefer long_name over band_* naming of band_as_variable=True
            if "long_name" in da.attrs:
                da = da.rename(da.attrs["long_name"])

            f = create_geotiff_field(band, da)
            fields.append(f)
            # fields.append(self.FIELD_TYPE(da, band, geography=self._geo))
        return fields

    def describe(self, *args, **kwargs):
        self._not_implemented()

    def _default_encoder(self):
        return "internal-pass-through"
