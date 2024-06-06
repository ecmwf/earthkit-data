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
    "x": ["x", "X", "xc", "projection_x_coordinate", "lon", "longitude"],
    "y": ["y", "Y", "yc", "projection_y_coordinate", "lat", "latitude"],
}


class DataSet:
    """Class that wraps a xarray dataset to provide caching"""

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

        keys, coords = self._get_xy_coords(data_array)
        key = ("bbox", tuple(keys), tuple(coords))
        if key in self._cache:
            return self._cache[key]

        # lons = self._get_xy(data_array, "x", flatten=False)
        # lats = self._get_xy(data_array, "y", flatten=False)

        lats, lons = self._get_latlon(data_array, flatten=False)

        north = np.amax(lats)
        west = np.amin(lons)
        south = np.amin(lats)
        east = np.amax(lons)

        self._cache[key] = (north, west, south, east)
        return self._cache[key]

    def _get_xy_coords(self, data_array):
        if (
            len(data_array.dims) >= 2
            and data_array.dims[-1] in GEOGRAPHIC_COORDS["x"]
            and data_array.dims[-2] in GEOGRAPHIC_COORDS["y"]
        ):
            return ("y", "x"), (data_array.dims[-2], data_array.dims[-1])

        keys = []
        coords = []
        axes = ("x", "y")
        for dim in data_array.dims:
            for ax in axes:
                candidates = GEOGRAPHIC_COORDS.get(ax, [])
                if dim in candidates:
                    keys.append(ax)
                    coords.append(dim)
                else:
                    ax = data_array.coords[dim].attrs.get("axis", "").lower()
                    if ax in axes:
                        keys.append(ax)
                        coords.append(dim)
            if len(keys) == 2:
                return tuple(keys), tuple(coords)

        for ax in axes:
            if ax not in keys:
                raise ValueError(f"No coordinate found with axis '{ax}'")

        return keys, coords

    def _get_xy(self, data_array, flatten=False, dtype=None):
        keys, coords = self._get_xy_coords(data_array)
        key = ("grid_points", tuple(keys), tuple(coords))

        if key in self._cache:
            points = self._cache[key]
        else:
            points = dict()
            v0, v1 = data_array.coords[coords[0]], data_array.coords[coords[1]]
            points[keys[1]], points[keys[0]] = np.meshgrid(v1, v0)
            self._cache[key] = points

        if flatten:
            points["x"] = points["x"].reshape(-1)
            points["y"] = points["y"].reshape(-1)

        if dtype is not None:
            return points["x"].astype(dtype), points["y"].astype(dtype)
        else:
            return points["x"], points["y"]

    def _get_latlon(self, data_array, flatten=False, dtype=None):
        keys, coords = self._get_xy_coords(data_array)

        points = dict()

        def _get_ll(keys):
            for key in keys:
                if key in self._ds:
                    return self._ds[key]

        lat_keys = ["latitude", "lat"]
        lon_keys = ["longitude", "lon"]
        latitude = _get_ll(lat_keys)
        longitude = _get_ll(lon_keys)

        if latitude is not None and longitude is not None:
            if latitude.dims == coords and longitude.dims == coords:
                latitude = latitude.data
                longitude = longitude.data
                points["y"] = latitude
                points["x"] = longitude

        if not points:
            key = ("grid_points", tuple(keys), tuple(coords))

            if key in self._cache:
                points = self._cache[key]
            else:
                v0, v1 = data_array.coords[coords[0]], data_array.coords[coords[1]]
                points[keys[1]], points[keys[0]] = np.meshgrid(v1, v0)
                self._cache[key] = points

        if flatten:
            points["x"] = points["x"].reshape(-1)
            points["y"] = points["y"].reshape(-1)

        if dtype is not None:
            return points["y"].astype(dtype), points["x"].astype(dtype)
        else:
            return points["y"], points["x"]
