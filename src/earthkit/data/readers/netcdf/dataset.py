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
    "x": ["x", "X", "xc", "projection_x_coordinate", "lon", "longitude", "grid_longitude"],
    "y": ["y", "Y", "yc", "projection_y_coordinate", "lat", "latitude", "grid_latitude"],
}

GEOGRAPHIC_COORDS_LATLON_FIRST = {
    "x": ["lon", "longitude", "x", "X", "xc", "projection_x_coordinate"],
    "y": ["lat", "latitude", "y", "Y", "yc", "projection_y_coordinate"],
}


class Coverage:
    def __init__(self, owner, da):
        self.owner = owner
        self.da = da

    def bbox(self):
        keys = self.keys()
        key = ("bbox", *keys)
        if key in self.owner._cache:
            return self.owner._cache[key]

        lat, lon = self.to_latlon(flatten=False)

        north = np.amax(lat)
        west = np.amin(lon)
        south = np.amin(lat)
        east = np.amax(lon)

        self.owner._cache[key] = (north, west, south, east)
        return self.owner._cache[key]

    @staticmethod
    def _output(points, flatten=False, dtype=None):
        if flatten:
            points["x"] = points["x"].reshape(-1)
            points["y"] = points["y"].reshape(-1)

        if dtype is not None:
            return points["x"].astype(dtype), points["y"].astype(dtype)
        else:
            return points["x"], points["y"]

    def to_xy(self, **kwargs):
        raise NotImplementedError

    def keys(self):
        raise NotImplementedError

    @property
    def shape(self):
        raise NotImplementedError

    @staticmethod
    def make(owner, da):
        if len(da.dims) >= 2:
            # the last 2 dimensions are y, x or x, y
            d1 = da.dims[-1]
            d2 = da.dims[-2]
            if d1 in GEOGRAPHIC_COORDS["x"] and d2 in GEOGRAPHIC_COORDS["y"]:
                return GridCoverage(owner, da, x_dim=d1, y_dim=d2, dims=(d2, d1))
            elif d1 in GEOGRAPHIC_COORDS["y"] and d2 in GEOGRAPHIC_COORDS["x"]:
                return GridCoverage(owner, da, x_dim=d2, y_dim=d1, dims=(d2, d1))

            # try to find the x and y dimensions
            dims = {}
            axes = ("x", "y")
            for dim in da.dims[-2:]:
                for ax in axes:
                    candidates = GEOGRAPHIC_COORDS.get(ax, [])
                    if dim in candidates:
                        # keys.append(ax)
                        dims[ax] = dim
                    else:
                        ax_attr = da.coords[dim].attrs.get("axis", "").lower()
                        if ax_attr in axes:
                            # keys.append(ax)
                            # dims.append(dim)
                            dims[ax] = dim
                if len(dims) == 2:
                    return GridCoverage(
                        owner, da, x_dim=dims["x"], y_dim=dims["y"], dims=tuple(dims.values())
                    )

        # try to find the x and y dimensions
        # 1D geographic coordinates using the dim='values/points' convention
        if da.dims:
            last_dim = da.dims[-1]
            for x, y in zip(GEOGRAPHIC_COORDS["x"], GEOGRAPHIC_COORDS["y"]):
                if x in da.coords and y in da.coords:
                    x_coord = da.coords[x]
                    y_coord = da.coords[y]
                    if (
                        len(x_coord.dims) == 1
                        and len(y_coord.dims) == 1
                        and x_coord.dims[-1] == last_dim
                        and y_coord.dims[-1] == last_dim
                    ):
                        return PointCoverage(owner, da, x=x, y=y, dim=last_dim, var_coord=True)
                elif x in owner._ds and y in owner._ds:
                    x_v = owner._ds[x]
                    y_v = owner._ds[y]
                    if (
                        len(x_v.dims) == 1
                        and len(y_v.dims) == 1
                        and x_v.dims[-1] == last_dim
                        and y_v.dims[-1] == last_dim
                    ):
                        return PointCoverage(owner, da, x=x, y=y, dim=last_dim, var_coord=False)


class GridCoverage(Coverage):
    def __init__(self, owner, da, x_dim, y_dim, dims):
        super().__init__(owner, da)
        self.x_dim = x_dim
        self.y_dim = y_dim
        self.dims = dims
        assert len(dims) == 2
        self.order = ("x", "y") if dims == (x_dim, y_dim) else ("y", "x")

    def keys(self):
        return tuple(self.order), tuple(self.dims), tuple([self.owner._ds.sizes[d] for d in self.dims])

    def to_xy(self, **kwargs):
        x, y = self.find_var_or_coord(GEOGRAPHIC_COORDS["x"], GEOGRAPHIC_COORDS["y"])
        if x is None or y is None:
            raise ValueError(f"Could not find xy coordinates for variable={self.da.name}")

        return self._xy(x, y, **kwargs)

    def to_latlon(self, **kwargs):
        x, y = self.find_var_or_coord(
            GEOGRAPHIC_COORDS_LATLON_FIRST["x"], GEOGRAPHIC_COORDS_LATLON_FIRST["y"]
        )

        # print(f"x: {x}, y: {y}")
        # print(f"x.dims: {x.dims}, y.dims: {y.dims}")
        # print(f"self.dims: {self.dims}")
        # print(f"da.dims: {self.da.dims}")

        if x is None or y is None:
            raise ValueError(f"Could not find latlon coordinates for variable={self.da.name}")

        x, y = self._xy(x, y, **kwargs)
        return y, x

    def find_var_or_coord(self, x_keys, y_keys):
        for x_key, y_key in zip(x_keys, y_keys):
            if x_key in self.da.coords and y_key in self.da.coords:
                x = self.da.coords[x_key]
                y = self.da.coords[y_key]
                return x, y
            if x_key in self.owner._ds and y_key in self.owner._ds:
                x = self.owner._ds[x_key]
                y = self.owner._ds[y_key]
                return x, y
        return None, None

    def _xy(self, x, y, **kwargs):
        points = dict()

        # lat-lon variable/coordinate available with the dims
        if x.dims[-2:] == self.dims and y.dims[-2:] == self.dims:
            points["y"] = y.data
            points["x"] = x.data
            return self._output(points, **kwargs)
        # lat-lon meshgrid
        elif y.dims[-1] == self.y_dim and x.dims[-1] == self.x_dim:
            key = ("grid_points", tuple(self.order), tuple(self.dims))
            if key in self.owner._cache:
                points = self.owner._cache[key]
                return self._output(points, **kwargs)
            else:
                if self.order == ("y", "x"):
                    v1, v0 = x, y
                else:
                    v1, v0 = y, x

                points[self.order[1]], points[self.order[0]] = np.meshgrid(v1, v0)
                self.owner._cache[key] = points
                return self._output(points, **kwargs)

        raise ValueError(f"Could not find lat-lon coordinates for {self.da.name}")

    @property
    def shape(self):
        return tuple([self.owner._ds.sizes[v] for v in self.dims])


class PointCoverage(Coverage):
    def __init__(self, owner, da, x, y, dim, var_coord=True):
        super().__init__(owner, da)
        self.x = x
        self.y = y
        self.dim = dim
        self.var_coord = var_coord

    def keys(self):
        return tuple([self.x, self.y, self.dim])

    def to_latlon(self, **kwargs):
        x, y = self.to_xy(**kwargs)
        return y, x

    def to_xy(self, **kwargs):
        points = dict()

        if self.var_coord:
            x = self.da.coords[self.x].data
            y = self.da.coords[self.y].data
        else:
            x = self.owner._ds[self.x].data
            y = self.owner._ds[self.y].data

        points["y"] = y
        points["x"] = x
        return self._output(points, **kwargs)

    @property
    def shape(self):
        v = self.owner._ds.sizes[self.dim]
        return (v,)


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

        cov = Coverage.make(self, data_array)
        return cov.bbox()

        # keys, coords = self._get_xy_coords(data_array)
        # key = ("bbox", tuple(keys), tuple(coords))
        # if key in self._cache:
        #     return self._cache[key]

        # lons = self._get_xy(data_array, "x", flatten=False)
        # lats = self._get_xy(data_array, "y", flatten=False)

        # lats, lons = self._get_latlon(data_array, flatten=False)

        # north = np.amax(lats)
        # west = np.amin(lons)
        # south = np.amin(lats)
        # east = np.amax(lons)

        # self._cache[key] = (north, west, south, east)
        # return self._cache[key]

    def _get_shape(self, data_array):
        cov = Coverage.make(self, data_array)
        return cov.shape

    def _get_xy(self, data_array, flatten=False, dtype=None):
        cov = Coverage.make(self, data_array)
        return cov.to_xy(flatten=flatten, dtype=dtype)

    def _get_latlon(self, data_array, flatten=False, dtype=None):
        cov = Coverage.make(self, data_array)
        return cov.to_latlon(flatten=flatten, dtype=dtype)

    # def _get_xy_coords(self, data_array):
    #     if (
    #         len(data_array.dims) >= 2
    #         and data_array.dims[-1] in GEOGRAPHIC_COORDS["x"]
    #         and data_array.dims[-2] in GEOGRAPHIC_COORDS["y"]
    #     ):
    #         return ("y", "x"), (data_array.dims[-2], data_array.dims[-1])

    #     keys = []
    #     coords = []
    #     axes = ("x", "y")
    #     for dim in data_array.dims:
    #         for ax in axes:
    #             candidates = GEOGRAPHIC_COORDS.get(ax, [])
    #             if dim in candidates:
    #                 keys.append(ax)
    #                 coords.append(dim)
    #             else:
    #                 ax = data_array.coords[dim].attrs.get("axis", "").lower()
    #                 if ax in axes:
    #                     keys.append(ax)
    #                     coords.append(dim)
    #         if len(keys) == 2:
    #             return tuple(keys), tuple(coords)

    #     for ax in axes:
    #         if ax not in keys:
    #             raise ValueError(f"No coordinate found with axis '{ax}'")

    #     return keys, coords

    # def _get_xy(self, data_array, flatten=False, dtype=None):
    #     keys, coords = self._get_xy_coords(data_array)
    #     key = ("grid_points", tuple(keys), tuple(coords))

    #     if key in self._cache:
    #         points = self._cache[key]
    #     else:
    #         points = dict()
    #         v0, v1 = data_array.coords[coords[0]], data_array.coords[coords[1]]
    #         points[keys[1]], points[keys[0]] = np.meshgrid(v1, v0)
    #         self._cache[key] = points

    #     if flatten:
    #         points["x"] = points["x"].reshape(-1)
    #         points["y"] = points["y"].reshape(-1)

    #     if dtype is not None:
    #         return points["x"].astype(dtype), points["y"].astype(dtype)
    #     else:
    #         return points["x"], points["y"]

    # def _get_latlon(self, data_array, flatten=False, dtype=None):
    #     keys, coords = self._get_xy_coords(data_array)

    #     points = dict()

    #     def _get_ll(keys):
    #         for key in keys:
    #             if key in self._ds:
    #                 return self._ds[key]

    #     lat_keys = ["latitude", "lat"]
    #     lon_keys = ["longitude", "lon"]
    #     latitude = _get_ll(lat_keys)
    #     longitude = _get_ll(lon_keys)

    #     if latitude is not None and longitude is not None:
    #         if latitude.dims == coords and longitude.dims == coords:
    #             latitude = latitude.data
    #             longitude = longitude.data
    #             points["y"] = latitude
    #             points["x"] = longitude

    #     if not points:
    #         key = ("grid_points", tuple(keys), tuple(coords))

    #         if key in self._cache:
    #             points = self._cache[key]
    #         else:
    #             v0, v1 = data_array.coords[coords[0]], data_array.coords[coords[1]]
    #             points[keys[1]], points[keys[0]] = np.meshgrid(v1, v0)
    #             self._cache[key] = points

    #     if flatten:
    #         points["x"] = points["x"].reshape(-1)
    #         points["y"] = points["y"].reshape(-1)

    #     if dtype is not None:
    #         return points["y"].astype(dtype), points["x"].astype(dtype)
    #     else:
    #         return points["y"], points["x"]
