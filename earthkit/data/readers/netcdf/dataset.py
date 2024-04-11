# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

import numpy as np

LOG = logging.getLogger(__name__)


GEOGRAPHIC_COORDS = {
    "x": ["x", "projection_x_coordinate", "lon", "longitude"],
    "y": ["y", "projection_y_coordinate", "lat", "latitude"],
}


class DataSet:
    """
    Class that wraps a xarray dataset to provide caching
    """

    def __init__(self, ds):
        self._ds = ds
        self._bbox = {}
        self._cache = {}

    @property
    def data_vars(self):
        return self._ds.data_vars

    def __getitem__(self, name):
        return self._ds[name]

    def __getattr__(self, name):
        return getattr(self._ds, name)

    def bbox(self, variable):
        data_array = self[variable]

        coords = self._get_xy_coords(data_array)
        key = ("bbox", tuple(coords))
        if key in self._cache:
            return self._cache[key]

        lons = self._get_xy(data_array, "x", flatten=False)
        lats = self._get_xy(data_array, "y", flatten=False)

        north = np.amax(lats)
        west = np.amin(lons)
        south = np.amin(lats)
        east = np.amax(lons)

        self._cache[key] = (north, west, south, east)
        return self._cache[key]

        # dims = data_array.dims

        # lat = dims[-2]
        # lon = dims[-1]

        # key = ("bbox", lat, lon)
        # if key in self._cache:
        #     return self._cache[key]

        # lats, lons = self.grid_points(variable)
        # north = np.amax(lats)
        # west = np.amin(lons)
        # south = np.amin(lats)
        # east = np.amax(lons)

        # self._cache[key] = (north, west, south, east)
        # return self._cache[key]

        # if (lat, lon) not in self._bbox:
        #     dims = data_array.dims

        #     latitude = data_array[lat]
        #     longitude = data_array[lon]

        #     self._bbox[(lat, lon)] = (
        #         np.amax(latitude.data),
        #         np.amin(longitude.data),
        #         np.amin(latitude.data),
        #         np.amax(longitude.data),
        #     )

        # return self._bbox[(lat, lon)]

    # def grid_points(self, variable):
    #     data_array = self[variable]
    #     dims = data_array.dims

    #     lat = dims[-2]
    #     lon = dims[-1]

    #     key = ("grid_points", lat, lon)
    #     if key in self._cache:
    #         return self._cache[key]

    #     if "latitude" in self._ds and "longitude" in self._ds:
    #         latitude = self._ds["latitude"]
    #         longitude = self._ds["longitude"]

    #         if latitude.dims == (lat, lon) and longitude.dims == (lat, lon):
    #             latitude = latitude.data
    #             longitude = longitude.data
    #             return latitude.flatten(), longitude.flatten()

    #     latitude = data_array[lat]
    #     longitude = data_array[lon]

    #     lat, lon = np.meshgrid(latitude.data, longitude.data)

    #     self._cache[key] = lat.flatten(), lon.flatten()
    #     return self._cache[key]

    # def grid_points_xy(self, variable):
    #     data_array = self[variable]
    #     dims = data_array.dims

    #     lat = dims[-2]
    #     lon = dims[-1]

    #     latitude = data_array[lat].data
    #     longitude = data_array[lon].data

    #     print(latitude, longitude)

    #     lat, lon = np.meshgrid(latitude, longitude)

    #     return lat.flatten(), lon.flatten()
    #     # return self._cache[key]

    def _get_xy(self, data_array, axis, flatten=False, dtype=None):
        if axis not in ("x", "y"):
            raise ValueError(f"Invalid axis={axis}")

        coords = self._get_xy_coords(data_array)
        key = ("grid_points", tuple(coords))
        if key in self._cache:
            points = self._cache[key]
        else:
            points = dict()
            keys = [x[0] for x in coords]
            coords = tuple([x[1] for x in coords])

            if "latitude" in self._ds and "longitude" in self._ds:
                latitude = self._ds["latitude"]
                longitude = self._ds["longitude"]

                if latitude.dims == coords and longitude.dims == coords:
                    latitude = latitude.data
                    longitude = longitude.data
                    points["x"] = longitude
                    points["y"] = latitude
            if not points:
                v0, v1 = data_array.coords[coords[0]], data_array.coords[coords[1]]
                points[keys[1]], points[keys[0]] = np.meshgrid(v1, v0)
                self._cache[key] = points

        if flatten:
            points[axis] = points[axis].reshape(-1)
        if dtype is not None:
            return points[axis].astype(dtype)
        else:
            return points[axis]

    def _get_xy_coords(self, data_array):
        c = []

        axes = ("x", "y")
        for dim in data_array.dims:
            for ax in axes:
                candidates = GEOGRAPHIC_COORDS.get(ax, [])
                if dim in candidates:
                    c.append((ax, dim))
                else:
                    ax = data_array.coords[dim].attrs.get("axis", "").lower()
                    if ax in axes:
                        c.append([ax, dim])
            if len(c) == 2:
                return c

        for ax in axes:
            if ax not in [x[0] for x in c]:
                raise ValueError(f"No coordinate found with axis '{ax}'")

        return c
