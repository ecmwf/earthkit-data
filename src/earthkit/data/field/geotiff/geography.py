# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import numpy as np

from earthkit.data.field.geography import GeographyFieldPart
from earthkit.data.field.spec.geography import Geography
from earthkit.data.utils.bbox import BoundingBox


class GeoTIFFGeographySpec(Geography):
    def __init__(self, ds):
        self._ds = ds
        self.x_dim = ds.rio.x_dim
        self.y_dim = ds.rio.y_dim

    def _latlon_coords(self):
        try:
            from pyproj import Transformer
        except ImportError:
            raise ImportError("geotiff handling requires 'pyproj' to be installed")

        return Transformer.from_crs(self._ds.rio.crs, "EPSG:4326", always_xy=True).transform(
            *self._xy_coords()
        )

    def _xy_coords(self):
        x = self._ds.coords[self.x_dim].values
        y = self._ds.coords[self.y_dim].values
        return np.meshgrid(x, y)

    @property
    def latitudes(self):
        return self._latlon_coords()[0]

    @property
    def longitudes(self):
        return self._latlon_coords()[1]

    @property
    def distinct_latitudes(self):
        r"""Return the distinct latitudes."""
        pass

    @property
    def distinct_longitudes(self):
        r"""Return the distinct longitudes."""
        pass

    @property
    def x(self):
        r"""array-like: Return the x coordinates in the original CRS."""
        return self._xy_coords()[0]

    @property
    def y(self):
        r"""array-like: Return the y coordinates in the original CRS."""
        return self._xy_coords()[1]

    @property
    def shape(self):
        return self._ds.rio.height, self._ds.rio.width

    @property
    def projection(self):
        from earthkit.data.utils.projections import Projection

        return Projection.from_cf_grid_mapping(**self._grid_mapping)

    @property
    def bounding_box(self):
        left, bottom, right, top = self._ds.rio.transform_bounds("EPSG:4326")
        return BoundingBox(north=top, west=left, south=bottom, east=right)

    @property
    def unique_grid_id(self):
        r"""str: Return the unique id of the grid."""
        return (*self.shape, self._ds.rio.crs.to_wkt())

    @property
    def grid_spec(self):
        r"""Return the grid specification."""
        pass

    @property
    def grid_type(self):
        r"""Return the grid specification."""
        pass

    @property
    def _grid_mapping(self):
        if self._ds.rio.grid_mapping == "spatial_ref":
            return self._ds.coords["spatial_ref"].attrs
        raise NotImplementedError

    def __getstate__(self):
        pass

    def __setstate__(self, state):
        pass


class GeoTIFFGeography(GeographyFieldPart):
    def __init__(self, ds) -> None:
        spec = GeoTIFFGeographySpec(ds)
        super().__init__(spec)
