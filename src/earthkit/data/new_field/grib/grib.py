# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from ..data import FieldData

# from ..geography import Geography
from ..labels import Labels
from ..labels import RawLabels

# from ..parameter import SimpleParameter
# from ..vertical import Vertical


def missing_is_none(x):
    return None if x == 2147483647 else x


class GribData(FieldData):
    def __init__(self, handle):
        self.handle = handle

    def get_values(self, dtype=None):
        """Get the values stored in the field as an array."""
        return self.handle.get_values(dtype=dtype)

    def to_dict(self, encoder=False):
        r = {}
        if encoder:
            r["handle"] = self.handle
        else:
            r["values"] = self.values

        return r


# from ..parameter import ParamSpec


# class GribParameter:
#     def __init__(self, handle):
#         self.handle = handle
#         self._spec = None
#         self._exception = None

#     @property
#     def spec(self):
#         if self._spec is None:
#             try:
#                 self._spec = ParamSpec.from_grib(self.handle)

#             except Exception as e:
#                 LOG.error(f"Failed to get parameter spec for {self.handle}: {e}")
#             self.handle = None
#         return self._spec

#     def __getattr__(self, name):
#         if self._exception is not None:
#             raise self._exception(name)
#         assert name != "spec"
#         return getattr(self.spec, name)


# # setattr(ParamSpec, "from_grib", classmethod(GribParameter._to_spec))


# class GribParameter(SimpleParameter):
#     def __init__(self, handle):
#         self.handle = handle

#     @cached_property
#     def spec(self):
#         from ..parameter import ParameterSpec

#         return ParameterSpec.from_grib(self.handle)

# @property
# def name(self):
#     v = self.handle.get("shortName", None)
#     if v == "~":
#         v = self.handle.get("paramId", ktype=str, default=None)
#     return v

# @property
# def units(self):
#     return self.handle.get("units", None)


# class GribParameter(SimpleParameter):
#     def __init__(self, handle):
#         self.handle = handle

#     @property
#     def name(self):
#         v = self.handle.get("shortName", None)
#         if v == "~":
#             v = self.handle.get("paramId", ktype=str, default=None)
#         return v

#     @property
#     def units(self):
#         return self.handle.get("units", None)

#     # def to_dict(self, encoder=False):
#     #     r = {}
#     #     if encoder:
#     #         r["handle"] = self.handle
#     #     else:
#     #         r["values"] = self.values


# class GribTime(Time):
#     def __init__(self, handle):
#         self.handle = handle

#     @property
#     def base_datetime(self):
#         return self._datetime("dataDate", "dataTime")

#     @property
#     def valid_datetime(self):
#         return self._datetime("validityDate", "validityTime")

#     # def reference_datetime(self):
#     #     return self._datetime("referenceDate", "referenceTime")

#     # def indexing_datetime(self):
#     #     return self._datetime("indexingDate", "indexingTime")

#     @property
#     def step(self):
#         v = self._get("endStep", None)
#         if v is None:
#             v = self._get("step", None)
#         return to_timedelta(v)

#     @property
#     def range(self):
#         v = self._get("endStep", None)
#         if v is None:
#             v = self._get("step", None)
#         return to_timedelta(v)

#     def _get(self, key, default=None):
#         """Get a value from the handle, returning default if not found."""
#         return self.handle.get(key, default)

#     def _datetime(self, date_key, time_key):
#         date = self._get(date_key, None)
#         if date is not None:
#             time = self._get(time_key, None)
#             if time is not None:
#                 return datetime_from_grib(date, time)
#         return None


# class GribGeography(Geography):
#     def __init__(self, handle):
#         self.handle = handle

#     @property
#     def latitudes(self):
#         return self.handle.get_latitudes().reshape(self.shape)

#     @property
#     def longitudes(self):
#         return self.handle.get_longitudes().reshape(self.shape)

#     @property
#     def distinct_latitudes(self):
#         return self.handle.get("distinctLatitudes", default=None)

#     @property
#     def distinct_longitudes(self):
#         return self.handle.get("distinctLongitudes", default=None)

#     @property
#     def x(self):
#         grid_type = self.handle.get("gridType", default=None)
#         if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
#             return self.longitudes
#         raise ValueError("x(): geographical coordinates in original CRS are not available")

#     @property
#     def y(self):
#         grid_type = self.handle.get("gridType", default=None)
#         if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
#             return self.latitudes
#         raise ValueError("y(): geographical coordinates in original CRS are not available")

#     @property
#     def shape(self):
#         r"""Get the shape of the field.

#         For structured grids the shape is a tuple in the form of (Nj, Ni) where:

#         - ni: the number of gridpoints in i direction (longitude for a regular latitude-longitude grid)
#         - nj: the number of gridpoints in j direction (latitude for a regular latitude-longitude grid)

#         For other grid types the number of gridpoints is returned as ``(num,)``

#         Returns
#         -------
#         tuple
#         """
#         Nj = missing_is_none(self.handle.get("Nj", default=None))
#         Ni = missing_is_none(self.handle.get("Ni", default=None))
#         if Ni is None or Nj is None:
#             n = self.handle.get("numberOfDataPoints", None)
#             return (n,)  # shape must be a tuple
#         return (Nj, Ni)

#     @property
#     def bounding_box(self):
#         r"""Return the bounding box of the field.

#         Returns
#         -------
#         :obj:`BoundingBox <data.utils.bbox.BoundingBox>`
#         """
#         from earthkit.data.utils.bbox import BoundingBox

#         return BoundingBox(
#             north=self.handle.get("latitudeOfFirstGridPointInDegrees", default=None),
#             south=self.handle.get("latitudeOfLastGridPointInDegrees", default=None),
#             west=self.handle.get("longitudeOfFirstGridPointInDegrees", default=None),
#             east=self.handle.get("longitudeOfLastGridPointInDegrees", default=None),
#         )

#     @property
#     def projection(self):
#         r"""Return information about the projection.

#         Returns
#         -------
#         :obj:`Projection`

#         Examples
#         --------
#         >>> import earthkit.data
#         >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
#         >>> ds.projection()
#         <Projected CRS: +proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to ...>
#         Name: unknown
#         Axis Info [cartesian]:
#         - E[east]: Easting (unknown)
#         - N[north]: Northing (unknown)
#         - h[up]: Ellipsoidal height (metre)
#         Area of Use:
#         - undefined
#         Coordinate Operation:
#         - name: unknown
#         - method: Equidistant Cylindrical
#         Datum: Unknown based on WGS 84 ellipsoid
#         - Ellipsoid: WGS 84
#         - Prime Meridian: Greenwich
#         >>> ds.projection().to_proj_string()
#         '+proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to_meter=111319.4907932736 +no_defs +type=crs'
#         """
#         from earthkit.data.utils.projections import Projection

#         return Projection.from_proj_string(self.handle.get("projTargetString", None))

#     @property
#     def unique_grid_id(self):
#         r"""Return a unique id of the grid of a field."""
#         return self.handle.get("md5GridSection", default=None)


# class GribVertical(Vertical):
#     def __init__(self, handle):
#         self.handle = handle

#     @property
#     def level(self):
#         return self.handle.get("level", None)

#     @property
#     def level_type(self):
#         return self.handle.get("levelType", None)


GribLabels = RawLabels


class GribRawLabels(Labels):
    def __init__(self, handle):
        self.handle = handle

    def __len__(self):
        return sum(map(lambda i: 1, self.keys()))

    def __contains__(self, key):
        if key.startswith("grib."):
            key = key[5:]
        return self.handle.__contains__(key)

    def __iter__(self):
        return self.keys()

    def keys(self):
        return self.handle.keys()

    def items(self):
        return self.handle.items()

    def __getitem__(self, key):
        return self.get(key, raise_on_missing=True)

    # def __getitem__(self, key):
    #     if key in self.handle:
    #         return self.handle.get(key)
    #     raise KeyError(f"Label '{key}' not found in GribLabels")

    def metadata(self, keys=None, default=None):
        return self.handle.get(keys=keys, default=default)

    def override(self, *args, headers_only_clone=True, **kwargs):
        pass

    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        def _key_name(key):
            if key == "param":
                key = "shortName"
            elif key == "_param_id":
                key = "paramId"
            return key

        _kwargs = {}
        if not raise_on_missing:
            _kwargs["default"] = default

        # allow using the "grib." prefix.
        if key.startswith("grib."):
            key = key[5:]

        # key = _key_name(key)

        v = self.handle.get(key, ktype=astype, **_kwargs)

        # special case when  "shortName" is "~".
        if key == "shortName" and v == "~":
            v = self.handle.get("paramId", ktype=str, **_kwargs)
        return v

    def set(self, d):
        return

    def message(self):
        r"""Return a buffer containing the encoded message.

        Returns
        -------
        bytes
        """
        return self.handle.get_buffer()
