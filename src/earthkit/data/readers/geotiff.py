import mimetypes
from functools import cached_property

import numpy as np

from ..core.fieldlist import Field
from ..core.fieldlist import FieldList
from ..core.geography import Geography
from ..core.metadata import RawMetadata
from ..utils.bbox import BoundingBox
from ..utils.projections import Projection
from . import Reader


class GeoTIFFGeography(Geography):

    def __init__(self, metadata, da):
        self._metadata = metadata
        self._da = da
        self.x_dim = da.rio.x_dim
        self.y_dim = da.rio.y_dim

    def latitudes(self, dtype=None):
        raise NotImplementedError

    def longitudes(self, dtype=None):
        raise NotImplementedError

    def _xy_coords(self):
        x = self._da.coords[self.x_dim].values
        y = self._da.coords[self.y_dim].values
        return np.meshgrid(x, y)

    def x(self, dtype=None):
        return self._xy_coords()[0]

    def y(self, dtype=None):
        return self._xy_coords()[1]

    # @property
    def shape(self):
        return self._da.rio.height, self._da.rio.width

    def _unique_grid_id(self):
        raise NotImplementedError

    def projection(self):
        return Projection.from_cf_grid_mapping(**self._grid_mapping)

    @property
    def _grid_mapping(self):
        if self._da.rio.grid_mapping == "spatial_ref":
            return self._metadata.spatial_ref
        raise NotImplementedError

    def bounding_box(self):
        left, bottom, right, top = self._da.rio.transform_bounds("+proj=latlon")
        return BoundingBox(north=top, west=left, south=bottom, east=right)

    def gridspec(self):
        raise NotImplementedError

    def resolution(self):
        return self._da.rio.resolution()

    def mars_grid(self):
        raise NotImplementedError

    def mars_area(self):
        raise NotImplementedError


class GeoTIFFMetadata(RawMetadata):

    LS_KEYS = ["variable", "band"]

    def __init__(self, field, band):
        self._field = field
        self._geo = None
        super().__init__({"variable": field._da.name, "band": band, **field._da.attrs})

    @property
    def geography(self):
        if self._geo is None:
            self._geo = GeoTIFFGeography(self, self._field._da)
        return self._geo

    @property
    def spatial_ref(self):
        return self._field._da.coords["spatial_ref"].attrs


class GeoTIFFField(Field):
    """A band of a GeoTIFF file"""

    def __init__(self, da, band, array_backend):
        super().__init__(array_backend)
        self._da = da
        self.band = band

    def __repr__(self):
        return f"{self.__class__.__name__}({self.band},{self._da.name})"

    @cached_property
    def _metadata(self):
        return GeoTIFFMetadata(self, self.band)

    def to_xarray(self):
        return self._da

    def _values(self, dtype=None):
        return self._da.values.astype(dtype)


class GeoTIFFFieldList(FieldList):

    FIELD_TYPE = GeoTIFFField

    def __init__(self, path, **kwargs):
        self._fields = None
        self.path = path
        self._ds = self.rioxarray_read(band_as_variable=True)
        super().__init__(**kwargs)

    def rioxarray_read(self, **kwargs):
        import rioxarray

        options = dict()
        options.update(kwargs.get("rioxarray_open_rasterio_kwargs", {}))
        if not options:
            options = dict(**kwargs)

        return rioxarray.open_rasterio(self.path, **options)

    def to_xarray(self, **kwargs):
        return self.rioxarray_read(**kwargs)

    def __len__(self):
        return len(self._ds.data_vars)

    def _getitem(self, n):
        if isinstance(n, int):
            return self.fields[n]

    @property
    def fields(self):
        if self._fields is None:
            self._fields = self._get_fields(self._ds)
        return self._fields

    def _get_fields(self, ds, names=None):
        fields = []
        for band, (name, da) in enumerate(ds.data_vars.items(), start=1):
            # Prefer long_name over band_* naming for band_as_variable=True
            if "long_name" in da.attrs:
                da = da.rename(da.attrs["long_name"])
            fields.append(self.FIELD_TYPE(da, band, array_backend=self.array_backend))
        return fields


class GeoTIFFReader(GeoTIFFFieldList, Reader):

    def __init__(self, source, path):
        Reader.__init__(self, source, path)
        GeoTIFFFieldList.__init__(self, path)

    def __repr__(self):
        return f"GeoTIFFReader({self.path})"


def reader(source, path, **kwargs):
    kind, _ = mimetypes.guess_type(path)
    if kind == "image/tiff":
        return GeoTIFFReader(source, path)
