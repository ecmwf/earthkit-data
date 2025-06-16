# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.utils.dates import datetime_from_grib
from earthkit.data.utils.dates import to_timedelta

from .data import SimpleData
from .geography import Geography
from .labels import Labels
from .parameter import Parameter
from .time import Time
from .vertical import Vertical


def missing_is_none(x):
    return None if x == 2147483647 else x


class GribData(SimpleData):
    def __init__(self, handle):
        self.handle = handle

    def get_values(self, dtype=None):
        """Get the values stored in the field as an array."""
        return self.handle.get_values(dtype=dtype)


class GribParameter(Parameter):
    def __init__(self, handle):
        self.handle = handle

    @property
    def name(self):
        return self.handle.get("shortName", None)

    @property
    def units(self):
        return self.handle.get("units", None)


class GribTime(Time):
    def __init__(self, handle):
        self.handle = handle

    @property
    def base_datetime(self):
        return self._datetime("dataDate", "dataTime")

    @property
    def valid_datetime(self):
        return self._datetime("validityDate", "validityTime")

    # def reference_datetime(self):
    #     return self._datetime("referenceDate", "referenceTime")

    # def indexing_datetime(self):
    #     return self._datetime("indexingDate", "indexingTime")

    @property
    def step(self):
        v = self._get("endStep", None)
        if v is None:
            v = self._get("step", None)
        return to_timedelta(v)

    @property
    def range(self):
        v = self._get("endStep", None)
        if v is None:
            v = self._get("step", None)
        return to_timedelta(v)

    def _get(self, key, default=None):
        """Get a value from the handle, returning default if not found."""
        return self.handle.get(key, default)

    def _datetime(self, date_key, time_key):
        date = self._get(date_key, None)
        if date is not None:
            time = self._get(time_key, None)
            if time is not None:
                return datetime_from_grib(date, time)
        return None


class GribGeography(Geography):
    def __init__(self, handle):
        self.handle = handle

    @property
    def latitudes(self):
        # Placeholder for actual implementation
        return self.handle.get_latitudes()

    @property
    def longitudes(self):
        # Placeholder for actual implementation
        return self.handle.get_longitudes()

    @property
    def shape(self):
        r"""Get the shape of the field.

        For structured grids the shape is a tuple in the form of (Nj, Ni) where:

        - ni: the number of gridpoints in i direction (longitude for a regular latitude-longitude grid)
        - nj: the number of gridpoints in j direction (latitude for a regular latitude-longitude grid)

        For other grid types the number of gridpoints is returned as ``(num,)``

        Returns
        -------
        tuple
        """
        Nj = missing_is_none(self.handle.get("Nj", None))
        Ni = missing_is_none(self.handle.get("Ni", None))
        if Ni is None or Nj is None:
            n = self.handle.get("numberOfDataPoints", None)
            return (n,)  # shape must be a tuple
        return (Nj, Ni)

    @property
    def projection(self):
        r"""Return information about the projection.

        Returns
        -------
        :obj:`Projection`

        Examples
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/examples/test.grib")
        >>> ds.projection()
        <Projected CRS: +proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to ...>
        Name: unknown
        Axis Info [cartesian]:
        - E[east]: Easting (unknown)
        - N[north]: Northing (unknown)
        - h[up]: Ellipsoidal height (metre)
        Area of Use:
        - undefined
        Coordinate Operation:
        - name: unknown
        - method: Equidistant Cylindrical
        Datum: Unknown based on WGS 84 ellipsoid
        - Ellipsoid: WGS 84
        - Prime Meridian: Greenwich
        >>> ds.projection().to_proj_string()
        '+proj=eqc +ellps=WGS84 +a=6378137.0 +lon_0=0.0 +to_meter=111319.4907932736 +no_defs +type=crs'
        """
        from earthkit.data.utils.projections import Projection

        return Projection.from_proj_string(self.handle.get("projTargetString", None))


class GribVertical(Vertical):
    def __init__(self, handle):
        self.handle = handle

    @property
    def level(self):
        return self.handle.get("level", None)

    @property
    def level_type(self):
        return self.handle.get("levelType", None)


class GribLabels(Labels):
    def __init__(self, handle):
        self.handle = handle

    def metadata(self, keys=None, default=None):
        return self.handle.get_labels_metadata(keys=keys, default=default)
