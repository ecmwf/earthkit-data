# (C) Copyright 2024 Anemoi contributors.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import logging
from abc import ABC
from abc import abstractmethod
from typing import Any
from typing import Tuple

import numpy as np
from earthkit.utils.decorators import thread_safe_cached_property

from earthkit.data.utils.bbox import BoundingBox

LOG = logging.getLogger(__name__)


class XarrayGrid:
    """Grid class for latitude and longitude coordinates."""

    def __init__(self, latlon_grid=None, xy_grid=None) -> None:
        self.latlon_grid = latlon_grid
        self.xy_grid = xy_grid

    @property
    def latlons(self):
        if self.latlon_grid is not None:
            return self.latlon_grid.latlons
        else:
            return self.xy_grid.latlons

    @property
    def xys(self):
        if self.xy_grid is not None:
            return self.xy_grid.xys
        else:
            raise NotImplementedError("XarrayGrid: xy grid not available")

    # Properly implement it for all grid types
    @thread_safe_cached_property
    def bbox(self):
        lat, lon = self.latlons
        lat = lat.flatten()
        lon = lon.flatten()

        north = np.amax(lat)
        west = np.amin(lon)
        south = np.amin(lat)
        east = np.amax(lon)

        return BoundingBox(north=north, south=south, east=east, west=west)

    @property
    def projection(self):
        if self.xy_grid is not None:
            from earthkit.data.utils.projections import Projection

            proj = self.xy_grid.projection
            return Projection.from_cf_grid_mapping(**proj)


class Grid(ABC):
    """Abstract base class for grid structures."""

    def __init__(self) -> None:
        pass

    @property
    @abstractmethod
    def latlons(self) -> Tuple[Any, Any]:
        """Get the grid points."""
        pass

    @property
    @abstractmethod
    def xys(self) -> Tuple[Any, Any]:
        """Get the grid points."""
        pass


class LatLonGrid(Grid):
    """Grid class for latitude and longitude coordinates."""

    def __init__(self, lat: Any, lon: Any, variable_dims: Any) -> None:
        """Initialize the LatLonGrid class.

        Parameters
        ----------
        lat : Any
            The latitudes.
        lon : Any
            The longitudes.
        variable_dims : Any
            The variable dimensions.
        """
        super().__init__()
        self.lat = lat
        self.lon = lon
        self.variable_dims = variable_dims

    @property
    def xys(self) -> Tuple[Any, Any]:
        """Get the x and y points for the lat-lon grid."""
        raise NotImplementedError("LatLonGrid: xy grid not available")


class XYGrid(Grid):
    """Grid class for x and y coordinates."""

    def __init__(self, x: Any, y: Any) -> None:
        """Initialize the XYGrid class.

        Parameters
        ----------
        x : Any
            The x-coordinates.
        y : Any
            The y-coordinates.
        """
        self.x = x
        self.y = y


class MeshedGrid(LatLonGrid):
    """Grid class for meshed latitude and longitude coordinates."""

    @thread_safe_cached_property
    def latlons(self) -> Tuple[Any, Any]:
        """Get the grid points for the meshed grid."""

        if self.variable_dims == (self.lon.variable.name, self.lat.variable.name):
            lat, lon = np.meshgrid(
                self.lat.variable.values,
                self.lon.variable.values,
            )
        elif self.variable_dims == (self.lat.variable.name, self.lon.variable.name):
            lon, lat = np.meshgrid(
                self.lon.variable.values,
                self.lat.variable.values,
            )

        else:
            raise NotImplementedError(
                f"MeshedGrid.grid_points: unrecognized variable_dims {self.variable_dims}"
            )

        return lat.flatten(), lon.flatten()


class UnstructuredGrid(LatLonGrid):
    """Grid class for unstructured latitude and longitude coordinates."""

    def __init__(self, lat: Any, lon: Any, variable_dims: Any) -> None:
        """Initialize the UnstructuredGrid class.

        Parameters
        ----------
        lat : Any
            The latitudes.
        lon : Any
            The longitudes.
        variable_dims : Any
            The variable dimensions.
        """
        super().__init__(lat, lon, variable_dims)
        assert len(lat) == len(lon), (len(lat), len(lon))
        self.variable_dims = variable_dims
        self.grid_dims = lat.variable.dims
        assert lon.variable.dims == self.grid_dims, (lon.variable.dims, self.grid_dims)
        assert set(self.variable_dims) == set(self.grid_dims), (self.variable_dims, self.grid_dims)

    @thread_safe_cached_property
    def latlons(self) -> Tuple[Any, Any]:
        """Get the grid points for the unstructured grid."""
        assert 1 <= len(self.variable_dims) <= 2

        if len(self.variable_dims) == 1:
            return self.lat.variable.values.flatten(), self.lon.variable.values.flatten()

        if len(self.variable_dims) == 2 and self.variable_dims == self.grid_dims:
            return self.lat.variable.values.flatten(), self.lon.variable.values.flatten()

        LOG.warning(
            "UnstructuredGrid: variable indexing %s does not match grid indexing %s",
            self.variable_dims,
            self.grid_dims,
        )

        lat = self.lat.variable.values.transpose().flatten()
        lon = self.lon.variable.values.transpose().flatten()

        return lat, lon


class RawXYGrid(XYGrid):
    """Grid class for raw x and y coordinates."""

    def __init__(self, x: Any, y: Any, variable_dims: Any) -> None:
        """Initialize the RawXYGrid class.

        Parameters
        ----------
        x : Any
            The x-coordinates.
        y : Any
            The y-coordinates.
        variable_dims : Any
            The variable dimensions.
        """
        super().__init__(x, y)
        self.variable_dims = variable_dims

    @property
    def latlons(self) -> Tuple[Any, Any]:
        """Get the lat and lon points for the raw xy grid."""
        raise NotImplementedError("RawXYGrid: latlon not available")


class MeshedXYGrid(RawXYGrid):
    """Grid class for meshed x and y coordinates."""

    @thread_safe_cached_property
    def xys(self) -> Tuple[Any, Any]:
        """Get the grid points for the meshed grid."""

        if self.variable_dims == (self.x.variable.name, self.y.variable.name):
            y, x = np.meshgrid(
                self.y.variable.values,
                self.x.variable.values,
            )
        elif self.variable_dims == (self.y.variable.name, self.x.variable.name):
            x, y = np.meshgrid(
                self.x.variable.values,
                self.y.variable.values,
            )

        else:
            raise NotImplementedError(
                f"MeshedGrid.grid_points: unrecognized variable_dims {self.variable_dims}"
            )

        return x.flatten(), y.flatten()


class UnstructuredXYGrid(RawXYGrid):
    """Grid class for unstructured x and y coordinates."""

    def __init__(self, x: Any, y: Any, variable_dims: Any) -> None:
        """Initialize the UnstructuredGrid class.

        Parameters
        ----------
        x : Any
            The x-coordinates.
        y : Any
            The y-coordinates.
        variable_dims : Any
            The variable dimensions.
        """
        super().__init__(x, y, variable_dims)
        assert len(x) == len(y), (len(x), len(y))
        self.variable_dims = variable_dims
        self.grid_dims = x.variable.dims
        assert y.variable.dims == self.grid_dims, (y.variable.dims, self.grid_dims)
        assert set(self.variable_dims) == set(self.grid_dims), (self.variable_dims, self.grid_dims)

    @thread_safe_cached_property
    def xys(self) -> Tuple[Any, Any]:
        """Get the grid points for the unstructured grid."""
        assert 1 <= len(self.variable_dims) <= 2

        if len(self.variable_dims) == 1:
            return self.x.variable.values.flatten(), self.y.variable.values.flatten()

        if len(self.variable_dims) == 2 and self.variable_dims == self.grid_dims:
            return self.x.variable.values.flatten(), self.y.variable.values.flatten()

        LOG.warning(
            "UnstructuredGrid: variable indexing %s does not match grid indexing %s",
            self.variable_dims,
            self.grid_dims,
        )

        x = self.x.variable.values.transpose().flatten()
        y = self.y.variable.values.transpose().flatten()

        return x, y


class ProjectionGrid(XYGrid):
    """Grid class for projected x and y coordinates."""

    def __init__(self, x: Any, y: Any, projection: Any) -> None:
        """Initialize the ProjectionGrid class.

        Parameters
        ----------
        x : Any
            The x-coordinates.
        y : Any
            The y-coordinates.
        projection : Any
            The projection information.
        """
        super().__init__(x, y)
        self.projection = projection

    def transformer(self) -> Any:
        """Get the transformer for the projection.

        Returns
        -------
        Any
            The transformer.
        """
        from pyproj import CRS
        from pyproj import Transformer

        if isinstance(self.projection, dict):
            data_crs = CRS.from_cf(self.projection)
        else:
            data_crs = self.projection

        wgs84_crs = CRS.from_epsg(4326)  # WGS84

        return Transformer.from_crs(data_crs, wgs84_crs, always_xy=True)


class MeshProjectionGrid(ProjectionGrid):
    """Grid class for meshed projected coordinates."""

    @thread_safe_cached_property
    def latlons(self) -> Tuple[Any, Any]:
        """Get the grid points for the mesh projection grid."""
        transformer = self.transformer()
        xv, yv = np.meshgrid(self.x.variable.values, self.y.variable.values)  # , indexing="ij")
        lon, lat = transformer.transform(xv, yv)
        return lat.flatten(), lon.flatten()

    @thread_safe_cached_property
    def xys(self) -> Tuple[Any, Any]:
        """Get the x and y points for the mesh projection grid."""
        xv, yv = np.meshgrid(self.x.variable.values, self.y.variable.values)  # , indexing="ij")
        return xv.flatten(), yv.flatten()


class UnstructuredProjectionGrid(ProjectionGrid):
    """Grid class for unstructured projected coordinates."""

    @thread_safe_cached_property
    def latlons(self) -> Tuple[Any, Any]:
        """Get the grid points for the unstructured projection grid."""
        transformer = self.transformer()
        xv, yv = self.xyz
        lon, lat = transformer.transform(xv, yv)
        return lat.flatten(), lon.flatten()

    @thread_safe_cached_property
    def xys(self) -> Tuple[Any, Any]:
        """Get the x and y points for the mesh projection grid."""
        if self.projection == "epsg:4326":
            # WGS84, no transformation needed
            return self.y.variable.values.flatten(), self.x.variable.values.flatten()
        xv, yv = np.meshgrid(self.x.variable.values, self.y.variable.values)  # , indexing="ij")
        return xv.flatten(), yv.flatten()
