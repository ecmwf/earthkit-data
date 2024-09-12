# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import logging
import warnings
from functools import cached_property

import numpy as np

from earthkit.data.core.fieldlist import Field
from earthkit.data.core.geography import Geography
from earthkit.data.core.metadata import RawMetadata
from earthkit.data.readers.grib.index import GribFieldList
from earthkit.data.readers.grib.metadata import GribMetadata
from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.utils.dates import step_to_delta
from earthkit.data.utils.projections import Projection

LOG = logging.getLogger(__name__)


def make_geography(metadata):
    if "gridType" not in metadata:
        lat = metadata.get("latitudes", None)
        lon = metadata.get("longitudes", None)
        val = metadata.get("values")

        distinct = False
        if lat is None or lon is None:
            lat = metadata.get("distinctLatitudes", None)
            lon = metadata.get("distinctLongitudes", None)

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
            if lat.ndim == 2:
                return StructuredGeography(metadata)
            return UnstructuredGeography(metadata)
        raise ValueError("Unsupported metadata")
    else:
        return VirtualGribGeography(metadata)


class VirtualGeography(Geography):
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
        # return make_gridspec(self.metadata)

    def resolution(self):
        raise NotImplementedError("resolution is not implemented for this geography")

    def mars_area(self):
        return [self.north(), self.west(), self.south(), self.east()]

    def mars_grid(self):
        raise NotImplementedError("mars_grid is not implemented for this geography")


class RegularDistinctLLGeography(VirtualGeography):
    def __init__(self, metadata):
        super().__init__(metadata)

    def _distinct_latitudes(self):
        v = self.metadata.get("latitudes", None)
        if v is None:
            v = self.metadata.get("distinctLatitudes", None)
        if v is None:
            raise ValueError("No latitudes found")
        return v

    def _distinct_longitudes(self):
        v = self.metadata.get("longitudes", None)
        if v is None:
            v = self.metadata.get("distinctLongitudes", None)
        if v is None:
            raise ValueError("No longitudes found")
        return v

    def latitudes(self, dtype=None):
        lat = self._distinct_latitudes()
        n_lon = len(self._distinct_longitudes())
        v = np.repeat(lat[: np.newaxis], n_lon, 1)

        if dtype is None:
            return v
        else:
            return v.astype(dtype)

    def longitudes(self, dtype=None):
        lon = self._distinct_longitudes()
        n_lat = len(self._distinct_latitudes())
        v = np.repeat(lon[np.newaxis, :], n_lat, 0)

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
            lon = self._distinct_latitudes()
            x = lon[1] - lon[0]
        x = round(x * 1_000_000) / 1_000_000
        return x

    def dy(self):
        y = self.metadata.get("DyInDegrees", None)
        if y is None:
            lat = self._distinct_latitudes()
            y = lat[0] - lat[1]
        y = round(y * 1_000_000) / 1_000_000
        return y

    def resolution(self):
        x = self.dx()
        y = self.dy()
        assert x == y, (x, y)
        return x

    def mars_grid(self):
        return [self.dx(), self.dy()]


class StructuredGeography(VirtualGeography):
    def __init__(self, metadata):
        super().__init__(metadata)
        assert metadata.get("latitudes").ndim == 2
        assert metadata.get("longitudes").ndim == 2
        assert metadata.get("values").ndim == 2

    # def resolution(self):
    #     raise NotImplementedError("resolution is not implemented for structured grids")


class UnstructuredGeography(VirtualGeography):
    def __init__(self, metadata):
        super().__init__(metadata)
        assert metadata.get("latitudes").ndim == 1
        assert metadata.get("longitudes").ndim == 1
        assert metadata.get("values").ndim == 1

    # def resolution(self):
    #     raise NotImplementedError("resolution is not implemented for structured grids")


class VirtualGribGeography(VirtualGeography):
    def __init__(self, metadata):
        super().__init__(metadata)
        self.check_rotated_support()

    def x(self, dtype=None):
        grid_type = self.metadata.get("gridType", None)
        if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
            return self.longitudes(dtype=dtype)

    def y(self, dtype=None):
        grid_type = self.metadata.get("gridType", None)
        if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
            return self.latitudes(dtype=dtype)

    def shape(self):
        Nj = self.metadata.get("Nj", None)
        Ni = self.metadata.get("Ni", None)
        if Ni is None or Nj is None:
            n = len(self.metadata.get("values"))
            return (n,)  # shape must be a tuple
        return (Nj, Ni)

    def _unique_grid_id(self):
        v = self.metadata.get("md5GridSection", None)
        if v is None:
            v = (self.metadata.get("gridType"), self.shape())
        return v

    def north(self):
        v = self.metadata.get("latitudeOfFirstGridPointInDegrees", None)
        if v is None:
            v = np.amax(self.latitudes())
        return v

    def south(self):
        v = self.metadata.get("latitudeOfLastGridPointInDegrees", None)
        if v is None:
            v = np.amin(self.latitudes())
        return v

    def west(self):
        v = self.metadata.get("longitudeOfFirstGridPointInDegrees", None)
        if v is None:
            v = np.amin(self.longitudes())
        return v

    def east(self):
        v = self.metadata.get("longitudeOfLastGridPointInDegrees", None)
        if v is None:
            v = np.amax(self.longitudes())
        return v

    def projection(self):
        return Projection.from_proj_string(self.metadata.get("projTargetString", None))

    # def bounding_box(self):
    #     return BoundingBox(
    #         north=self.north(),
    #         south=self.south(),
    #         west=self.west(),
    #         east=self.east(),
    #     )

    # def gridspec(self):
    #     return None
    #     # return make_gridspec(self.metadata)

    def resolution(self):
        grid_type = self.metadata.get("gridType")

        if grid_type in ("reduced_gg", "reduced_rotated_gg"):
            return self.metadata.get("gridName")

        if grid_type in ("regular_ll", "rotated_ll"):
            x = self.metadata.get("DxInDegrees")
            y = self.metadata.get("DyInDegrees")
            x = round(x * 1_000_000) / 1_000_000
            y = round(y * 1_000_000) / 1_000_000
            assert x == y, (x, y)
            return x

        if grid_type == "lambert":
            x = self.metadata.get("DxInMetres")
            y = self.metadata.get("DyInMetres")
            assert x == y, (x, y)
            return str(x / 1000).replace(".", "p") + "km"

        raise ValueError(f"Unknown gridType={grid_type}")

    def mars_grid(self):
        if len(self.shape()) == 2:
            return [
                self.metadata.get("iDirectionIncrementInDegrees"),
                self.metadata.get("jDirectionIncrementInDegrees"),
            ]

        return self.metadata.get("gridName")

    # def mars_area(self):
    #     north = self.metadata.get("latitudeOfFirstGridPointInDegrees")
    #     south = self.metadata.get("latitudeOfLastGridPointInDegrees")
    #     west = self.metadata.get("longitudeOfFirstGridPointInDegrees")
    #     east = self.metadata.get("longitudeOfLastGridPointInDegrees")
    #     return [north, west, south, east]

    @property
    def rotation(self):
        return (
            self.metadata.get("latitudeOfSouthernPoleInDegrees"),
            self.metadata.get("longitudeOfSouthernPoleInDegrees"),
            self.metadata.get("angleOfRotationInDegrees"),
        )

    @cached_property
    def rotated(self):
        grid_type = self.metadata.get("gridType")
        return "rotated" in grid_type

    @cached_property
    def rotated_iterator(self):
        return self.metadata.get("iteratorDisableUnrotate") is not None

    def check_rotated_support(self):
        if self.rotated and self.metadata.get("gridType") == "reduced_rotated_gg":
            from earthkit.data.utils.message import ECC_FEATURES

            if not ECC_FEATURES.version >= (2, 35, 0):
                raise RuntimeError("gridType=rotated_reduced_gg requires ecCodes >= 2.35.0")

    def latitudes_unrotated(self, **kwargs):
        if not self.rotated:
            return self.latitudes(**kwargs)

        if not self.rotated_iterator:
            from earthkit.geo.rotate import unrotate

            grid_type = self.metadata.get("gridType")
            warnings.warn(f"ecCodes does not support rotated iterator for {grid_type}")
            lat, lon = self.latitudes(**kwargs), self.longitudes(**kwargs)
            south_pole_lat, south_pole_lon, _ = self.rotation
            lat, lon = unrotate(lat, lon, south_pole_lat, south_pole_lon)
            return lat

        with self.metadata._handle._set_tmp("iteratorDisableUnrotate", 1, 0):
            return self.latitudes(**kwargs)

    def longitudes_unrotated(self, **kwargs):
        if not self.rotated:
            return self.longitudes(**kwargs)

        if not self.rotated_iterator:
            from earthkit.geo.rotate import unrotate

            grid_type = self.metadata.get("gridType")
            warnings.warn(f"ecCodes does not support rotated iterator for {grid_type}")
            lat, lon = self.latitudes(**kwargs), self.longitudes(**kwargs)
            south_pole_lat, south_pole_lon, _ = self.rotation
            lat, lon = unrotate(lat, lon, south_pole_lat, south_pole_lon)
            return lon

        with self.metadata._handle._set_tmp("iteratorDisableUnrotate", 1, 0):
            return self.longitudes(**kwargs)


class VirtualGribMetadata(RawMetadata):
    KEY_TYPES = {
        "s": str,
        "l": int,
        "d": float,
        "str": str,
        "int": int,
        "float": float,
        "": None,
    }

    KEY_TYPE_SUFFIX = {str: ":s", int: ":l", float: ":d"}

    KEY_GROUPS = {
        ("dataDate", "date"),
        ("dataTime", "time"),
        ("level", "levelist"),
        ("step", "endStep", "stepRange"),
        ("param", "shortName"),
    }

    def __init__(self, m):
        super().__init__(m)

    def _get(self, key, astype=None, default=None, raise_on_missing=True):
        def _key_name(key):
            if key == "_param_id":
                key = "paramId"
            return key

        key = _key_name(key)
        key, _, key_type_str = key.partition(":")
        try:
            key_type = self.KEY_TYPES[key_type_str]
        except KeyError:
            raise ValueError(f"Key type={key_type_str} not supported")

        if key not in self:
            for v in self.KEY_GROUPS:
                if key in v:
                    for k in v:
                        if k in self:
                            key = k
                            break

            if key not in self and key in ("step", "endStep", "stepRange"):
                return self._default_step(astype=astype)

        if key_type is None:
            key_type = astype

        if key == "stepRange" and key_type is None:
            key_type = str

        return super()._get(key, astype=key_type, default=default, raise_on_missing=raise_on_missing)

    def shape(self):
        Nj = self.get("Nj", None)
        Ni = self.get("Ni", None)
        if Ni is None or Nj is None:
            n = len(self.get("values"))
            return (n,)  # shape must be a tuple
        return (Nj, Ni)

    def as_namespace(self, ns):
        return {}

    def ls_keys(self):
        return GribMetadata.LS_KEYS

    def namespaces(self):
        return []

    # def latitudes(self, dtype=None):
    #     v = self.get("latitudes")
    #     if dtype is None:
    #         return v
    #     else:
    #         return v.astype(dtype)

    # def longitudes(self, dtype=None):
    #     v = self.get("longitudes")
    #     if dtype is None:
    #         return v
    #     else:
    #         return v.astype(dtype)

    # def x(self, dtype=None):
    #     grid_type = self.get("gridType", None)
    #     if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
    #         return self.longitudes(dtype=dtype)

    # def y(self, dtype=None):
    #     grid_type = self.get("gridType", None)
    #     if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
    #         return self.latitudes(dtype=dtype)

    # def _unique_grid_id(self):
    #     return self.get("md5GridSection", None)

    def datetime(self):
        return {
            "base_time": self._base_datetime(),
            "valid_time": self._valid_datetime(),
        }

    def _base_datetime(self):
        date = int(self.get("date", None))
        time = int(self.get("time", None))
        return datetime.datetime(
            date // 10000,
            date % 10000 // 100,
            date % 100,
            time // 100,
            time % 100,
        )

    def _valid_datetime(self):
        step = self.get("endStep", None)
        return self._base_datetime() + step_to_delta(step)

    def _default_step(self, astype=None):
        step = "0"
        if astype is None:
            return step
        else:
            return astype(step)

    # def projection(self):
    #     return Projection.from_proj_string(self.get("projTargetString", None))

    # def bounding_box(self):
    #     return BoundingBox(
    #         north=self.get("latitudeOfFirstGridPointInDegrees", None),
    #         south=self.get("latitudeOfLastGridPointInDegrees", None),
    #         west=self.get("longitudeOfFirstGridPointInDegrees", None),
    #         east=self.get("longitudeOfLastGridPointInDegrees", None),
    #     )

    @cached_property
    def geography(self):
        return make_geography(self)


class VirtualGribField(Field):
    def __init__(self, d, backend):
        super().__init__(backend, metadata=VirtualGribMetadata(d))

    def _values(self, dtype=None):
        v = self._metadata["values"]
        if dtype is None:
            return v
        else:
            return v.astype(dtype)


class GribFromDicts(GribFieldList):
    def __init__(self, list_of_dicts, *args, **kwargs):
        self.list_of_dicts = list_of_dicts
        super().__init__(*args, **kwargs)

    def __getitem__(self, n):
        return VirtualGribField(self.list_of_dicts[n], self.array_backend)

    def __len__(self):
        return len(self.list_of_dicts)


source = GribFromDicts
