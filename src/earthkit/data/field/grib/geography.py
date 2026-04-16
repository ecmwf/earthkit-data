# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import json
import logging

from earthkit.utils.decorators import thread_safe_cached_property

from earthkit.data.field.component.component import _normalise_set_kwargs
from earthkit.data.field.component.geography import GeographyBase, _create_geography_from_dict
from earthkit.data.utils.grid import ECKIT_GRID_SUPPORT

from .collector import GribContextCollector
from .core import GribFieldComponentHandler

LOG = logging.getLogger(__name__)


def missing_is_none(x):
    return None if x == 2147483647 else x


class GribGeography(GeographyBase):
    # If this class is used, it means that eckit-geo does not support the grid
    # so we need to fallback to the legacy grid handling in ecCodes
    def __init__(self, handle):
        self.handle = handle

    def latitudes(self, dtype=None):
        return self.handle.get_latitudes(dtype=dtype).reshape(self.shape())

    def longitudes(self, dtype=None):
        return self.handle.get_longitudes(dtype=dtype).reshape(self.shape())

    def distinct_latitudes(self, dtype=None):
        return self.handle.get("distinctLatitudes", default=None)

    def distinct_longitudes(self, dtype=None):
        return self.handle.get("distinctLongitudes", default=None)

    def x(self, dtype=None):
        grid_type = self.handle.get("gridType", default=None)
        if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
            return self.longitudes(dtype=dtype)
        raise ValueError("x(): geographical coordinates in original CRS are not available")

    def y(self, dtype=None):
        grid_type = self.handle.get("gridType", default=None)
        if grid_type in ["regular_ll", "reduced_gg", "regular_gg"]:
            return self.latitudes(dtype=dtype)
        raise ValueError("y(): geographical coordinates in original CRS are not available")

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

    def bounding_box(self):
        r"""Return the bounding box of the field.

        Returns
        -------
        :obj:`BoundingBox <earthkit.data.utils.bbox.BoundingBox>`
        """
        from earthkit.data.utils.bbox import BoundingBox

        return BoundingBox(
            north=self.handle.get("latitudeOfFirstGridPointInDegrees", default=None),
            south=self.handle.get("latitudeOfLastGridPointInDegrees", default=None),
            west=self.handle.get("longitudeOfFirstGridPointInDegrees", default=None),
            east=self.handle.get("longitudeOfLastGridPointInDegrees", default=None),
        )

    def projection(self):
        r"""Return information about the projection.

        Returns
        -------
        :obj:`Projection`

        Examplesa
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/how-tos/test.grib")
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

    def unique_grid_id(self):
        r"""Return a unique id of the grid of a field."""
        return self.handle.get("md5GridSection", default=None)

    def grid(self):
        r"""Return the Grid object.

        This feature is not yet implemented in earthkit-data, and this method currently returns None.
        """
        return None

    def grid_spec(self):
        if ECKIT_GRID_SUPPORT.has_ecc_grid_spec and ECKIT_GRID_SUPPORT.has_grid:
            return self._get_grid_spec_from_handle
        else:
            return None

    @thread_safe_cached_property
    def _get_grid_spec_from_handle(self):
        if ECKIT_GRID_SUPPORT.has_ecc_grid_spec and ECKIT_GRID_SUPPORT.has_grid:
            # Try to get the gridspec from the handle
            grid_spec = self.handle.get("gridSpec", default=None)
            if isinstance(grid_spec, str) and grid_spec != "":
                try:
                    grid_spec = json.loads(grid_spec)
                except Exception:
                    grid_spec = None

            if not isinstance(grid_spec, dict):
                grid_spec = None

        return grid_spec

    def area(self):
        north = self.handle.get("latitudeOfFirstGridPointInDegrees")
        south = self.handle.get("latitudeOfLastGridPointInDegrees")
        west = self.handle.get("longitudeOfFirstGridPointInDegrees")
        east = self.handle.get("longitudeOfLastGridPointInDegrees")
        return tuple([north, west, south, east])

    def grid_type(self):
        r"""Return the grid type."""
        return self.handle.get("gridType", default=None)

    @classmethod
    def from_dict(*args, **kwargs):
        raise NotImplementedError("GribGeography cannot be created from a dictionary")

    # def to_dict(self):
    #     return dict()

    def __getstate__(self):
        state = {}
        state["handle"] = self.handle
        return state

    def __setstate__(self, state):
        self.__init__(state["handle"])


class GribGeographyBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.handler.geography import GeographyFieldComponentHandler

        grid_type = handle.get("gridType", None)

        # Spectral data is handled differently right now
        if grid_type == "sh":
            from earthkit.data.field.component.geography import SpectralGeography

            shape = (handle.get("numberOfDataPoints", None),)
            component = SpectralGeography(shape=shape)
        # "unstructured" grids are handled differently.
        # Currently, ecCodes cannot generate lat-lon for these grids, so we need to
        # rely on the gridSpec to reconstruct the grid with the eckit-geo Grid object.
        # If the gridSpec is not available, we cannot handle these grids.
        elif grid_type == "unstructured_grid":
            if not ECKIT_GRID_SUPPORT.has_ecc_grid_spec or not ECKIT_GRID_SUPPORT.has_grid:
                raise ValueError(
                    (
                        "GribGeographyBuilder: cannot use unstructured grid because eckit-geo"
                        " grid support is not available in ecCodes"
                    )
                )
            from earthkit.data.field.component.geography import GridsSpecBasedGeography

            grid_spec = handle.get("gridSpec", default=None)
            if isinstance(grid_spec, str) and grid_spec != "":
                component = GridsSpecBasedGeography(grid_spec)
            else:
                raise ValueError(
                    (
                        "GribGeographyBuilder: cannot use unstructured grid because gridSpec"
                        "  is not available in the handle"
                    )
                )
        # Other gridded data is handled with ecCodes
        else:
            component = GribGeography(handle)
        return GeographyFieldComponentHandler.from_component(component)


class GribGeographyContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(handler, context):
        component = handler.component
        if component.grid() is not None and component.grid_spec():
            grid_spec = component.grid_spec()
            if isinstance(grid_spec, dict):
                import json

                grid_spec = json.dumps(grid_spec)

            r = {
                "gridSpec": grid_spec,
            }
            context.update(r)
        else:
            raise ValueError(
                ("GribGeographyContextCollector: cannot collect context for a geography without a valid grid_spec")
            )


COLLECTOR = GribGeographyContextCollector()


class GribGeographyHandler(GribFieldComponentHandler):
    BUILDER = GribGeographyBuilder
    COLLECTOR = COLLECTOR

    def set(self, *args, shape_hint=None, **kwargs):
        kwargs = _normalise_set_kwargs(self.component, *args, **kwargs)
        keys = set(kwargs.keys())

        if keys == {"grid_spec"}:
            if not ECKIT_GRID_SUPPORT.has_ecc_grid_spec or not ECKIT_GRID_SUPPORT.has_grid:
                raise ValueError(
                    (
                        "GribGeographyHandler: cannot set grid_spec because eckit-geo grid support is not"
                        " available in ecCodes"
                    )
                )

        return _create_geography_from_dict(kwargs, shape_hint=shape_hint)
