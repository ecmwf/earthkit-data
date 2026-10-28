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
from earthkit.data.field.component.geography import (
    EmptyGeography,
    GeographyBase,
    GridsSpecBasedGeography,
    _create_geography_from_dict,
)
from earthkit.data.utils.grid import ECKIT_GRID_SUPPORT

from .collector import GribEncoderCollector, GribIndexerFieldKeysCollector, MultiCollector
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

        north = self.handle.get("latitudeOfFirstGridPointInDegrees", default=None)
        south = self.handle.get("latitudeOfLastGridPointInDegrees", default=None)
        if south is not None and north is not None and south > north:
            # latitudes are in the wrong order, swap them
            north, south = south, north
        west = self.handle.get("longitudeOfFirstGridPointInDegrees", default=None)
        east = self.handle.get("longitudeOfLastGridPointInDegrees", default=None)

        return BoundingBox(
            north=north,
            south=south,
            west=west,
            east=east,
        )

    def projection(self):
        r"""Return information about the projection.

        Returns
        -------
        :obj:`Projection`

        Examplesa
        --------
        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "docs/tutorials/test.grib")
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
        gs = self.grid_spec()
        if gs is not None:
            from eckit.geo import Grid

            return Grid(gs)
        else:
            return None

    def grid_spec(self):
        if ECKIT_GRID_SUPPORT.has_ecc_grid_spec and ECKIT_GRID_SUPPORT.has_grid:
            gs = self._get_grid_spec_from_handle
            if gs is not None:
                return gs.copy()  # return a copy to avoid accidental modifications

        return None

    @thread_safe_cached_property
    def _get_grid_spec_from_handle(self):
        if ECKIT_GRID_SUPPORT.has_ecc_grid_spec and ECKIT_GRID_SUPPORT.has_grid:
            grid_type = self.handle.get("gridType", default=None)
            # For certain gridTypes the grid specification is not available and when we try to access it a
            # lot of errors are logged/printed from the supporting libraries (eccodes/eckit), so we skip
            # them here.
            # TODO: remove this check once the supporting libraries handle all grid types correctly
            if grid_type in ["lambert", "polar_stereographic", "mercator", "lambert_azimuthal_equal_area"]:
                return None

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

        return None

    def area(self):
        north = self.handle.get("latitudeOfFirstGridPointInDegrees")
        south = self.handle.get("latitudeOfLastGridPointInDegrees")
        if south is not None and north is not None and south > north:
            # latitudes are in the wrong order, swap them
            north, south = south, north
        west = self.handle.get("longitudeOfFirstGridPointInDegrees")
        east = self.handle.get("longitudeOfLastGridPointInDegrees")
        return tuple([north, west, south, east])

    def grid_type(self):
        r"""Return the grid type."""
        return self.handle.get("gridType", default=None)

    # @classmethod
    # def from_dict(*args, **kwargs):
    #     raise NotImplementedError("GribGeography cannot be created from a dictionary")

    # def to_dict(self):
    #     return dict()

    def __getstate__(self):
        state = {}
        state["handle"] = self.handle
        return state

    def __setstate__(self, state):
        self.__init__(state["handle"])


def _has_zero_grid_uid(handle):
    """Return True if the ``uuidOfHGrid`` of the message is available and all zeros."""
    try:
        uid = handle.get("uuidOfHGrid", default=None)
    except Exception:
        return False

    if isinstance(uid, bytes):
        uid = uid.hex()
    if isinstance(uid, str):
        uid = uid.strip()
        return uid != "" and set(uid) == {"0"}
    return False


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
            # An all-zero uuidOfHGrid means the grid is not registered anywhere. Asking ecCodes for the
            # gridSpec would make ecCodes/eckit print "GridUnknownError" to stderr, so we skip it.
            if _has_zero_grid_uid(handle):
                grid_spec = None
            else:
                try:
                    grid_spec = handle.get("gridSpec", default=None)
                except Exception:
                    grid_spec = None

            if isinstance(grid_spec, str) and grid_spec != "":
                from earthkit.data.field.component.geography import GridsSpecBasedGeography

                component = GridsSpecBasedGeography(grid_spec)
            else:
                grid_name = handle.get("gridName", default=None)
                # this is the case for user defined grids with a custom set of lats/lons
                if grid_name == "undefined":
                    from earthkit.data.field.component.geography import EmptyGeography

                    shape = (handle.get("numberOfDataPoints", None),)
                    component = EmptyGeography(shape=shape, grid_type=grid_type)
                # for a named grid the the grid spec should exist, otherwise we cannot handle it
                else:
                    raise ValueError(
                        (
                            "GribGeographyBuilder: cannot handle unstructured grid with gridName="
                            f"{grid_name}. No gridSpec available"
                        )
                    )

        # Other gridded data is handled with ecCodes
        else:
            component = GribGeography(handle)
        return GeographyFieldComponentHandler.from_component(component)


class GribGeographyEncoderCollector(GribEncoderCollector):
    @staticmethod
    def _collect(handler, context):
        component = handler.component

        if (grid_spec := component.grid_spec()) is not None:
            if isinstance(grid_spec, dict):
                import json

                grid_spec = json.dumps(grid_spec)

            r = {
                "gridSpec": grid_spec,
            }
            context.update(r)
        else:
            raise ValueError(
                ("GribGeographyEncoderCollector: cannot collect context for a geography without a valid grid_spec")
            )


class GribGeographyIndexerFieldKeysCollector(GribIndexerFieldKeysCollector):
    """Collect the geography keys stored in the index.

    The keys are:

    - ``geography.shape``: list of int, the shape of the field
    - ``geography.unique_grid_id``: the unique grid id of the field
    - ``geography.grid_spec``: JSON str, only when the grid has a grid spec

    These keys are enough to rebuild the geography with :func:`create_geography_from_index`.
    """

    @staticmethod
    def _collect(handler, context):
        component = handler.component
        r = {}

        shape = component.shape()
        if shape is not None and all(x is not None for x in shape):
            r["geography.shape"] = [int(x) for x in shape]

        uid = component.unique_grid_id()
        if isinstance(uid, (tuple, list)):
            uid = [x if isinstance(x, (int, float, str)) else str(x) for x in uid]
        elif uid is not None and not isinstance(uid, (int, float, str)):
            uid = str(uid)
        if uid is not None:
            r["geography.unique_grid_id"] = uid

        try:
            grid_spec = component.grid_spec()
        except Exception:
            LOG.debug("Could not get grid_spec for indexing", exc_info=True)
            grid_spec = None

        if grid_spec is not None:
            if not isinstance(grid_spec, str):
                grid_spec = json.dumps(grid_spec)
            r["geography.grid_spec"] = grid_spec

        context.update(r)


COLLECTOR = MultiCollector(encoder=GribGeographyEncoderCollector(), indexer=GribGeographyIndexerFieldKeysCollector())


class _LazyGribGeography(GeographyBase):
    """Geography of a GRIB field rebuilt from index keys and a lazy GRIB handle.

    :meth:`shape` and :meth:`unique_grid_id` are answered from the values stored in
    the index. Every other method builds the normal GRIB geography from the handle on
    first use (so the GRIB message is only read then) and delegates to it.

    Parameters
    ----------
    handle: GribHandle, None
        The (lazy) GRIB handle of the message. When it is None and a method needs it
        an :class:`EmptyGeography` with the stored shape is used instead.
    shape: tuple, None
        The stored shape. When it is None the shape is taken from the handle.
    unique_grid_id: str, tuple, None
        The stored unique grid id. When it is None it is taken from the handle.
    """

    def __init__(self, handle, shape=None, unique_grid_id=None):
        self._handle = handle
        self._shape = tuple(shape) if shape is not None else None
        self._uid = unique_grid_id

    @thread_safe_cached_property
    def _resolved(self):
        if self._handle is None:
            return EmptyGeography(shape=self._shape)
        return GribGeographyBuilder.build(self._handle).component

    def latitudes(self, dtype=None):
        return self._resolved.latitudes(dtype=dtype)

    def longitudes(self, dtype=None):
        return self._resolved.longitudes(dtype=dtype)

    def distinct_latitudes(self, dtype=None):
        return self._resolved.distinct_latitudes(dtype=dtype)

    def distinct_longitudes(self, dtype=None):
        return self._resolved.distinct_longitudes(dtype=dtype)

    def x(self, dtype=None):
        return self._resolved.x(dtype=dtype)

    def y(self, dtype=None):
        return self._resolved.y(dtype=dtype)

    def shape(self):
        if self._shape is not None:
            return self._shape
        return self._resolved.shape()

    def projection(self):
        return self._resolved.projection()

    def bounding_box(self):
        return self._resolved.bounding_box()

    def area(self):
        return self._resolved.area()

    def grid(self):
        return self._resolved.grid()

    def unique_grid_id(self):
        if self._uid is not None:
            return self._uid
        return self._resolved.unique_grid_id()

    def grid_spec(self):
        return self._resolved.grid_spec()

    def grid_type(self):
        return self._resolved.grid_type()

    def __getstate__(self):
        return {"handle": self._handle, "shape": self._shape, "unique_grid_id": self._uid}

    def __setstate__(self, state):
        self.__init__(state["handle"], shape=state["shape"], unique_grid_id=state["unique_grid_id"])


def create_geography_from_index(d, handle=None):
    """Create the geography of a field from the flat keys stored in the index.

    Parameters
    ----------
    d: dict
        The geography keys without the ``geography.`` prefix, as stored by the
        indexer: ``shape`` (list of int), ``unique_grid_id`` and ``grid_spec`` (JSON str).
        Missing keys can be absent or None.
    handle: GribHandle, None
        The lazy GRIB handle of the message. It is only used when the geography
        cannot be built from ``d``, and only when something other than
        :meth:`shape` and :meth:`unique_grid_id` is requested.

    Returns
    -------
    GeographyFieldComponentHandler, None
        - When ``d`` has a ``grid_spec`` (and eckit-geo grid support is available) the geography
          is built from it and ``handle`` is never used. ``shape()`` and ``unique_grid_id()``
          return the stored values.
        - Otherwise a lazy geography is created, which answers ``shape()`` and
          ``unique_grid_id()`` from the stored keys and builds the normal GRIB geography
          from ``handle`` on first use of any other method.
        - A lazy geography without stored shape when ``d`` has no usable value but a
          ``handle`` is given.
        - None, when ``d`` has no usable value and there is no ``handle``.
    """
    from earthkit.data.field.handler.geography import GeographyFieldComponentHandler

    grid_spec = d.get("grid_spec")
    shape = d.get("shape")
    uid = d.get("unique_grid_id")

    if grid_spec is None and shape is None and uid is None:
        if handle is None:
            return None
        # nothing is stored (the geography could not be indexed): build it from the handle on demand
        return GeographyFieldComponentHandler.from_component(_LazyGribGeography(handle))

    if shape is not None:
        shape = tuple(shape)
    if isinstance(uid, list):
        uid = tuple(uid)

    if grid_spec is not None and ECKIT_GRID_SUPPORT.has_grid:
        component = GridsSpecBasedGeography(grid_spec, shape=shape, unique_grid_id=uid)
    else:
        component = _LazyGribGeography(handle, shape=shape, unique_grid_id=uid)

    return GeographyFieldComponentHandler.from_component(component)


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
