# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
import logging

from earthkit.data.decorators import thread_safe_cached_property
from earthkit.data.field.component.component import normalise_set_kwargs
from earthkit.data.field.component.geography import BaseGeography
from earthkit.data.field.component.geography import create_geography_from_dict

from .collector import GribContextCollector
from .core import GribFieldComponentHandler

LOG = logging.getLogger(__name__)


def missing_is_none(x):
    return None if x == 2147483647 else x


class EckitGridSupport:
    """Support for eckit-based grid handling in ecCodes.

    This class checks for the availability of eckit and its grid support, as well as the
    ecCodes features related to eckit grid support. It is only evaluated once and cached
    for future use.
    """

    @thread_safe_cached_property
    def has_grid(self):
        try:
            from eckit.geo import Grid  # noqa: F401

            return True
        except ImportError:
            pass

        return False

    @thread_safe_cached_property
    def has_ecc_grid_spec(self):
        import os

        if os.environ.get("ECCODES_ECKIT_GEO") == "1":
            import eccodes

            try:
                r = eccodes.codes_get_features(eccodes.CODES_FEATURES_ENABLED)
                if isinstance(r, str) and "ECKIT_GEO" in r:
                    return True
            except Exception as e:
                LOG.warning(f"Failed to get ecCodes features: {e}")
                return False

        return False


_ECKIT_GRID_SUPPORT = EckitGridSupport()


class GribGeography(BaseGeography):
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
        :obj:`BoundingBox <data.utils.bbox.BoundingBox>`
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

    def unique_grid_id(self):
        r"""Return a unique id of the grid of a field."""
        return self.handle.get("md5GridSection", default=None)

    def grid(self):
        r"""Return the grid information as a dictionary."""
        return None

    def grid_spec(self):
        # Use the legacy earthkit-data grid_spec builder. If this class is used, it means that the eckit-based
        # grid_spec builder is not available, so we need to fallback to the legacy one.
        from .grid_spec import make_gridspec
        from .metadata import GribMetadata

        return make_gridspec(GribMetadata(self.handle))

    def area(self):
        north = self.handle.get("latitudeOfFirstGridPointInDegrees")
        south = self.handle.get("latitudeOfLastGridPointInDegrees")
        west = self.handle.get("longitudeOfFirstGridPointInDegrees")
        east = self.handle.get("longitudeOfLastGridPointInDegrees")
        return [north, west, south, east]

    def grid_type(self):
        r"""Return the grid type."""
        return self.handle.get("gridType", default=None)

    @classmethod
    def from_dict(*args, **kwargs):
        raise NotImplementedError("GribGeography cannot be created from a dictionary")

    def to_dict(self):
        return dict()

    # @classmethod
    # def from_grid_spec(cls, spec, grid_spec):
    #     from earthkit.data.readers.grib.gridspec import GridSpecConverter

    #     # edition = d.get("edition", self["edition"])
    #     edition = spec.handle.get("edition", 2)
    #     md, new_value_size = GridSpecConverter.to_metadata(grid_spec, edition=edition)

    #     print("FROM GRID SPEC MD:", md)
    #     print("FROM GRID SPEC new_value_size:", new_value_size)

    #     handle = spec.handle.clone(headers_only=False)
    #     handle.set_multiple(md)

    #     # we need to set the values to the new size otherwise the clone generated
    #     # with headers_only=True will be inconsistent
    #     if new_value_size is not None and new_value_size > 0:
    #         import numpy as np

    #         vals = np.zeros(new_value_size)
    #         handle.set_values(vals)

    #     return cls(handle)

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

        # Spectral data is handled differently right now
        if handle.get("gridType", None) == "sh":
            from earthkit.data.field.component.geography import SpectralGeography

            shape = (handle.get("numberOfDataPoints", None),)
            component = SpectralGeography(shape=shape)
        # Gridded data
        else:
            if _ECKIT_GRID_SUPPORT.has_ecc_grid_spec and _ECKIT_GRID_SUPPORT.has_grid:
                from earthkit.data.field.component.geography import GridsSpecBasedGeography

                # Try to get the gridspec from the handle
                grid_spec = handle.get("gridSpec", None)
                if grid_spec is not None and grid_spec != "":
                    component = GridsSpecBasedGeography(grid_spec)
                else:
                    # fallback to non-eckit based geo support in ecCodes
                    component = GribGeography(handle)
            else:
                component = GribGeography(handle)

        return GeographyFieldComponentHandler.from_component(component)


class GribGeographyContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(handler, context):
        pass


COLLECTOR = GribGeographyContextCollector()


class GribGeographyHandler(GribFieldComponentHandler):
    BUILDER = GribGeographyBuilder
    COLLECTOR = COLLECTOR

    def set(self, *args, shape_hint=None, **kwargs):
        kwargs = normalise_set_kwargs(self.component, *args, **kwargs)
        keys = set(kwargs.keys())

        if keys == {"grid_spec"}:
            handle = self._handle_from_grid_spec(self, kwargs["grid_spec"])
            return GribGeographyHandler(handle)
        else:
            return create_geography_from_dict(kwargs, shape_hint=shape_hint)

    def _handle_from_grid_spec(cls, handler, grid_spec):
        from earthkit.data.readers.grib.gridspec import GridSpecConverter
        from earthkit.data.readers.grib.handle import MemoryGribHandle

        # edition = d.get("edition", self["edition"])
        edition = handler.handle.get("edition", 2)
        md, new_value_size = GridSpecConverter.to_metadata(grid_spec, edition=edition)

        handle = handler.handle.clone(headers_only=False)
        handle.set_multiple(md)

        # we need to set the values to the new size otherwise the clone generated
        # with headers_only=True will be inconsistent
        if new_value_size is not None and new_value_size > 0:
            import numpy as np

            vals = np.zeros(new_value_size)
            handle.set_values(vals)

        return MemoryGribHandle(handle)
