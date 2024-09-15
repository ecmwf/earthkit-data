# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from functools import cached_property

import numpy as np

from earthkit.data.core.geography import Geography
from earthkit.data.core.metadata import Metadata
from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.utils.dates import datetime_from_grib
from earthkit.data.utils.dates import step_to_delta
from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.projections import Projection

LOG = logging.getLogger(__name__)


def make_geography(metadata):
    if "gridType" not in metadata:
        lat = metadata.get("latitudes", None)
        lon = metadata.get("longitudes", None)
        val = metadata.get("values")

        lat = np.asarray(lat, dtype=float)
        lon = np.asarray(lon, dtype=float)
        val = np.asarray(val, dtype=float)

        distinct = False
        if lat is None or lon is None:
            lat = metadata.get("distinctLatitudes", None)
            lon = metadata.get("distinctLongitudes", None)
            lat = np.asarray(lat, dtype=float)
            lon = np.asarray(lon, dtype=float)
            if lat is None:
                raise ValueError("No distinctLatitudes found")
            if lon is None:
                raise ValueError("No distinctLongitudes found")
            if len(lat.shape) != 1:
                return ValueError(f"distinct latitudes must be 1D array! shape={lat.shape} unsupported")
            if len(lon.shape) != 1:
                return ValueError(f"distinctLongitudes must be 1D array! shape={lon.shape} unsupported")

            distinct = True
        elif lat.size * lon.size == val.size:
            if len(lat.shape) != 1:
                return ValueError(
                    f"latitudes must be 1D array when holding distinct values! shape={lat.shape} unsupported"
                )
            if len(lon.shape) != 1:
                return ValueError(
                    f"longitudes must be 1D array when holding distinct values! shape={lon.shape} unsupported"
                )
            distinct = True

        if distinct:
            return RegularDistinctLLGeography(metadata)

        if lat.size == lon.size == val.size:
            if lat.shape != lon.shape or lat.shape != val.shape:
                raise ValueError(
                    (
                        "latitudes, longitudes and values must have the same "
                        f"shape! lat={lat.shape}, lon={lon.shape}, val={val.shape}"
                    )
                )
            return UserGeography(metadata)
            # if lat.ndim == 2:
            #     return StructuredGeography(metadata)
            # return UnstructuredGeography(metadata)
        raise ValueError("Unsupported metadata")
    else:
        raise
        # return VirtualGribGeography(metadata)


class UserGeography(Geography):
    def __init__(self, metadata):
        self.metadata = metadata

    def latitudes(self, dtype=None):
        v = self.metadata.get("latitudes")
        if dtype is None:
            return v
        else:
            return v.astype(dtype)

    def longitudes(self, dtype=None):
        v = self.metadata.get("longitudes")
        if dtype is None:
            return v
        else:
            return v.astype(dtype)

    def x(self, dtype=None):
        raise NotImplementedError("x is not implemented for this geography")

    def y(self, dtype=None):
        raise NotImplementedError("y is not implemented for this geography")

    def shape(self):
        return self.latitudes().shape

    def _unique_grid_id(self):
        return self.shape()

    def north(self):
        return np.amax(self.latitudes())

    def south(self):
        return np.amin(self.latitudes())

    def west(self):
        return np.amin(self.longitudes())

    def east(self):
        return np.amax(self.longitudes())

    def projection(self):
        return Projection.from_proj_string(self.metadata.get("projTargetString", None))

    def bounding_box(self):
        return BoundingBox(
            north=self.north(),
            south=self.south(),
            west=self.west(),
            east=self.east(),
        )

    def gridspec(self):
        return None

    def resolution(self):
        raise NotImplementedError("resolution is not implemented for this geography")

    def mars_area(self):
        return [self.north(), self.west(), self.south(), self.east()]

    def mars_grid(self):
        raise NotImplementedError("mars_grid is not implemented for this geography")


class RegularDistinctLLGeography(UserGeography):
    def __init__(self, metadata):
        super().__init__(metadata)

    def _distinct_latitudes(self):
        v = self.metadata.get("latitudes", None)
        if v is None:
            v = self.metadata.get("distinctLatitudes", None)
        if v is None:
            raise ValueError("No latitudes found")
        return np.asarray(v)

    def _distinct_longitudes(self):
        v = self.metadata.get("longitudes", None)
        if v is None:
            v = self.metadata.get("distinctLongitudes", None)
        if v is None:
            raise ValueError("No longitudes found")
        return np.asarray(v)

    def latitudes(self, dtype=None):
        lat = self._distinct_latitudes()
        n_lon = len(self._distinct_longitudes())
        v = np.repeat(lat[:, np.newaxis], n_lon, axis=1)

        if dtype is None:
            return v
        else:
            return v.astype(dtype)

    def longitudes(self, dtype=None):
        lon = self._distinct_longitudes()
        n_lat = len(self._distinct_latitudes())
        v = np.repeat(lon[np.newaxis, :], n_lat, axis=0)

        if dtype is None:
            return v
        else:
            return v.astype(dtype)

    def shape(self):
        Nj = len(self._distinct_latitudes())
        Ni = len(self._distinct_longitudes())
        return (Nj, Ni)

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
        assert x == y, (x, y)
        return x

    def mars_grid(self):
        return [self.dx(), self.dy()]


# class StructuredGeography(VirtualGeography):
#     def __init__(self, metadata):
#         super().__init__(metadata)
#         assert metadata.get("latitudes").ndim == 2
#         assert metadata.get("longitudes").ndim == 2
#         assert metadata.get("values").ndim == 2

#     # def resolution(self):
#     #     raise NotImplementedError("resolution is not implemented for structured grids")


# class UnstructuredGeography(VirtualGeography):
#     def __init__(self, metadata):
#         super().__init__(metadata)
#         assert metadata.get("latitudes").ndim == 1
#         assert metadata.get("longitudes").ndim == 1
#         assert metadata.get("values").ndim == 1

#     # def resolution(self):
#     #     raise NotImplementedError("resolution is not implemented for structured grids")


# class VirtualGribGeography(VirtualGeography):
#     def __init__(self, metadata):
#         super().__init__(metadata)
#         self.check_rotated_support()

#     def x(self, dtype=None):
#         grid_type = self.metadata.get("gridType", None)
#         if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
#             return self.longitudes(dtype=dtype)

#     def y(self, dtype=None):
#         grid_type = self.metadata.get("gridType", None)
#         if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
#             return self.latitudes(dtype=dtype)

#     def shape(self):
#         Nj = self.metadata.get("Nj", None)
#         Ni = self.metadata.get("Ni", None)
#         if Ni is None or Nj is None:
#             n = len(self.metadata.get("values"))
#             return (n,)  # shape must be a tuple
#         return (Nj, Ni)

#     def _unique_grid_id(self):
#         v = self.metadata.get("md5GridSection", None)
#         if v is None:
#             v = (self.metadata.get("gridType"), self.shape())
#         return v

#     def north(self):
#         v = self.metadata.get("latitudeOfFirstGridPointInDegrees", None)
#         if v is None:
#             v = np.amax(self.latitudes())
#         return v

#     def south(self):
#         v = self.metadata.get("latitudeOfLastGridPointInDegrees", None)
#         if v is None:
#             v = np.amin(self.latitudes())
#         return v

#     def west(self):
#         v = self.metadata.get("longitudeOfFirstGridPointInDegrees", None)
#         if v is None:
#             v = np.amin(self.longitudes())
#         return v

#     def east(self):
#         v = self.metadata.get("longitudeOfLastGridPointInDegrees", None)
#         if v is None:
#             v = np.amax(self.longitudes())
#         return v

#     def projection(self):
#         return Projection.from_proj_string(self.metadata.get("projTargetString", None))

#     # def bounding_box(self):
#     #     return BoundingBox(
#     #         north=self.north(),
#     #         south=self.south(),
#     #         west=self.west(),
#     #         east=self.east(),
#     #     )

#     # def gridspec(self):
#     #     return None
#     #     # return make_gridspec(self.metadata)

#     def resolution(self):
#         grid_type = self.metadata.get("gridType")

#         if grid_type in ("reduced_gg", "reduced_rotated_gg"):
#             return self.metadata.get("gridName")

#         if grid_type in ("regular_ll", "rotated_ll"):
#             x = self.metadata.get("DxInDegrees")
#             y = self.metadata.get("DyInDegrees")
#             x = round(x * 1_000_000) / 1_000_000
#             y = round(y * 1_000_000) / 1_000_000
#             assert x == y, (x, y)
#             return x

#         if grid_type == "lambert":
#             x = self.metadata.get("DxInMetres")
#             y = self.metadata.get("DyInMetres")
#             assert x == y, (x, y)
#             return str(x / 1000).replace(".", "p") + "km"

#         raise ValueError(f"Unknown gridType={grid_type}")

#     def mars_grid(self):
#         if len(self.shape()) == 2:
#             return [
#                 self.metadata.get("iDirectionIncrementInDegrees"),
#                 self.metadata.get("jDirectionIncrementInDegrees"),
#             ]

#         return self.metadata.get("gridName")

#     # def mars_area(self):
#     #     north = self.metadata.get("latitudeOfFirstGridPointInDegrees")
#     #     south = self.metadata.get("latitudeOfLastGridPointInDegrees")
#     #     west = self.metadata.get("longitudeOfFirstGridPointInDegrees")
#     #     east = self.metadata.get("longitudeOfLastGridPointInDegrees")
#     #     return [north, west, south, east]

#     @property
#     def rotation(self):
#         return (
#             self.metadata.get("latitudeOfSouthernPoleInDegrees"),
#             self.metadata.get("longitudeOfSouthernPoleInDegrees"),
#             self.metadata.get("angleOfRotationInDegrees"),
#         )

#     @cached_property
#     def rotated(self):
#         grid_type = self.metadata.get("gridType")
#         return "rotated" in grid_type

#     @cached_property
#     def rotated_iterator(self):
#         return self.metadata.get("iteratorDisableUnrotate") is not None

#     def check_rotated_support(self):
#         if self.rotated and self.metadata.get("gridType") == "reduced_rotated_gg":
#             from earthkit.data.utils.message import ECC_FEATURES

#             if not ECC_FEATURES.version >= (2, 35, 0):
#                 raise RuntimeError("gridType=rotated_reduced_gg requires ecCodes >= 2.35.0")

#     def latitudes_unrotated(self, **kwargs):
#         if not self.rotated:
#             return self.latitudes(**kwargs)

#         if not self.rotated_iterator:
#             from earthkit.geo.rotate import unrotate

#             grid_type = self.metadata.get("gridType")
#             warnings.warn(f"ecCodes does not support rotated iterator for {grid_type}")
#             lat, lon = self.latitudes(**kwargs), self.longitudes(**kwargs)
#             south_pole_lat, south_pole_lon, _ = self.rotation
#             lat, lon = unrotate(lat, lon, south_pole_lat, south_pole_lon)
#             return lat

#         with self.metadata._handle._set_tmp("iteratorDisableUnrotate", 1, 0):
#             return self.latitudes(**kwargs)

#     def longitudes_unrotated(self, **kwargs):
#         if not self.rotated:
#             return self.longitudes(**kwargs)

#         if not self.rotated_iterator:
#             from earthkit.geo.rotate import unrotate

#             grid_type = self.metadata.get("gridType")
#             warnings.warn(f"ecCodes does not support rotated iterator for {grid_type}")
#             lat, lon = self.latitudes(**kwargs), self.longitudes(**kwargs)
#             south_pole_lat, south_pole_lon, _ = self.rotation
#             lat, lon = unrotate(lat, lon, south_pole_lat, south_pole_lon)
#             return lon

#         with self.metadata._handle._set_tmp("iteratorDisableUnrotate", 1, 0):
#             return self.longitudes(**kwargs)


class UserMetadata(Metadata):
    ALIASES = [
        ("dataDate", "date"),
        ("dataTime", "time"),
        ("forecast_reference_time", "base_datetime"),
        ("level", "levelist"),
        ("step", "endStep", "stepRange"),
        ("param", "shortName"),
    ]

    LS_KEYS = ["param", "level", "base_datetime", "valid_datetime", "step", "number", set]

    def __init__(self, d, values=None):
        self._data = d

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._keys())

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    def _get(self, key, astype=None, default=None, raise_on_missing=True):
        def _key_name(key):
            if key in self._data:
                return key
            else:
                for group in self.ALIASES:
                    if key in group:
                        for k in group:
                            if k in self._data:
                                return k

        key = _key_name(key)
        if key is None:
            if raise_on_missing:
                raise KeyError(f"Key={key} not found")
            return default

        v = self._data[key]
        if astype is None:
            return v
        else:
            return astype(v)

    def base_datetime(self):
        v = self._get_one(["base_datetime", "forecast_reference_time"])
        if v is not None:
            v = to_datetime(v)
            return v

        v = self._datetime("date", "time")
        if v is not None:
            return v

    def valid_datetime(self):
        if "valid_datetime" in self._data:
            v = self._data["valid_datetime"]
            v = to_datetime(v)
            return v

        base_dt = self.base_datetime()
        if base_dt is None:
            return base_dt + self.step_timedelta()

    def step_timedelta(self):
        if "step_timedelta" in self._data:
            return self._data["step_timedelta"]
        v = self._get_one(["endStep", "step"])
        return step_to_delta(v)

    def _datetime(self, date_key, time_key):
        date = self.get(date_key, None)
        if date is not None:
            time = self.get(time_key, None)
            if time is not None:
                return datetime_from_grib(date, time)
        return None

    def _get_one(self, keys):
        for k in keys:
            if k in self._data:
                return self._data[k]

    @cached_property
    def geography(self):
        return make_geography(self)

    def override(self, *args, **kwargs):
        raise NotImplementedError("override is not implemented for UserFieldMetadata")
