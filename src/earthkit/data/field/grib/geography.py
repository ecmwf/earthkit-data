# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.field.spec.geography import Geography

from .collector import GribContextCollector
from .spec import GribSpec


def missing_is_none(x):
    return None if x == 2147483647 else x


class GribGeographySpec(Geography):
    def __init__(self, handle):
        self.handle = handle

    @property
    def latitudes(self):
        return self.handle.get_latitudes().reshape(self.shape)

    @property
    def longitudes(self):
        return self.handle.get_longitudes().reshape(self.shape)

    @property
    def distinct_latitudes(self):
        return self.handle.get("distinctLatitudes", default=None)

    @property
    def distinct_longitudes(self):
        return self.handle.get("distinctLongitudes", default=None)

    @property
    def x(self):
        grid_type = self.handle.get("gridType", default=None)
        if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
            return self.longitudes
        raise ValueError("x(): geographical coordinates in original CRS are not available")

    @property
    def y(self):
        grid_type = self.handle.get("gridType", default=None)
        if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
            return self.latitudes
        raise ValueError("y(): geographical coordinates in original CRS are not available")

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
        Nj = missing_is_none(self.handle.get("Nj", default=None))
        Ni = missing_is_none(self.handle.get("Ni", default=None))
        if Ni is None or Nj is None:
            n = self.handle.get("numberOfDataPoints", None)
            return (n,)  # shape must be a tuple
        return (Nj, Ni)

    @property
    def bounding_box(self):
        r"""Return the bounding box of the field.

        Returns
        -------
        :obj:`BoundingBox <data.utils.bbox.BoundingBox>`
        """
        from earthkit.data.utils.bbox import BoundingBox

        return BoundingBox(
            north=self.handle.get("latitudeOfFirstGridPointInDegrees", default=None),
            south=self.handle.get("latitudeOfLastGridPointInDegrees", default=None),
            west=self.handle.get("longitudeOfFirstGridPointInDegrees", default=None),
            east=self.handle.get("longitudeOfLastGridPointInDegrees", default=None),
        )

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

    @property
    def unique_grid_id(self):
        r"""Return a unique id of the grid of a field."""
        return self.handle.get("md5GridSection", default=None)

    @property
    def grid_spec(self):
        from .grid_spec import make_gridspec
        from .labels import GribLabels

        return make_gridspec(GribLabels(self.handle))

    @property
    def grid_type(self):
        r"""Return the grid type."""
        return self.handle.get("gridType", default=None)

    def to_dict(self):
        return dict()

    def __getstate__(self):
        state = {}
        state["handle"] = self.handle
        return state

    def __setstate__(self, state):
        self.__init__(state["handle"])


class GribGeographyBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.geography import GeographyFieldMember

        return GeographyFieldMember(GribGeographySpec(handle))


class GribGeographyContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(spec, context):
        pass


COLLECTOR = GribGeographyContextCollector()


class GribGeography(GribSpec):
    BUILDER = GribGeographyBuilder
    COLLECTOR = COLLECTOR
