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
from .component import mark_key


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
            return NoGeography(shape_hint)

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
        dx = uniform_resolution(lon)
        dy = uniform_resolution(lat)

        if dx is not None and dy is not None:
            # metadata["DxInDegrees"] = dx
            # metadata["DyInDegrees"] = dy
            return RegularDistinctLLGeography(lat, lon, proj_str)
        else:
            return DistinctLLGeography(lat, lon, proj_str=proj_str)
    else:
        if lat.shape != lon.shape:
            raise ValueError(f"latitudes and longitudes must have the same shape. {lat.shape} != {lon.shape}")

        if shape_hint is not None:
            if lat.size == expected_size:
                if lat.shape != shape_hint:
                    shape = lat.shape if lat.ndim > len(shape_hint) else shape_hint
                else:
                    shape = lat.shape

                return SimpleGeography(lat, lon, proj_str=proj_str, shape=shape)

            else:
                raise ValueError(
                    (
                        "Number of points do not match expected size. "
                        f"Expected=({expected_size}), got={lat.size}"
                    )
                )
        else:
            shape = lat.shape
            return SimpleGeography(lat, lon, proj_str=proj_str, shape=shape)


def create_geography_from_dict(d, shape_hint=None):
    return create_geography_from_array(
        latitudes=d.get("latitudes", None),
        longitudes=d.get("longitudes", None),
        distinct_latitudes=d.get("distinct_latitudes", None),
        distinct_longitudes=d.get("distinct_longitudes", None),
        proj_str=d.get("projTargetString", None),
        shape_hint=shape_hint,
    )


@component_keys
class BaseGeography(SimpleFieldComponent):
    @mark_key("get")
    @abstractmethod
    def latitudes(self):
        r"""array-like: Return the latitudes."""
        pass

    @mark_key("get")
    @abstractmethod
    def longitudes(self):
        r"""array-like: Return the longitudes."""
        pass

    @mark_key("get")
    @abstractmethod
    def distinct_latitudes(self):
        r"""Return the distinct latitudes."""
        pass

    @mark_key("get")
    @abstractmethod
    def distinct_longitudes(self):
        r"""Return the distinct longitudes."""
        pass

    @mark_key("get")
    @abstractmethod
    def x(self):
        r"""array-like: Return the x coordinates in the original CRS."""
        pass

    @mark_key("get")
    @abstractmethod
    def y(self):
        r"""array-like: Return the y coordinates in the original CRS."""
        pass

    @mark_key("get")
    @abstractmethod
    def shape(self):
        pass

    @mark_key("get")
    @abstractmethod
    def projection(self):
        """Return the projection."""
        pass

    @mark_key("get")
    @abstractmethod
    def bounding_box(self):
        """:obj:`BoundingBox <data.utils.bbox.BoundingBox>`: Return the bounding box."""
        pass

    @mark_key("get")
    @abstractmethod
    def unique_grid_id(self):
        r"""str: Return the unique id of the grid."""
        pass

    @mark_key("get")
    @abstractmethod
    def grid_spec(self):
        r"""Return the grid specification."""
        pass

    @mark_key("get")
    @abstractmethod
    def grid_type(self):
        r"""Return the grid specification."""
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

    def __getstate__(self):
        return super().__getstate__()

    def __setstate__(self, state):
        super().__setstate__(state)


class NoGeography(BaseGeography):
    def __init__(self, shape):
        self._shape = shape

    def latitudes(self):
        return None

    def longitudes(self):
        return None

    def distinct_latitudes(self):
        return None

    def distinct_longitudes(self):
        return None

    def x(self):
        raise NotImplementedError("x is not implemented for this geography")

    def y(self):
        raise NotImplementedError("y is not implemented for this geography")

    def shape(self):
        return self._shape

    def unique_grid_id(self):
        return self.shape()

    def projection(self):
        return None

    def bounding_box(self):
        return None

    def grid_spec(self):
        return None

    def resolution(self):
        return None
        # raise NotImplementedError("resolution is not implemented for this geography")

    def mars_area(self):
        return None

    def mars_grid(self):
        raise NotImplementedError("mars_grid is not implemented for this geography")

    def grid_type(self):
        return "none"

    @classmethod
    def from_dict(cls, d):
        if not isinstance(d, dict):
            raise TypeError("data must be a dictionary")
        shape = d.get("shape", None)
        if "shape" in d and len(d) > 1:
            raise ValueError("NoGeography can only be created from a dictionary with a single key 'shape'")
        return cls(shape=shape)

    def __getstate__(self):
        return {"shape": self._shape}

    def __setstate__(self, state):
        self._shape = state["shape"]


class SimpleGeography(BaseGeography):
    def __init__(self, latitudes, longitudes, proj_str=None, shape=None):
        self._lat = latitudes
        self._lon = longitudes
        self._proj_str = proj_str
        self._shape = shape

    def latitudes(self):
        return np.asarray(self._lat)

    def longitudes(self):
        return np.asarray(self._lon)

    def distinct_latitudes(self):
        return None

    def distinct_longitudes(self):
        return None

    def x(self):
        raise NotImplementedError("x is not implemented for this geography")

    def y(self):
        raise NotImplementedError("y is not implemented for this geography")

    def shape(self):
        if self._shape is not None:
            return self._shape
        return self.latitudes.shape

    def unique_grid_id(self):
        return self.shape()

    def _north(self):
        return np.amax(self.latitudes)

    def _south(self):
        return np.amin(self.latitudes)

    def west(self):
        return np.amin(self.longitudes)

    def _east(self):
        return np.amax(self.longitudes)

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

    def resolution(self):
        return None
        # raise NotImplementedError("resolution is not implemented for this geography")

    def mars_area(self):
        return [self.north(), self.west(), self.south(), self.east()]

    def mars_grid(self):
        raise NotImplementedError("mars_grid is not implemented for this geography")

    def grid_type(self):
        return "_unstructured"

    @classmethod
    def from_dict(cls, data, shape_hint=None):
        return create_geography_from_dict(data, shape_hint=shape_hint)


class DistinctLLGeography(SimpleGeography):
    def __init__(self, latitudes, longitudes, proj_str=None):
        super().__init__(None, None, proj_str=proj_str)
        self._distinct_lat = latitudes
        self._distinct_lon = longitudes

    def latitudes(self):
        lat = self.distinct_latitudes()
        n_lon = len(self.distinct_longitudes())
        v = np.repeat(lat[:, np.newaxis], n_lon, axis=1)
        return v

    def longitudes(self):
        lon = self.distinct_longitudes()
        n_lat = len(self.distinct_latitudes())
        v = np.repeat(lon[np.newaxis, :], n_lat, axis=0)
        return v

    def distinct_latitudes(self):
        return np.asarray(self._distinct_lat)

    def distinct_longitudes(self):
        return np.asarray(self._distinct_lon)

    def shape(self):
        Nj = len(self.distinct_latitudes())
        Ni = len(self.distinct_longitudes())
        return (Nj, Ni)

    def grid_type(self):
        return "_distinct_ll"


class RegularDistinctLLGeography(DistinctLLGeography):
    def dx(self):
        x = self.metadata.get("DxInDegrees", None)
        if x is None:
            lon = self.distinct_longitudes()
            x = lon[1] - lon[0]
        x = abs(round(x * 1_000_000) / 1_000_000)
        return x

    def dy(self):
        y = self.metadata.get("DyInDegrees", None)
        if y is None:
            lat = self.distinct_latitudes()
            y = lat[0] - lat[1]
        y = abs(round(y * 1_000_000) / 1_000_000)
        return y

    def resolution(self):
        x = self.dx()
        y = self.dy()
        if x == y:
            return x

    def mars_grid(self):
        return [self.dx(), self.dy()]

    def grid_type(self):
        return "_regular_ll"
