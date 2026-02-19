# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import abstractmethod
from math import prod

import numpy as np

from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.utils.projections import Projection

from .component import SimpleFieldComponent
from .component import component_keys
from .component import mark_get_key


def uniform_resolution(vals):
    if len(vals) > 1:
        delta = np.diff(vals)
        if np.allclose(delta, delta[0]):
            return delta[0]
    return None


def create_geography_from_array(
    latitudes=None,
    longitudes=None,
    distinct_latitudes=None,
    distinct_longitudes=None,
    proj_str=None,
    shape_hint=None,
):
    lat = latitudes
    lon = longitudes

    expected_size = prod(shape_hint) if shape_hint else None

    distinct = False
    if lat is None or lon is None:
        lat = distinct_latitudes
        lon = distinct_longitudes

        # it is possible to have no geography at all.
        if lat is None and lon is None:
            return EmptyGeography(shape_hint)

        if shape_hint is None:
            if lat is None:
                raise ValueError("No latitudes or distinctLatitudes found")
            if lon is None:
                raise ValueError("No longitudes or distinctLongitudes found")

            lat = np.asarray(lat, dtype=np.float64)
            lon = np.asarray(lon, dtype=np.float64)

            if len(lat.shape) != 1:
                raise ValueError(f"distinct latitudes must be 1D array! shape={lat.shape} unsupported")
            if len(lon.shape) != 1:
                raise ValueError(f"distinctLongitudes must be 1D array! shape={lon.shape} unsupported")
            distinct = True
        else:
            if lat is not None and lon is not None:
                lat = np.asarray(lat, dtype=np.float64)
                lon = np.asarray(lon, dtype=np.float64)

                if len(lat.shape) != 1:
                    raise ValueError(f"distinct latitudes must be 1D array! shape={lat.shape} unsupported")
                if len(lon.shape) != 1:
                    raise ValueError(f"distinctLongitudes must be 1D array! shape={lon.shape} unsupported")
                if lat.size * lon.size != expected_size:
                    raise ValueError(
                        (
                            "Distinct latitudes and longitudes do not match number of values. "
                            f"Expected number=({lat.size * lon.size}), got={expected_size}"
                        )
                    )
                distinct = True

            else:
                lat = None
                lon = None
    else:
        lat = np.asarray(lat, dtype=np.float64)
        lon = np.asarray(lon, dtype=np.float64)
        if expected_size is not None:
            if lat.size * lon.size == expected_size:
                if len(lat.shape) != 1:
                    raise ValueError(
                        f"latitudes must be a 1D array when holding distinct values! shape={lat.shape} unsupported"
                    )
                if len(lon.shape) != 1:
                    raise ValueError(
                        f"longitudes must be a 1D array when holding distinct values! shape={lon.shape} unsupported"
                    )
                distinct = True

    assert lat is not None and lon is not None

    if distinct:
        # dx = uniform_resolution(lon)
        # dy = uniform_resolution(lat)
        return MeshedLatLonGeography(lat, lon, proj_str=proj_str)
        # if dx is not None and dy is not None:
        #     # metadata["DxInDegrees"] = dx
        #     # metadata["DyInDegrees"] = dy
        #     return RegularDistinctLLGeography(lat, lon, proj_str)
        # else:
        #     return DistinctLLGeography(lat, lon, proj_str=proj_str)
    else:
        if lat.shape != lon.shape:
            raise ValueError(f"latitudes and longitudes must have the same shape. {lat.shape} != {lon.shape}")

        if shape_hint is not None:
            if lat.size == expected_size:
                if lat.shape != shape_hint:
                    shape = lat.shape if lat.ndim > len(shape_hint) else shape_hint
                else:
                    shape = lat.shape

                return LatLonGeography(lat, lon, proj_str=proj_str, shape=shape)

            else:
                raise ValueError(
                    (
                        "Number of points do not match expected size. "
                        f"Expected=({expected_size}), got={lat.size}"
                    )
                )
        else:
            shape = lat.shape
            return LatLonGeography(lat, lon, proj_str=proj_str, shape=shape)


def create_geography_from_dict(d, shape_hint=None):
    return create_geography_from_array(
        latitudes=d.get("latitudes", None),
        longitudes=d.get("longitudes", None),
        distinct_latitudes=d.get("distinct_latitudes", None),
        distinct_longitudes=d.get("distinct_longitudes", None),
        proj_str=d.get("projTargetString", None),
        shape_hint=shape_hint,
    )


def _array_convert(v, flatten=False, dtype=None):
    if flatten:
        from earthkit.data.utils.array import flatten

        v = flatten(v)

    if dtype is not None:
        from earthkit.utils.array import array_namespace
        from earthkit.utils.array.convert import convert_dtype

        target_xp = array_namespace(v)
        target_dtype = convert_dtype(dtype, target_xp)
        if target_dtype is not None:
            v = target_xp.astype(v, target_dtype, copy=False)

    return v


@component_keys
class BaseGeography(SimpleFieldComponent):
    @mark_get_key
    @abstractmethod
    def latitudes(self, dtype=None):
        r"""Return the latitudes.

        Parameters
        ----------
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.

        Returns
        -------
        array-like, None
            The latitudes or None if not available.
        """
        pass

    @mark_get_key
    @abstractmethod
    def longitudes(self, dtype=None):
        r"""Return the longitudes.

        Parameters
        ----------
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.

        Returns
        -------
        array-like, None
            The longitudes or None if not available.
        """
        pass

    @mark_get_key
    @abstractmethod
    def distinct_latitudes(self, dtype=None):
        r"""Return the distinct latitudes.

        Parameters
        ----------
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.

        Returns
        -------
        array-like, None
            The distinct latitudes or None if not available.
        """
        pass

    @mark_get_key
    @abstractmethod
    def distinct_longitudes(self, dtype=None):
        r"""Return the distinct longitudes.

        Parameters
        ----------
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.

        Returns
        -------
        array-like, None
            The distinct longitudes or None if not available.
        """
        pass

    @mark_get_key
    @abstractmethod
    def x(self, dtype=None):
        r"""Return the x coordinates in the original CRS.

        Parameters
        ----------
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.

        Returns
        -------
        array-like, None
            The x coordinates or None if not available.
        """
        pass

    @mark_get_key
    @abstractmethod
    def y(self, dtype=None):
        r"""Return the y coordinates in the original CRS.

        Parameters
        ----------
        dtype: str, array.dtype or None
            Typecode or data-type of the array. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is ``float64``.

        Returns
        -------
        array-like, None
            The y coordinates or None if not available.
        """
        pass

    @mark_get_key
    @abstractmethod
    def shape(self) -> tuple:
        r"""Return the shape of the geography.

        Returns
        -------
        tuple
            The shape of the geography.
        """
        pass

    @mark_get_key
    @abstractmethod
    def projection(self):
        """Return the projection."""
        pass

    @mark_get_key
    @abstractmethod
    def bounding_box(self):
        """:obj:`BoundingBox <data.utils.bbox.BoundingBox>`: Return the bounding box."""
        pass

    @mark_get_key
    @abstractmethod
    def area(self) -> tuple:
        r"""Return the area as a tuple of (north, west, south, east).

        Returns
        -------
        tuple
            The area as a tuple of (north, west, south, east).
        """
        pass

    @mark_get_key
    @abstractmethod
    def grid(self):
        """Return the `eckit.geo.Grid` object representing the grid geometry.

        Returns
        -------
        eckit.geo.Grid, None
            The grid object or None if not available.
        """
        pass

    @mark_get_key
    @abstractmethod
    def unique_grid_id(self) -> str:
        r"""Return the unique id of the grid.

        Returns
        -------
        str, None
            The unique id of the grid or None if not available.
        """
        pass

    @mark_get_key
    @abstractmethod
    def grid_spec(self) -> dict:
        r"""Return the grid spec.

        Returns
        -------
        dict, None
            The grid spec or None if not available.
        """
        pass

    @mark_get_key
    @abstractmethod
    def grid_type(self) -> str:
        r"""Return the grid type.

        Returns
        -------
        str, None
            The grid type or None if not available.
        """
        pass

    def to_dict(self):
        return {"grid_spec": self.grid_spec()}

    # @classmethod
    # def from_dict(cls, data, shape_hint=None):
    #     from ..dict.geography import create_geography

    #     spec = create_geography(data, shape_hint=shape_hint)
    #     return spec

    def set(self, *args, shape_hint=None, **kwargs):
        kwargs = self.normalise_set_kwargs(*args, **kwargs)
        keys = set(kwargs.keys())

        if keys == {"grid_spec"}:
            spec = self.from_grid_spec(self, kwargs["grid_spec"])
            return spec
        if keys == {"latitudes", "longitudes"}:
            spec = self.from_dict(kwargs, shape_hint=shape_hint)
            return spec

        raise ValueError(f"Invalid {keys=} for Geography specification")

    def latlons(self, flatten=False, dtype=None):
        r"""Return the latitudes/longitudes of all the gridpoints in the field.

        Parameters
        ----------
        flatten: bool
            When it is True 1D arrays are returned. Otherwise arrays with the field's
            :obj:`shape` are returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``float64``.


        Returns
        -------
        array-like, array-like
            Tuple of latitudes and longitudes.

        See Also
        --------
        to_points

        """
        lat = self.latitudes()
        lon = self.longitudes()
        lat = _array_convert(lat, flatten=flatten, dtype=dtype)
        lon = _array_convert(lon, flatten=flatten, dtype=dtype)

        return lat, lon

    def xys(self, flatten=False, dtype=None):
        r"""Return the x/y coordinates of all the points.

        Parameters
        ----------
        flatten: bool
            When it is True 1D arrays are returned. Otherwise arrays with the field's
            :obj:`shape` are returned.
        dtype: str, array.dtype or None
            Typecode or data-type of the arrays. When it is :obj:`None` the default
            type used by the underlying data accessor is used. For GRIB it is
            ``float64``.

        Returns
        -------
        array-like, array-like
            Tuple of x and y coordinates.

        See Also
        --------
        to_points

        """
        x = self.x(dtype=dtype)
        y = self.y(dtype=dtype)

        if x is not None and y is not None:
            x = _array_convert(x, flatten=flatten, dtype=dtype)
            y = _array_convert(y, flatten=flatten, dtype=dtype)
            return x, y

        try:
            if self.projection().CARTOPY_CRS == "PlateCarree":
                return self.latlons(flatten=flatten, dtype=dtype)
        except Exception:
            pass

        raise ValueError("xys(): geographical coordinates in original CRS are not available")

    def points(self, flatten=False, dtype=None):
        return self.xys(flatten=flatten, dtype=dtype)

    def __getstate__(self):
        return super().__getstate__()

    def __setstate__(self, state):
        super().__setstate__(state)


class EmptyGeography(BaseGeography):
    def __init__(self, shape=None):
        self._shape = shape

    def latitudes(self, dtype=None):
        return None

    def longitudes(self, dtype=None):
        return None

    def distinct_latitudes(self, dtype=None):
        return None

    def distinct_longitudes(self, dtype=None):
        return None

    def x(self, dtype=None):
        raise NotImplementedError("x is not implemented for this geography")

    def y(self, dtype=None):
        raise NotImplementedError("y is not implemented for this geography")

    def shape(self):
        return self._shape

    def unique_grid_id(self):
        return self.shape()

    def projection(self):
        return None

    def bounding_box(self):
        return None

    def grid(self):
        return None

    def grid_spec(self):
        return None

    def area(self) -> tuple:
        return None

    def grid_type(self) -> str | None:
        return None

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")
        shape = d.get("shape", None)
        if "shape" in d and len(d) > 1:
            raise ValueError("EmptyGeography can only be created from a dictionary with a single key 'shape'")
        return cls(shape=shape)

    def __getstate__(self):
        return {"shape": self._shape}

    def __setstate__(self, state):
        self._shape = state["shape"]


class SpectralGeography(EmptyGeography):
    pass


class LatLonGeography(BaseGeography):
    def __init__(self, latitudes, longitudes, proj_str=None, shape=None):
        self._lat = latitudes
        self._lon = longitudes
        self._proj_str = proj_str
        self._shape = shape

    def latitudes(self, dtype=None):
        return np.asarray(self._lat, dtype=dtype).reshape(self._shape)

    def longitudes(self, dtype=None):
        return np.asarray(self._lon, dtype=dtype).reshape(self._shape)

    def distinct_latitudes(self, dtype=None):
        return None

    def distinct_longitudes(self, dtype=None):
        return None

    def x(self, dtype=None):
        raise NotImplementedError("x is not implemented for this geography")

    def y(self, dtype=None):
        raise NotImplementedError("y is not implemented for this geography")

    def shape(self):
        if self._shape is not None:
            return self._shape
        return self.latitudes.shape

    def unique_grid_id(self) -> str:
        return str(self.shape())

    def grid(self):
        return None

    def _north(self):
        return np.amax(self.latitudes())

    def _south(self):
        return np.amin(self.latitudes())

    def west(self):
        return np.amin(self.longitudes())

    def _east(self):
        return np.amax(self.longitudes())

    def projection(self):
        if self._proj_str:
            return Projection.from_proj_string(self._proj_str)
        return None
        # return Projection.from_proj_string(self.metadata.get("projTargetString", None))

    def bounding_box(self):
        return BoundingBox(
            north=self._north(),
            south=self._south(),
            west=self._west(),
            east=self._east(),
        )

    def grid_spec(self):
        return None

    def area(self) -> tuple:
        return (self.north(), self.west(), self.south(), self.east())

    def grid_type(self):
        return "_unstructured"

    @classmethod
    def from_dict(cls, data, shape_hint=None):
        return create_geography_from_dict(data, shape_hint=shape_hint)


class MeshedLatLonGeography(LatLonGeography):
    def __init__(self, latitudes, longitudes, proj_str=None):
        super().__init__(None, None, proj_str=proj_str)
        self._distinct_lat = latitudes
        self._distinct_lon = longitudes

    def latitudes(self, dtype=None):
        lat = self.distinct_latitudes(dtype=dtype)
        n_lon = len(self.distinct_longitudes())
        v = np.repeat(lat[:, np.newaxis], n_lon, axis=1)
        return v

    def longitudes(self, dtype=None):
        lon = self.distinct_longitudes(dtype=dtype)
        n_lat = len(self.distinct_latitudes())
        v = np.repeat(lon[np.newaxis, :], n_lat, axis=0)
        return v

    def distinct_latitudes(self, dtype=None):
        return np.asarray(self._distinct_lat, dtype=dtype)

    def distinct_longitudes(self, dtype=None):
        return np.asarray(self._distinct_lon, dtype=dtype)

    def shape(self):
        Nj = len(self.distinct_latitudes())
        Ni = len(self.distinct_longitudes())
        return (Nj, Ni)

    def grid_type(self):
        return "_distinct_ll"


# class RegularDistinctLLGeography(DistinctLLGeography):
#     def __init__(self, latitudes, longitudes, proj_str=None, dx=None, dy=None):
#         super().__init__(latitudes, longitudes, proj_str=proj_str)
#         self._dx = dx
#         self._dy = dy

#     def dx(self, dtype=None):
#         x = self._dx
#         if x is None:
#             lon = self.distinct_longitudes(dtype=dtype)
#             x = lon[1] - lon[0]
#         x = abs(round(x * 1_000_000) / 1_000_000)
#         return x

#     def dy(self, dtype=None):
#         y = self._dy
#         if y is None:
#             lat = self.distinct_latitudes(dtype=dtype)
#             y = lat[0] - lat[1]
#         y = abs(round(y * 1_000_000) / 1_000_000)
#         return y

#     def grid_type(self):
#         return "_regular_ll"


class GridsSpecBasedGeography(BaseGeography):
    def __init__(self, grid_spec):
        from eckit.geo import Grid

        self._grid = Grid(grid_spec)
        self._grid_spec_in = grid_spec

    # @thread_safe_cached_property
    # def spectral(self):
    #     return False

    def latitudes(self, dtype=None):
        r"""Return the latitudes of the field.

        Returns
        -------
        ndarray
        """
        v, _ = self._grid.to_latlons()
        import numpy as np

        v = np.asarray(v)

        if dtype is None:
            dtype = np.float64
        v = _array_convert(v, dtype=dtype)

        return v

    def longitudes(self, dtype=None):
        r"""Return the longitudes of the field.

        Returns
        -------
        ndarray
        """
        _, v = self._grid.to_latlons()
        import numpy as np

        v = np.asarray(v)

        if dtype is None:
            dtype = np.float64
        v = _array_convert(v, dtype=dtype)

        return v

    def distinct_latitudes(self, dtype=None):
        return None

    def distinct_longitudes(self, dtype=None):
        return None

    def x(self, dtype=None):
        r"""Return the x coordinates in the field's original CRS.

        Returns
        -------
        ndarray
        """
        return NotImplementedError("x(): geographical coordinates in original CRS are not available")

    def y(self, dtype=None):
        r"""Return the y coordinates in the field's original CRS.

        Returns
        -------
        ndarray
        """
        raise NotImplementedError("y(): geographical coordinates in original CRS are not available")

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
        return self._grid.shape

    def unique_grid_id(self):
        return self._grid.uid

    def projection(self):
        raise NotImplementedError("projection is not implemented for this geography")

    def bounding_box(self):
        bb = self._grid.bounding_box()
        return BoundingBox(
            north=bb[0],
            south=bb[2],
            west=bb[1],
            east=bb[3],
        )

    def grid_spec(self):
        try:
            return self._grid.spec
        except Exception:
            if isinstance(self._grid_spec_in, str):
                import json

                return json.loads(self._grid_spec_in)
            return self._grid_spec_in

    def area(self) -> tuple:
        bb = self._grid.bounding_box()
        return bb

    def grid(self):
        return self._grid

    # @property
    # def rotation(self):
    #     raise NotImplementedError("rotation is not implemented for this geography")

    # @thread_safe_cached_property
    # def rotated(self):
    #     raise NotImplementedError("rotated is not implemented for this geography")

    # @thread_safe_cached_property
    # def rotated_iterator(self):
    #     raise NotImplementedError

    # def check_rotated_support(self):
    #     if self.rotated and self.metadata.get("gridType") == "reduced_rotated_gg":
    #         from earthkit.data.utils.message import ECC_FEATURES

    #         if not ECC_FEATURES.version >= (2, 35, 0):
    #             raise RuntimeError("gridType=rotated_reduced_gg requires ecCodes >= 2.35.0")

    # def latitudes_unrotated(self, **kwargs):
    #     raise NotImplementedError("latitudes_unrotated is not implemented for this geography")

    # def longitudes_unrotated(self, **kwargs):
    #     raise NotImplementedError
