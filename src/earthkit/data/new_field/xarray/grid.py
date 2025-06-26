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
from functools import cached_property
from typing import Any
from typing import Tuple

import numpy as np

LOG = logging.getLogger(__name__)


class Grid(ABC):
    """Abstract base class for grid structures."""

    def __init__(self) -> None:
        pass

    @property
    def latitudes(self) -> Any:
        """Get the latitudes of the grid."""
        return self.grid_points[0]

    @property
    def longitudes(self) -> Any:
        """Get the longitudes of the grid."""
        return self.grid_points[1]

    @property
    @abstractmethod
    def grid_points(self) -> Tuple[Any, Any]:
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

    @cached_property
    def grid_points(self) -> Tuple[Any, Any]:
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

    @cached_property
    def grid_points(self) -> Tuple[Any, Any]:
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

    @cached_property
    def grid_points(self) -> Tuple[Any, Any]:
        """Get the grid points for the mesh projection grid."""
        transformer = self.transformer()
        xv, yv = np.meshgrid(self.x.variable.values, self.y.variable.values)  # , indexing="ij")
        lon, lat = transformer.transform(xv, yv)
        return lat.flatten(), lon.flatten()


class UnstructuredProjectionGrid(XYGrid):
    """Grid class for unstructured projected coordinates."""

    @cached_property
    def grid_points(self) -> Tuple[Any, Any]:
        """Get the grid points for the unstructured projection grid."""
        raise NotImplementedError("UnstructuredProjectionGrid")
