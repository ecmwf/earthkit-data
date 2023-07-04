# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

# The code is copied from skinnywms, and we should combile later

import datetime
from contextlib import closing
from itertools import product

import numpy as np
import xarray as xr

from earthkit.data.core import Base
from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.utils.dates import to_datetime
from earthkit.data.utils.projections import Projection

from . import Reader

GEOGRAPHIC_COORDS = {
    "x": ["x", "projection_x_coordinate", "lon", "longitude"],
    "y": ["y", "projection_y_coordinate", "lat", "latitude"],
}


def as_datetime(self, time):
    return datetime.datetime.strptime(str(time)[:19], "%Y-%m-%dT%H:%M:%S")


def as_level(self, level):
    n = float(level)
    if int(n) == n:
        return int(n)
    return n


class Slice:
    def __init__(self, name, value, index, is_dimension, is_info):
        self.name = name
        self.index = index
        self.value = value
        self.is_dimension = (not is_info,)
        self.is_info = is_info

    def __repr__(self):
        return "[%s:%s=%s]" % (self.name, self.index, self.value)


class TimeSlice(Slice):
    pass


class Coordinate:
    def __init__(self, variable, info):
        self.variable = variable
        # We only support 1D coordinate for now
        # assert len(variable.dims) == 1
        self.is_info = info
        self.is_dimension = not info

        if variable.values.ndim == 0:
            self.values = [self.convert(variable.values)]
        else:
            self.values = [self.convert(t) for t in variable.values.flatten()]

    def make_slice(self, value):
        return self.slice_class(
            self.variable.name,
            value,
            self.values.index(value),
            self.is_dimension,
            self.is_info,
        )

    def __repr__(self):
        return "%s[name=%s,values=%s]" % (
            self.__class__.__name__,
            self.variable.name,
            len(self.values),
        )


class TimeCoordinate(Coordinate):
    slice_class = TimeSlice
    is_dimension = True
    convert = as_datetime


class LevelCoordinate(Coordinate):
    # This class is just in case we want to specialise
    # 'level', othewise, it is the same as OtherCoordinate
    slice_class = Slice
    is_dimension = False
    convert = as_level


class OtherCoordinate(Coordinate):
    slice_class = Slice
    is_dimension = False
    convert = as_level


class DataSet:
    def __init__(self, ds):
        self._ds = ds
        self._bbox = {}
        self._cache = {}

    @property
    def data_vars(self):
        return self._ds.data_vars

    def __getitem__(self, key):
        if key not in self._cache:
            self._cache[key] = self._ds[key]
        return self._cache[key]

    def bbox(self, variable):
        data_array = self[variable]
        dims = data_array.dims

        lat = dims[-2]
        lon = dims[-1]

        if (lat, lon) not in self._bbox:
            dims = data_array.dims

            latitude = data_array[lat]
            longitude = data_array[lon]

            self._bbox[(lat, lon)] = (
                np.amax(latitude.data),
                np.amin(longitude.data),
                np.amin(latitude.data),
                np.amax(longitude.data),
            )

        return self._bbox[(lat, lon)]


class NetCDFField(Base):
    def __init__(self, path, ds, variable, slices, non_dim_coords):
        data_array = ds[variable]

        self._ds = ds
        self._da = data_array

        self.north, self.west, self.south, self.east = ds.bbox(variable)

        self.path = path
        self.variable = variable
        self.slices = slices
        self.non_dim_coords = non_dim_coords

        self.name = self.variable

        self.title = getattr(
            data_array,
            "long_name",
            getattr(data_array, "standard_name", self.variable),
        )

        self.time = non_dim_coords.get("valid_time", non_dim_coords.get("time"))

        # print('====', non_dim_coords)

        for s in self.slices:
            if isinstance(s, TimeSlice):
                self.time = s.value

            if s.is_info:
                self.title += " (" + s.name + "=" + str(s.value) + ")"

    def __repr__(self):
        return "NetCDFField[%r,%r]" % (self.variable, self.slices)

    def bounding_box(self):
        return BoundingBox(
            north=self.north, south=self.south, east=self.east, west=self.west
        )

    def to_xarray(self):
        return self._da

    def to_pandas(self):
        return self._da.to_pandas()

    def to_numpy(self, flatten=True):
        arr = self.to_xarray().to_numpy()
        if flatten:
            arr = arr.flatten()
        return arr

    def to_proj(self):
        if "proj4_string" in self._da.attrs:
            proj_source = self._da.attrs["proj4_string"]
        elif "grid_mapping" in self._da.attrs:
            proj_source = self._ds[self._da.attrs["grid_mapping"]].attrs["proj4_params"]
        else:
            raise AttributeError(
                "No CF-compliant proj information detected in netCDF attributes"
            )

        # Simply assume a WGS 84 target projection for CF-compliant netCDF
        proj_target = "+proj=eqc +datum=WGS84 +units=m +no_defs"

        return proj_source, proj_target

    def _grid_mapping(self):
        if "grid_mapping" in self._da.attrs:
            grid_mapping = self._ds[self._da.attrs["grid_mapping"]]
        else:
            raise AttributeError(
                "no CF-compliant 'grid_mapping' detected in netCDF attributes"
            )
        return grid_mapping

    def projection(self):
        return Projection.from_cf_grid_mapping(**self._grid_mapping().attrs)

    def to_points(self, flatten=False):
        points = dict()
        for axis in ("x", "y"):
            for coord in self._da.coords:
                if self._da.coords[coord].attrs.get("axis", "").lower() == axis:
                    break
            else:
                candidates = GEOGRAPHIC_COORDS.get(axis, [])
                for coord in candidates:
                    if coord in self._da.coords:
                        break
                else:
                    raise ValueError(f"No coordinate found with axis '{axis}'")
            points[axis] = self._da.coords[coord]
        points["x"], points["y"] = np.meshgrid(points["x"], points["y"])
        if flatten:
            points["x"], points["y"] = points["x"].flatten(), points["y"].flatten()
        return points


class NetCDFReader(Reader):
    def __init__(self, source, path):
        super().__init__(source, path)
        self.fields = None

    def _scan(self):
        if self.fields is None:
            self.fields = self.get_fields()

    def __repr__(self):
        return "NetCDFReader(%s)" % (self.path,)

    def __iter__(self):
        self._scan()
        return iter(self.fields)

    def __len__(self):
        self._scan()
        return len(self.fields)

    def __getitem__(self, n):
        self._scan()
        return self.fields[n]

    def get_fields(self):
        with closing(
            xr.open_mfdataset(self.path, combine="by_coords")
        ) as ds:  # or nested
            return self._get_fields(DataSet(ds))

    def _get_fields(self, ds):  # noqa C901
        # Select only geographical variables
        has_lat = False
        has_lon = False

        fields = []

        skip = set()

        for name in ds.data_vars:
            v = ds[name]
            skip.update(getattr(v, "coordinates", "").split(" "))
            skip.update(getattr(v, "bounds", "").split(" "))
            skip.update(getattr(v, "grid_mapping", "").split(" "))

        for name in ds.data_vars:
            if name in skip:
                continue

            v = ds[name]

            coordinates = []

            # self.log.info('Scanning file: %s var=%s coords=%s', self.path, name, v.coords)

            info = [value for value in v.coords if value not in v.dims]
            non_dim_coords = {}
            for coord in v.coords:
                if coord not in v.dims:
                    non_dim_coords[coord] = ds[coord].values
                    continue

                c = ds[coord]

                # self.log.info("COORD %s %s %s %s", coord, type(coord), hasattr(c, 'calendar'), c)

                standard_name = getattr(c, "standard_name", "")
                axis = getattr(c, "axis", "")
                long_name = getattr(c, "long_name", "")

                use = False

                if (
                    standard_name.lower() in GEOGRAPHIC_COORDS["x"]
                    or (long_name == "longitude")
                    or (axis == "X")
                ):
                    has_lon = True
                    use = True

                if (
                    standard_name.lower() in GEOGRAPHIC_COORDS["y"]
                    or (long_name == "latitude")
                    or (axis == "Y")
                ):
                    has_lat = True
                    use = True

                # Of course, not every one sets the standard_name
                if standard_name in ("time", "forecast_reference_time") or axis == "T":
                    coordinates.append(TimeCoordinate(c, coord in info))
                    use = True

                # TODO: Support other level types
                if standard_name in (
                    "air_pressure",
                    "model_level_number",
                    "altitude",
                ):  # or axis == 'Z':
                    coordinates.append(LevelCoordinate(c, coord in info))
                    use = True

                if axis in ("X", "Y"):
                    use = True

                if not use:
                    coordinates.append(OtherCoordinate(c, coord in info))

            if not (has_lat and has_lon):
                # self.log.info("NetCDFReader: skip %s (Not a 2 field)", name)
                continue

            for values in product(*[c.values for c in coordinates]):
                slices = []
                for value, coordinate in zip(values, coordinates):
                    slices.append(coordinate.make_slice(value))

                fields.append(NetCDFField(self.path, ds, name, slices, non_dim_coords))

        if not fields:
            raise Exception("NetCDFReader no 2D fields found in %s" % (self.path,))

        return fields

    def to_numpy(self, flatten=False):
        arr = self.to_xarray().to_array().to_numpy()
        if flatten:
            arr = arr.flatten()
        return arr

    def to_pandas(self):
        return self.to_xarray().to_pandas()

    def to_xarray(self, **kwargs):
        return type(self).to_xarray_multi_from_paths([self.path], **kwargs)

    @classmethod
    def to_xarray_multi_from_paths(cls, paths, **kwargs):
        import xarray as xr

        options = dict()
        options.update(kwargs.get("xarray_open_mfdataset_kwargs", {}))

        return xr.open_mfdataset(
            paths,
            **options,
        )

    def datetime(self):
        r = sorted({to_datetime(s.time) for s in self.get_fields()})
        return {"base_time": r, "valid_time": r}

    def bounding_box(self):
        return [s.bounding_box() for s in self.get_fields()]


def _match_magic(magic, deeper_check):
    if magic is not None:
        type_id = (b"\x89HDF", b"CDF\x01", b"CDF\x02")
        return len(magic) >= 4 and magic[:4] in type_id
    return False


def reader(source, path, magic=None, deeper_check=False):
    if _match_magic(magic, deeper_check):
        return NetCDFReader(source, path)
