# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from math import prod

import numpy as np

from earthkit.data.field.part.geography import BaseGeography
from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.utils.projections import Projection

LOG = logging.getLogger(__name__)


def uniform_resolution(vals):
    if len(vals) > 1:
        delta = np.diff(vals)
        if np.allclose(delta, delta[0]):
            return delta[0]
    return None


def create_geography(metadata, shape_hint=None):
    lat = metadata.get("latitudes", None)
    lon = metadata.get("longitudes", None)

    expected_size = prod(shape_hint) if shape_hint else None

    distinct = False
    if lat is None or lon is None:
        lat = metadata.get("distinctLatitudes", None)
        lon = metadata.get("distinctLongitudes", None)

        # it is possible to have no geography at all.
        if lat is None and lon is None:
            return NoGeography(shape_hint)

        if shape_hint is None:
            if lat is None:
                raise ValueError("No latitudes or distinctLatitudes found")
            if lon is None:
                raise ValueError("No longitudes or distinctLongitudes found")

            lat = np.asarray(lat, dtype=float)
            lon = np.asarray(lon, dtype=float)

            if len(lat.shape) != 1:
                raise ValueError(f"distinct latitudes must be 1D array! shape={lat.shape} unsupported")
            if len(lon.shape) != 1:
                raise ValueError(f"distinctLongitudes must be 1D array! shape={lon.shape} unsupported")
            distinct = True
        else:
            if lat is not None and lon is not None:
                lat = np.asarray(lat, dtype=float)
                lon = np.asarray(lon, dtype=float)

                if len(lat.shape) != 1:
                    raise ValueError(f"distinct latitudes must be 1D array! shape={lat.shape} unsupported")
                if len(lon.shape) != 1:
                    raise ValueError(f"distinctLongitudes must be 1D array! shape={lon.shape} unsupported")
                if lat.size * lon.size != expected_size:
                    raise ValueError(
                        (
                            "Distinct latitudes and longitudes do not match number of values. "
                            f"Expected number=({lat.size * lon.size}), got={expected_size}"
                        )
                    )
                distinct = True

            else:
                lat = None
                lon = None
    else:
        lat = np.asarray(lat, dtype=float)
        lon = np.asarray(lon, dtype=float)
        if expected_size is not None:
            if lat.size * lon.size == expected_size:
                if len(lat.shape) != 1:
                    raise ValueError(
                        f"latitudes must be a 1D array when holding distinct values! shape={lat.shape} unsupported"
                    )
                if len(lon.shape) != 1:
                    raise ValueError(
                        f"longitudes must be a 1D array when holding distinct values! shape={lon.shape} unsupported"
                    )
                distinct = True

    assert lat is not None and lon is not None

    if distinct:
        dx = uniform_resolution(lon)
        dy = uniform_resolution(lat)

        if dx is not None and dy is not None:
            # metadata["DxInDegrees"] = dx
            # metadata["DyInDegrees"] = dy
            return RegularDistinctLLGeography(metadata)
        else:
            return DistinctLLGeography(metadata)
    else:
        if lat.shape != lon.shape:
            raise ValueError(f"latitudes and longitudes must have the same shape. {lat.shape} != {lon.shape}")

        if shape_hint is not None:
            if lat.size == expected_size:
                if lat.shape != shape_hint:
                    shape = lat.shape if lat.ndim > len(shape_hint) else shape_hint
                else:
                    shape = lat.shape

                return UserGeography(metadata, shape=shape)

            else:
                raise ValueError(
                    (
                        "Number of points do not match expected size. "
                        f"Expected=({expected_size}), got={lat.size}"
                    )
                )
        else:
            shape = lat.shape
            return UserGeography(metadata, shape=shape)


class NoGeography(BaseGeography):
    def __init__(self, shape):
        self._shape = shape

    @property
    def latitudes(self):
        return None

    @property
    def longitudes(self):
        return None

    @property
    def distinct_latitudes(self):
        return None

    @property
    def distinct_longitudes(self):
        return None

    @property
    def x(self):
        raise NotImplementedError("x is not implemented for this geography")

    @property
    def y(self):
        raise NotImplementedError("y is not implemented for this geography")

    @property
    def shape(self):
        return self._shape

    @property
    def unique_grid_id(self):
        return self.shape

    @property
    def projection(self):
        return None

    @property
    def bounding_box(self):
        return None

    def grid_spec(self):
        return None

    def resolution(self):
        return None
        # raise NotImplementedError("resolution is not implemented for this geography")

    def mars_area(self):
        return None

    def mars_grid(self):
        raise NotImplementedError("mars_grid is not implemented for this geography")

    @property
    def grid_type(self):
        return "none"


class UserGeography(BaseGeography):
    def __init__(self, metadata, shape=None):
        self.metadata = metadata
        self._shape = shape

    @property
    def latitudes(self):
        v = self.metadata.get("latitudes")
        v = np.asarray(v)
        return v
        # if dtype is None:
        #     return v
        # else:
        #     return v.astype(dtype)

    @property
    def longitudes(self):
        v = self.metadata.get("longitudes")
        v = np.asarray(v)
        return v
        # if dtype is None:
        #     return v
        # else:
        #     return v.astype(dtype)

    @property
    def distinct_latitudes(self):
        return None

    @property
    def distinct_longitudes(self):
        return None

    @property
    def x(self):
        raise NotImplementedError("x is not implemented for this geography")

    @property
    def y(self):
        raise NotImplementedError("y is not implemented for this geography")

    @property
    def shape(self):
        if self._shape is not None:
            return self._shape
        return self.latitudes.shape

    @property
    def unique_grid_id(self):
        return self.shape

    def north(self):
        return np.amax(self.latitudes)

    def south(self):
        return np.amin(self.latitudes)

    def west(self):
        return np.amin(self.longitudes)

    def east(self):
        return np.amax(self.longitudes)

    @property
    def projection(self):
        return Projection.from_proj_string(self.metadata.get("projTargetString", None))

    @property
    def bounding_box(self):
        return BoundingBox(
            north=self.north(),
            south=self.south(),
            west=self.west(),
            east=self.east(),
        )

    def grid_spec(self):
        return None

    def resolution(self):
        return None
        # raise NotImplementedError("resolution is not implemented for this geography")

    def mars_area(self):
        return [self.north(), self.west(), self.south(), self.east()]

    def mars_grid(self):
        raise NotImplementedError("mars_grid is not implemented for this geography")

    @property
    def grid_type(self):
        return "_unstructured"


class DistinctLLGeography(UserGeography):
    def __init__(self, metadata):
        super().__init__(metadata)

    @property
    def latitudes(self):
        lat = self.distinct_latitudes
        n_lon = len(self.distinct_longitudes)
        v = np.repeat(lat[:, np.newaxis], n_lon, axis=1)
        return v
        # if np.dtype is None:
        #     return v
        # else:
        #     return v.astype(np.dtype)

    @property
    def longitudes(self):
        lon = self.distinct_longitudes
        n_lat = len(self.distinct_latitudes)
        v = np.repeat(lon[np.newaxis, :], n_lat, axis=0)
        return v
        # if dtype is None:
        #     return v
        # else:
        #     return v.astype(dtype)

    @property
    def distinct_latitudes(self):
        v = self.metadata.get("latitudes", None)
        if v is None:
            v = self.metadata.get("distinctLatitudes", None)
        if v is None:
            raise ValueError("No latitudes found")
        return np.asarray(v)

    @property
    def distinct_longitudes(self):
        v = self.metadata.get("longitudes", None)
        if v is None:
            v = self.metadata.get("distinctLongitudes", None)
        if v is None:
            raise ValueError("No longitudes found")
        return np.asarray(v)

    @property
    def shape(self):
        Nj = len(self.distinct_latitudes)
        Ni = len(self.distinct_longitudes)
        return (Nj, Ni)

    @property
    def grid_type(self):
        return "_distinct_ll"


class RegularDistinctLLGeography(DistinctLLGeography):
    def dx(self):
        x = self.metadata.get("DxInDegrees", None)
        if x is None:
            lon = self._distinct_longitudes()
            x = lon[1] - lon[0]
        x = abs(round(x * 1_000_000) / 1_000_000)
        return x

    def dy(self):
        y = self.metadata.get("DyInDegrees", None)
        if y is None:
            lat = self._distinct_latitudes()
            y = lat[0] - lat[1]
        y = abs(round(y * 1_000_000) / 1_000_000)
        return y

    def resolution(self):
        x = self.dx()
        y = self.dy()
        if x == y:
            return x

    def mars_grid(self):
        return [self.dx(), self.dy()]

    @property
    def grid_type(self):
        return "_regular_ll"
