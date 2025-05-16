# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import math

import numpy as np

LOG = logging.getLogger(__name__)


# TODO: refactor this when earthkit.geo grid support is implemented
class Grid:
    def __init__(self, field):
        self.field = field

    @staticmethod
    def make(field):
        # NOTE: underscore grid types are coming from UserMetadata
        grid_type = field.metadata("gridType", default=None)

        if grid_type in ["regular_ll", "_regular_ll"]:
            return RegularLLGrid(field)
        elif grid_type in ["regular_gg", "mercator", "_rectified_ll"]:
            return RectifiedLLGrid(field)
        elif grid_type in ["sh"]:
            return SpectralGrid(field)
        elif grid_type is None or grid_type == "none":
            return NonGrid(field)
        elif grid_type == "_unstructured":
            return Grid(field)
        else:
            return Grid(field)

    def to_distinct_latlon(self, field_shape):
        return None, None

    def to_latlon(self, field_shape=None):
        ll = self.field.to_latlon(flatten=True)
        lat = np.atleast_1d(ll["lat"])
        lon = np.atleast_1d(ll["lon"])

        if field_shape is not None:
            lat = lat.reshape(field_shape)
            lon = lon.reshape(field_shape)
        return lat, lon

    def is_spectral(self):
        return False


class RegularLLGrid(Grid):
    def to_distinct_latlon(self, field_shape):
        assert len(field_shape) == 2
        assert field_shape == self.field.shape
        lat, lon = self.to_latlon()
        _, nx = field_shape
        lat = lat[::nx]
        lon = lon[:nx]
        return lat, lon


class RectifiedLLGrid(Grid):
    def to_distinct_latlon(self, field_shape):
        geo = self.field.metadata().geography
        lat = np.atleast_1d(geo.distinct_latitudes())
        if len(lat) == field_shape[0]:
            lon = np.atleast_1d(geo.distinct_longitudes())
            if len(lon) == field_shape[1]:
                return lat, lon
        return None, None


class SpectralGrid(Grid):
    def to_latlon(self, field_shape=None):
        return None, None

    def is_spectral(self):
        return True


class NonGrid(Grid):
    def to_latlon(self, field_shape=None):
        return None, None

    def is_spectral(self):
        return False


class TensorGrid:
    def __init__(self, field, flatten_values=False):
        self.dims, self.coords, self.coords_dim = self.build(field, flatten_values)

    @staticmethod
    def build(field, flatten_values):
        field_shape = field.shape

        if flatten_values:
            field_shape = (math.prod(field_shape),)

        assert isinstance(field_shape, tuple), (
            field_shape,
            field,
        )

        coords = {}
        dims = {}
        coords_dim = {}

        grid = Grid.make(field)
        if grid.is_spectral():
            if len(field_shape) == 1:
                dims["values"] = field_shape[0]
        else:
            if len(field_shape) == 1:
                dims["values"] = field_shape[0]
                try:
                    lat, lon = grid.to_latlon()
                    if lat is not None and lon is not None:
                        coords["latitude"] = lat
                        coords["longitude"] = lon
                        coords_dim = {k: ("values",) for k in coords}
                except Exception:
                    pass
            elif len(field_shape) == 2:
                try:
                    lat, lon = grid.to_distinct_latlon(field_shape)
                    if (
                        lat is not None
                        and lon is not None
                        and len(lat) == field_shape[0]
                        and len(lon) == field_shape[1]
                    ):
                        coords["latitude"] = lat
                        coords["longitude"] = lon
                        coords_dim["latitude"] = ("latitude",)
                        coords_dim["longitude"] = ("longitude",)
                        dims["latitude"] = lat.size
                        dims["longitude"] = lon.size
                        assert coords["latitude"].size == field_shape[0]
                        assert coords["longitude"].size == field_shape[1]
                        assert dims["latitude"] == field_shape[0]
                        assert dims["longitude"] == field_shape[1]
                except Exception as e:
                    print(e)
                    pass

                if not coords or not dims:
                    lat, lon = grid.to_latlon(field_shape)
                    if lat is not None and lon is not None:
                        coords["latitude"] = lat
                        coords["longitude"] = lon
                        coords_dim = {k: ("y", "x") for k in coords}
                        dims["y"] = field_shape[0]
                        dims["x"] = field_shape[1]
                        assert coords["latitude"].shape == field_shape
                        assert coords["longitude"].shape == field_shape
            else:
                raise ValueError(f"Unsupported field shape {field_shape}")

        # if hasattr(field, "unload"):
        #     field.unload()

        for k, v in coords.items():
            assert k in coords_dim, f"{k=}, {coords_dim=}"
            assert all(x in dims for x in coords_dim[k]), f"{k=}, {coords_dim=} {dims=}"
            assert v.size == math.prod([dims[x] for x in coords_dim[k]])

        return dims, coords, coords_dim
