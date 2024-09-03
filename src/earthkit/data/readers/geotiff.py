import mimetypes
import os
from functools import cached_property

from ..core.fieldlist import Field
from ..core.fieldlist import FieldList
from ..core.geography import Geography
from ..core.metadata import RawMetadata
from ..utils.projections import Projection
from . import Reader


class GeoTIFFBandGeography(Geography):

    def __init__(self, da):
        self._da = da

    def latitudes(self, dtype=None):
        raise NotImplementedError

    def longitudes(self, dtype=None):
        raise NotImplementedError

    def x(self, dtype=None):
        raise NotImplementedError

    def y(self, dtype=None):
        raise NotImplementedError

    @property
    def shape(self):
        raise NotImplementedError

    def _unique_grid_id(self):
        raise NotImplementedError

    def projection(self):
        proj_string = self._da.rio.crs.to_proj4()
        return Projection.from_proj_string(proj_string)

    def bounding_box(self):
        raise NotImplementedError

    def gridspec(self):
        raise NotImplementedError

    def resolution(self):
        raise NotImplementedError

    def mars_grid(self):
        raise NotImplementedError

    def mars_area(self):
        raise NotImplementedError


class GeoTIFFBandMetadata(RawMetadata):

    def __init__(self, field):
        self._field = field
        self._geo = None
        super().__init__(dict(field._da.attrs))

    @property
    def geography(self):
        if self._geo is None:
            self._geo = GeoTIFFBandGeography(self._field._da)
        return self._geo


class GeoTIFFBandField(Field):

    def __init__(self, da, band, array_backend):
        super().__init__(array_backend)
        self._da = da
        self.band = band

    def __repr__(self):
        return f"{self.__class__.__name__}(band_{self.band})"

    @cached_property
    def _metadata(self):
        return GeoTIFFBandMetadata(self)

    def to_xarray(self):
        return self._da.sel({"band": self.band})

    def to_numpy(self):
        return self.to_xarray().values


class GeoTIFFBandFieldList(FieldList):

    FIELD_TYPE = GeoTIFFBandField

    def __init__(self, path, **kwargs):
        self._fields = None
        self.path = path
        super().__init__(**kwargs)

    @cached_property
    def xr_dataarray(self):
        import rioxarray

        return rioxarray.open_rasterio(self.path, band_as_variable=False)

    def to_xarray(self):
        name = self.xr_dataarray.name
        if name is None:
            # TODO: could be a URL
            # TODO: get rid of file extension
            name = os.path.basename(self.path)
        return self.xr_dataarray.to_dataset(name=name)

    def __len__(self):
        return self.xr_dataarray.coords["band"].size

    def _getitem(self, n):
        if isinstance(n, int):
            return self.fields[n]

    @property
    def fields(self):
        if self._fields is None:
            self._fields = self._get_fields(self.xr_dataarray)
        return self._fields

    def _get_fields(self, da):
        fields = []
        for band in da.coords["band"].values:
            # TODO: name?
            fields.append(self.FIELD_TYPE(da, band, array_backend=self.array_backend))
        return fields


class GeoTIFFReader(GeoTIFFBandFieldList, Reader):

    def __init__(self, source, path):
        Reader.__init__(self, source, path)
        GeoTIFFBandFieldList.__init__(self, path)

    def __repr__(self):
        return f"GeoTIFFReader({self.path})"


def reader(source, path, **kwargs):
    kind, _ = mimetypes.guess_type(path)
    if kind == "image/tiff":
        # import rioxarray
        # ds = rioxarray .open_rasterio(path)
        # return from_object(ds)
        return GeoTIFFReader(source, path)
