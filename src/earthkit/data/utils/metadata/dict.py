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
from earthkit.data.core.metadata import MetadataAccessor
from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.utils.dates import datetime_from_grib
from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.dates import to_timedelta
from earthkit.data.utils.projections import Projection

LOG = logging.getLogger(__name__)


def uniform_resolution(vals):
    if len(vals) > 1:
        delta = np.diff(vals)
        if np.allclose(delta, delta[0]):
            return delta[0]
    return None


def make_geography(metadata):
    lat = metadata.get("latitudes", None)
    lon = metadata.get("longitudes", None)
    val = metadata.get("values")

    # lat = np.asarray(lat, dtype=float)
    # lon = np.asarray(lon, dtype=float)

    val = np.asarray(val, dtype=float)

    distinct = False
    if lat is None or lon is None:
        lat = metadata.get("distinctLatitudes", None)
        lon = metadata.get("distinctLongitudes", None)
        lat = np.asarray(lat, dtype=float)
        lon = np.asarray(lon, dtype=float)
        if lat is None:
            raise ValueError("No latitudes or distinctLatitudes found")
        if lon is None:
            raise ValueError("No longitudes or distinctLongitudes found")
        if len(lat.shape) != 1:
            raise ValueError(f"distinct latitudes must be 1D array! shape={lat.shape} unsupported")
        if len(lon.shape) != 1:
            raise ValueError(f"distinctLongitudes must be 1D array! shape={lon.shape} unsupported")
        if lat.size * lon.size != val.size:
            raise ValueError(
                (
                    "Distinct latitudes and longitudes do not match number of values. "
                    f"Expected number=({lat.size * lon.size}), got={val.size}"
                )
            )

        distinct = True
    else:
        lat = np.asarray(lat, dtype=float)
        lon = np.asarray(lon, dtype=float)
        if lat.size * lon.size == val.size:
            if len(lat.shape) != 1:
                raise ValueError(
                    f"latitudes must be a 1D array when holding distinct values! shape={lat.shape} unsupported"
                )
            if len(lon.shape) != 1:
                raise ValueError(
                    f"longitudes must be a 1D array when holding distinct values! shape={lon.shape} unsupported"
                )
            distinct = True

    assert lat is not None
    assert lon is not None

    if distinct:
        dx = uniform_resolution(lon)
        dy = uniform_resolution(lat)

        if dx is not None and dy is not None:
            # metadata["DxInDegrees"] = dx
            # metadata["DyInDegrees"] = dy
            return RegularDistinctLLGeography(metadata)
        else:
            return DistinctLLGeography(metadata)

    if lat.shape != lon.shape:
        raise ValueError(f"latitudes and longitudes must have the same shape. {lat.shape} != {lon.shape}")

    if lat.size == val.size:
        if lat.shape != val.shape:
            shape = lat.shape if lat.ndim > val.ndim else val.shape
        else:
            shape = lat.shape

        return UserGeography(metadata, shape=shape)

    else:
        raise ValueError(
            (
                "latitudes and longitudes do not match number of values. "
                f"Expected number=({lat.size * lon.size}), got={val.size}"
            )
        )


class UserGeography(Geography):
    def __init__(self, metadata, shape=None):
        self.metadata = metadata
        self._shape = shape

    def latitudes(self, dtype=None):
        v = self.metadata.get("latitudes")
        v = np.asarray(v)
        if dtype is None:
            return v
        else:
            return v.astype(dtype)

    def longitudes(self, dtype=None):
        v = self.metadata.get("longitudes")
        v = np.asarray(v)
        if dtype is None:
            return v
        else:
            return v.astype(dtype)

    def x(self, dtype=None):
        raise NotImplementedError("x is not implemented for this geography")

    def y(self, dtype=None):
        raise NotImplementedError("y is not implemented for this geography")

    def shape(self):
        if self._shape is not None:
            return self._shape
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
        return None
        # raise NotImplementedError("resolution is not implemented for this geography")

    def mars_area(self):
        return [self.north(), self.west(), self.south(), self.east()]

    def mars_grid(self):
        raise NotImplementedError("mars_grid is not implemented for this geography")


# class StructuredGeography(UserGeography):
#     pass


class DistinctLLGeography(UserGeography):
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


class UserMetadata(Metadata):
    ALIASES = [
        ("dataDate", "date"),
        ("dataTime", "time"),
        ("forecast_reference_time", "base_datetime"),
        ("level", "levelist"),
        ("step", "endStep", "stepRange"),
        ("param", "shortName"),
    ]

    ACCESSORS = {
        "base_datetime": "base_datetime",
        "valid_datetime": "valid_datetime",
        "step_timedelta": "step_timedelta",
        "param_level": "param_level",
    }

    LS_KEYS = ["param", "level", "base_datetime", "valid_datetime", "step", "number"]

    def __init__(self, d, values=None):
        self._data = d

    def __len__(self):
        return len(self._data)

    def __contains__(self, key):
        return key in self._data

    def __getitem__(self, key):
        return self.get(key, raise_on_missing=True)

    def __iter__(self):
        return iter(self._keys())

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()

    @MetadataAccessor(ACCESSORS, ALIASES)
    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        def _key_name(key):
            if key in self._data:
                return key
            else:
                for group in self.ALIASES:
                    if key in group:
                        for k in group:
                            if k in self._data:
                                return k

        key_n = _key_name(key)
        if key_n is None:
            if raise_on_missing:
                raise KeyError(f"Key={key} not found")
            return default

        v = self._data[key_n]
        if astype is None:
            return v
        else:
            return astype(v)

    def datetime(self):
        return {
            "base_time": self.base_datetime(),
            "valid_time": self.valid_datetime(),
        }

    def base_datetime(self):
        v = self._get_one(["base_datetime", "forecast_reference_time"])
        if v is not None:
            v = to_datetime(v)
            return v

        v = self._datetime("date", "time")
        if v is not None:
            return v

        v = self.step_timedelta()
        if v is not None:
            return self.valid_datetime() - v

    def valid_datetime(self):
        if "valid_datetime" in self._data:
            v = self._data["valid_datetime"]
            v = to_datetime(v)
            return v

        base_dt = self.base_datetime()
        if base_dt is not None:
            td = self.step_timedelta()
            if td is not None:
                return base_dt + td
            return base_dt

    def step_timedelta(self):
        if "step_timedelta" in self._data:
            return self._data["step_timedelta"]
        v = self._get_one(["endStep", "step"])
        if v is not None:
            return to_timedelta(v)

    def _datetime(self, date_key, time_key):
        date = self.get(date_key, None)
        if date is not None:
            time = self.get(time_key, None)
            if time is not None:
                return datetime_from_grib(date, time)
        return None

    def param_level(self):
        return f"{self.get('param')}{self.get('level', default='')}"

    def _get_one(self, keys):
        for k in keys:
            if k in self._data:
                return self._data[k]

    @cached_property
    def geography(self):
        return make_geography(self)

    def override(self, *args, **kwargs):
        raise NotImplementedError("override is not implemented for UserMetadata")

    def namespaces(self):
        return []

    def as_namespace(self, namespace=None):
        return {}

    def dump(self, **kwargs):
        return None

    def ls_keys(self):
        return self.LS_KEYS

    def describe_keys(self):
        return []

    def index_keys(self):
        return None

    def data_format(self):
        return "dict"

    def _hide_internal_keys(self):
        return self
