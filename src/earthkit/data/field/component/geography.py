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
from typing import Optional

import numpy as np

from earthkit.data.utils.array import adjust_array
from earthkit.data.utils.bbox import BoundingBox
from earthkit.data.utils.grid import ECKIT_GRID_SUPPORT
from earthkit.data.utils.projections import Projection

from .component import SimpleFieldComponent, component_keys, mark_get_key


def _create_geography_from_array(
    latitudes=None,
    longitudes=None,
    distinct_latitudes=None,
    distinct_longitudes=None,
    proj_str=None,
    shape_hint=None,
) -> "GeographyBase":
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
        return MeshedLatLonGeography(lat, lon, proj_str=proj_str)
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
                    (f"Number of points do not match expected size. Expected=({expected_size}), got={lat.size}")
                )
        else:
            shape = lat.shape
            return LatLonGeography(lat, lon, proj_str=proj_str, shape=shape)


def _create_geography_from_dict(d, shape_hint=None) -> "GeographyBase":
    if not isinstance(d, dict):
        raise TypeError("data must be a dictionary")

    if "grid_spec" in d:
        if len(d) > 1:
            raise ValueError("When 'grid_spec' is provided no other keys should be present to create a geography")

        if ECKIT_GRID_SUPPORT.has_grid:
            return GridsSpecBasedGeography(d["grid_spec"])
        else:
            raise ValueError("Cannot create geography from 'grid_spec' since eckit-geo grid support is not available")

    elif "grid" in d:
        if len(d) > 1:
            raise ValueError("When 'grid' is provided no other keys should be present to create a geography")

        if ECKIT_GRID_SUPPORT.has_grid:
            return GridsSpecBasedGeography(d["grid"])
        else:
            raise ValueError("Cannot create geography from 'grid' since eckit-geo grid support is not available")

    return _create_geography_from_array(
        latitudes=d.get("latitudes", None),
        longitudes=d.get("longitudes", None),
        distinct_latitudes=d.get("distinct_latitudes", None),
        distinct_longitudes=d.get("distinct_longitudes", None),
        proj_str=d.get("projTargetString", None),
        shape_hint=shape_hint,
    )


@component_keys
class GeographyBase(SimpleFieldComponent):
    """Geography component representing the geographical information of a field.

    This class defines the interface for geography components, which can represent
    different types of geographical information. Some of the methods may not be applicable to all geography
    types (e.g. :meth:`distinct_latitudes`), and may return None.

    The geographical information can be accessed by methods like :meth:`latitudes`,
    :meth:`longitudes`, and :meth:`shape`. Each of these methods has an associated key
    that can be used in the :meth:`get` method to retrieve the corresponding information. The list
    of supported keys are as follows:

    - "latitudes"
    - "longitudes"
    - "distinct_latitudes"
    - "distinct_longitudes"
    - "x"
    - "y"
    - "shape"
    - "projection"
    - "bounding_box"
    - "unique_grid_id"
    - "grid_spec"
    - "grid_type"
    - "grid"
    - "area"

    Depending on the type of geographical information available, some of these keys may not be supported
    and will return None in the subclasses. For example, the "distinct_latitudes" key is only supported
    for certain grid types, and will return None for other grid types.

    Typically, this object is used as a component of a field, and can be accessed via the :attr:`geography`
    attribute of a field. The keys above can also be accessed via the :meth:`get` method of the field,
    using the "geography." prefix.

    The following example demonstrates how to access the geographical information from a field using
    various methods and keys:

        >>> import earthkit.data as ekd
        >>> field = ekd.from_source("sample", "test.grib").to_fieldlist()[0]
        >>> field.geography.area()
        (70, -20, 35, 40)
        >>> field.geography.get("area")
        (70, -20, 35, 40)
        >>> field.get("geography.area")
        (70, -20, 35, 40)

    The geography component is immutable. The :meth:`set` method to create a new
    instance with updated values. For example, the following code creates a new geography
    component with an updated step:

        >>> new_geography = field.geography.set(grid_spec= [10,10])
        >>> new_geography.area()
        (90.0, 0, -90.0, 360.0)

    We can also call the Field's :meth:`set` method to create a new field with an updated time component.
    This is typically done by also passing a new data array to match the new geography. For example,
    the following code creates a new field with an updated geography component and data array:

        >>> values = np.random.rand(19, 36)  # new values matching the new geography shape
        >>> new_field = field.set({"geography.grid_spec": [10,10], "values": values})
        >>> new_field.geography.area()
        (90.0, 0, -90.0, 360.0)


    """

    @mark_get_key
    @abstractmethod
    def latitudes(self, dtype=None) -> Optional[np.ndarray]:
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
    def longitudes(self, dtype=None) -> Optional[np.ndarray]:
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
    def distinct_latitudes(self, dtype=None) -> Optional[np.ndarray]:
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
    def distinct_longitudes(self, dtype=None) -> Optional[np.ndarray]:
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
    def x(self, dtype=None) -> Optional[np.ndarray]:
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
    def y(self, dtype=None) -> Optional[np.ndarray]:
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
    def projection(self) -> Optional[Projection]:
        """Return the projection.

        Returns
        -------
        Projection, None
            The projection or None if not available.
        """
        pass

    @mark_get_key
    @abstractmethod
    def bounding_box(self) -> Optional[BoundingBox]:
        r"""Return the bounding box.

        Returns
        -------
        BoundingBox, None
            The bounding box or None if not available.
        """
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
    def grid(self) -> Optional[object]:
        """Return the `eckit.geo.Grid` object representing the grid geometry.

        This is an experimental method and may not be available for
        all geography types.

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

    def set(self, *args, shape_hint=None, **kwargs) -> "GeographyBase":
        """Return a new GeographyBase object with updated values.

        Parameters
        ----------
        *args: tuple
            Positional arguments to update the geography. Positional arguments containing time data.
            Only dictionaries are allowed.

        shape_hint: tuple, optional
            A hint for the shape of the geography. This is typically used when the geography
            is created from a dictionary that does not contain explicit shape information, and
            the shape needs to be inferred from the data array shape.

        **kwargs: dict
            Keyword arguments to update the geography. The allowed keys are:

        The allowed keys in the dictionaries and keyword arguments are:

         - "grid_spec", str or dict
         - "latitudes" and "longitudes", array-like

        The following cases are supported for updating:

        - the only key provided is "grid_spec", in which case the new geography
          is created from the provided grid specification. In this case nothing
          is taken from the existing geography, and no other keys should be
          provided to avoid ambiguity. The "grid_spec" can be str or dict.

        - the only keys provided are "latitudes" and "longitudes", in which case
          the new geography is created from the provided latitude and longitude arrays.
          In this case, the ``shape_hint`` is used to determine the shape of the new geography
          if the provided latitudes and longitudes are 1D arrays. If the latitudes and
          longitudes are already 2D arrays matching the ``shape_hint``, then the ``shape_hint``
          is ignored. No other keys should be provided to avoid ambiguity.

        Returns
        -------
        GeographyBase
            The new GeographyBase object with updated values.

        Raises
        ------
        ValueError
            If the provided keys do not match any of the supported update cases, or if there is
            ambiguity in the provided keys.


        Example
        -------
        >>> new_geography = field.geography.set(grid_spec= [10,10])
        >>> new_geography.area()
        (90.0, 0, -90.0, 360.0)

        >>> values = np.random.rand(19, 36)  # new values matching the new geography shape
        >>> new_field = field.set({"geography.grid_spec": [10,10], "values": values})
        >>> new_field.geography.area()
        (90.0, 0, -90.0, 360.0)
        """
        kwargs = self._normalise_set_kwargs(*args, **kwargs)
        keys = set(kwargs.keys())

        if keys == {"grid_spec"}:
            spec = self.from_grid_spec(self, kwargs["grid_spec"])
            return spec
        if keys == {"latitudes", "longitudes"}:
            spec = self.from_dict(kwargs, shape_hint=shape_hint)
            return spec

        raise ValueError(f"Invalid {keys=} for Geography specification")

    def latlons(self, flatten=False, dtype=None) -> tuple:
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
        lat = adjust_array(lat, flatten=flatten, dtype=dtype)
        lon = adjust_array(lon, flatten=flatten, dtype=dtype)

        return lat, lon

    def xys(self, flatten=False, dtype=None) -> tuple:
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
            x = adjust_array(x, flatten=flatten, dtype=dtype)
            y = adjust_array(y, flatten=flatten, dtype=dtype)
            return x, y

        try:
            if self.projection().CARTOPY_CRS == "PlateCarree":
                return self.latlons(flatten=flatten, dtype=dtype)
        except Exception:
            pass

        raise ValueError("xys(): geographical coordinates in original CRS are not available")

    def points(self, flatten=False, dtype=None) -> tuple:
        r"""Return the x/y coordinates of all the points.

        This is an alias for :meth:`xys` and is provided for convenience when the
        geographical coordinates are desired as points rather than separate x and y arrays.

        See Also
        --------
        xys
        """
        return self.xys(flatten=flatten, dtype=dtype)

    @classmethod
    def from_dict(cls, data, shape_hint=None) -> "GeographyBase":
        """Create a Geography object from a dictionary.

        Parameters
        ----------
        data : dict
            Dictionary containing geography data.
        shape_hint: tuple, optional
            A hint for the shape of the geography. This is typically used when the geography
            is created from a dictionary that does not contain explicit shape information, and
            the shape needs to be inferred from the data array shape.

        Returns
        -------
        Geography
            The created Geography instance.

        """
        return _create_geography_from_dict(data, shape_hint=shape_hint)

    def to_dict(self) -> dict:
        """Return a dictionary representation of the Geography."""
        r = dict()
        for k in ("grid_spec", "grid_type", "shape", "area"):
            try:
                r[k] = getattr(self, k)()
            except Exception:
                pass
        return r

    def __getstate__(self) -> dict:
        return super().__getstate__()

    def __setstate__(self, state) -> None:
        super().__setstate__(state)


class EmptyGeography(GeographyBase):
    def __init__(self, shape=None) -> None:
        self._shape = shape

    def latitudes(self, dtype=None) -> None:
        return None

    def longitudes(self, dtype=None) -> None:
        return None

    def distinct_latitudes(self, dtype=None) -> None:
        return None

    def distinct_longitudes(self, dtype=None) -> None:
        return None

    def x(self, dtype=None) -> None:
        raise NotImplementedError("x is not implemented for this geography")

    def y(self, dtype=None) -> None:
        raise NotImplementedError("y is not implemented for this geography")

    def shape(self) -> Optional[tuple]:
        return self._shape

    def unique_grid_id(self) -> Optional[tuple]:
        return self.shape()

    def projection(self) -> None:
        return None

    def bounding_box(self) -> None:
        return None

    def grid(self) -> None:
        return None

    def grid_spec(self) -> None:
        return None

    def area(self) -> tuple:
        return None

    def grid_type(self) -> str | None:
        return None

    @classmethod
    def from_dict(cls, d) -> "EmptyGeography":
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")
        shape = d.get("shape", None)
        if "shape" in d and len(d) > 1:
            raise ValueError("EmptyGeography can only be created from a dictionary with a single key 'shape'")
        return cls(shape=shape)

    def __getstate__(self) -> dict:
        return {"shape": self._shape}

    def __setstate__(self, state) -> None:
        self._shape = state["shape"]


class SpectralGeography(EmptyGeography):
    pass


class LatLonGeography(GeographyBase):
    def __init__(self, latitudes, longitudes, proj_str=None, shape=None) -> None:
        self._lat = latitudes
        self._lon = longitudes
        self._proj_str = proj_str
        self._shape = shape

    def latitudes(self, dtype=None) -> np.ndarray:
        return np.asarray(self._lat, dtype=dtype).reshape(self._shape)

    def longitudes(self, dtype=None) -> np.ndarray:
        return np.asarray(self._lon, dtype=dtype).reshape(self._shape)

    def distinct_latitudes(self, dtype=None) -> None:
        return None

    def distinct_longitudes(self, dtype=None) -> None:
        return None

    def x(self, dtype=None) -> None:
        raise NotImplementedError("x is not implemented for this geography")

    def y(self, dtype=None) -> None:
        raise NotImplementedError("y is not implemented for this geography")

    def shape(self) -> tuple:
        if self._shape is not None:
            return self._shape
        return self.latitudes.shape

    def unique_grid_id(self) -> str:
        return str(self.shape())

    def grid(self) -> None:
        return None

    def _north(self) -> float:
        return float(np.amax(self.latitudes()))

    def _south(self) -> float:
        return float(np.amin(self.latitudes()))

    def _west(self) -> float:
        return float(np.amin(self.longitudes()))

    def _east(self) -> float:
        return float(np.amax(self.longitudes()))

    def projection(self) -> Optional[Projection]:
        if self._proj_str:
            return Projection.from_proj_string(self._proj_str)
        return None
        # return Projection.from_proj_string(self.metadata.get("projTargetString", None))

    def bounding_box(self) -> BoundingBox:
        return BoundingBox(
            north=self._north(),
            south=self._south(),
            west=self._west(),
            east=self._east(),
        )

    def grid_spec(self) -> None:
        return None

    def area(self) -> tuple:
        return (self._north(), self._west(), self._south(), self._east())

    def grid_type(self) -> str:
        return "_unstructured"

    @classmethod
    def from_dict(cls, data, shape_hint=None) -> "LatLonGeography":
        return _create_geography_from_dict(data, shape_hint=shape_hint)


class MeshedLatLonGeography(LatLonGeography):
    def __init__(self, latitudes, longitudes, proj_str=None) -> None:
        super().__init__(None, None, proj_str=proj_str)
        self._distinct_lat = latitudes
        self._distinct_lon = longitudes

    def latitudes(self, dtype=None) -> np.ndarray:
        lat = self.distinct_latitudes(dtype=dtype)
        n_lon = len(self.distinct_longitudes())
        v = np.repeat(lat[:, np.newaxis], n_lon, axis=1)
        return v

    def longitudes(self, dtype=None) -> np.ndarray:
        lon = self.distinct_longitudes(dtype=dtype)
        n_lat = len(self.distinct_latitudes())
        v = np.repeat(lon[np.newaxis, :], n_lat, axis=0)
        return v

    def distinct_latitudes(self, dtype=None) -> np.ndarray:
        return np.asarray(self._distinct_lat, dtype=dtype)

    def distinct_longitudes(self, dtype=None) -> np.ndarray:
        return np.asarray(self._distinct_lon, dtype=dtype)

    def shape(self) -> tuple:
        Nj = len(self.distinct_latitudes())
        Ni = len(self.distinct_longitudes())
        return (Nj, Ni)

    def grid_type(self) -> str:
        return "_distinct_ll"


class GridsSpecBasedGeography(GeographyBase):
    def __init__(self, grid_or_grid_spec) -> None:
        from eckit.geo import Grid

        if isinstance(grid_or_grid_spec, Grid):
            self._grid = grid_or_grid_spec
            self._grid_spec_in = None
        else:
            self._grid = Grid(grid_or_grid_spec)
            self._grid_spec_in = grid_or_grid_spec

    def latitudes(self, dtype=None) -> np.ndarray:
        r"""Return the latitudes of the field.

        Returns
        -------
        ndarray
        """
        v, _ = self._grid.to_latlons()
        import numpy as np

        v = np.asarray(v).reshape(self.shape())

        if dtype is None:
            dtype = np.float64
        v = adjust_array(v, dtype=dtype)

        return v

    def longitudes(self, dtype=None) -> np.ndarray:
        r"""Return the longitudes of the field.

        Returns
        -------
        ndarray
        """
        _, v = self._grid.to_latlons()
        import numpy as np

        v = np.asarray(v).reshape(self.shape())

        if dtype is None:
            dtype = np.float64
        v = adjust_array(v, dtype=dtype)

        return v

    def distinct_latitudes(self, dtype=None) -> None:
        return None

    def distinct_longitudes(self, dtype=None) -> None:
        return None

    def x(self, dtype=None) -> np.ndarray:
        r"""Return the x coordinates in the field's original CRS.

        Returns
        -------
        ndarray
        """
        return self.longitudes(dtype=dtype)

    def y(self, dtype=None) -> np.ndarray:
        r"""Return the y coordinates in the field's original CRS.

        Returns
        -------
        ndarray
        """
        return self.latitudes(dtype=dtype)

    def shape(self) -> tuple:
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

    def unique_grid_id(self) -> str:
        return self._grid.uid

    def projection(self) -> Projection:
        return Projection.from_proj_string(proj_string=None)

    def bounding_box(self) -> BoundingBox:
        bb = self._grid.bounding_box()
        return BoundingBox(
            north=bb[0],
            south=bb[2],
            west=bb[1],
            east=bb[3],
        )

    def grid_spec(self) -> Optional[dict]:
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

    def grid(self) -> object:
        return self._grid

    def grid_type(self) -> str:
        return self._grid.type

    @classmethod
    def from_dict(cls, data, shape_hint=None) -> "GridsSpecBasedGeography":
        return _create_geography_from_dict(data, shape_hint=shape_hint)

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
