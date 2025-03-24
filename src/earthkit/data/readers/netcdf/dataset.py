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

        keys, dims = self._get_xy_dims(data_array)
        key = ("bbox", tuple(keys), tuple(dims))
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

    def _get_xy_dims(self, data_array):
        # TODO: refactor it

        # the last 2 dimensions are y,x
        if (
            len(data_array.dims) >= 2
            and data_array.dims[-1] in GEOGRAPHIC_COORDS["x"]
            and data_array.dims[-2] in GEOGRAPHIC_COORDS["y"]
        ):
            return ("y", "x"), (data_array.dims[-2], data_array.dims[-1])

        # the last 2 dimensions are x, y
        if (
            len(data_array.dims) >= 2
            and data_array.dims[-1] in GEOGRAPHIC_COORDS["y"]
            and data_array.dims[-2] in GEOGRAPHIC_COORDS["x"]
        ):
            return ("x", "y"), (data_array.dims[-2], data_array.dims[-1])

        # try to find the x and y dimensions
        keys = []
        dims = []
        axes = ("x", "y")
        for dim in data_array.dims:
            for ax in axes:
                candidates = GEOGRAPHIC_COORDS.get(ax, [])
                if dim in candidates:
                    keys.append(ax)
                    dims.append(dim)
                else:
                    ax = data_array.coords[dim].attrs.get("axis", "").lower()
                    if ax in axes:
                        keys.append(ax)
                        dims.append(dim)
            if len(keys) == 2:
                return tuple(keys), tuple(dims)

        # 1D geographic coordinates using the dim='values' convention
        if not keys or not dims:
            dim = "values"
            if data_array.dims and data_array.dims[-1] == dim:
                for x, y in zip(GEOGRAPHIC_COORDS["x"], GEOGRAPHIC_COORDS["y"]):
                    if (x in data_array.coords or x in self._ds.variables) and (
                        y in data_array.coords or y in self._ds.variables
                    ):
                        if (
                            len(self._ds[x].dims) == 1
                            and len(self._ds[y].dims) == 1
                            and self._ds[x].dims[-1] == dim
                            and self._ds[y].dims[-1] == dim
                        ):
                            return tuple(["x"]), tuple([dim])

        for ax in axes:
            if ax not in keys:
                raise ValueError(f"No dimension found with axis '{ax}'")

        return keys, dims

    def _get_xy(self, data_array, flatten=False, dtype=None):
        # TODO: refactor it

        keys, dims = self._get_xy_dims(data_array)
        key = ("grid_points", tuple(keys), tuple(dims))

        if key in self._cache:
            points = self._cache[key]
        else:
            points = dict()
            if all(d in data_array.coords for d in dims):
                v0, v1 = data_array.coords[dims[0]], data_array.coords[dims[1]]
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
        # TODO: refactor it
        keys, dims = self._get_xy_dims(data_array)

        points = dict()

        def _get_ll(keys):
            for key in keys:
                if key in self._ds:
                    return self._ds[key]

        lat_keys = ["latitude", "lat"]
        lon_keys = ["longitude", "lon"]
        latitude = _get_ll(lat_keys)
        longitude = _get_ll(lon_keys)

        # lat-lon variable/coordinate available
        if latitude is not None and longitude is not None:
            if latitude.dims == dims and longitude.dims == dims:
                latitude = latitude.data
                longitude = longitude.data
                points["y"] = latitude
                points["x"] = longitude

        # lat-lon meshgrid
        if not points:
            key = ("grid_points", tuple(keys), tuple(dims))

            if key in self._cache:
                points = self._cache[key]
            else:
                if all(d in data_array.coords for d in dims):
                    v0, v1 = data_array.coords[dims[0]], data_array.coords[dims[1]]
                    points[keys[1]], points[keys[0]] = np.meshgrid(v1, v0)
                    self._cache[key] = points
                else:
                    raise ValueError(f"Could not find lat-lon coordinates for {data_array.name}")

        if flatten:
            points["x"] = points["x"].reshape(-1)
            points["y"] = points["y"].reshape(-1)

        if dtype is not None:
            return points["y"].astype(dtype), points["x"].astype(dtype)
        else:
            return points["y"], points["x"]
