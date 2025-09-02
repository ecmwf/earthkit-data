# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import abstractmethod

from .spec import SimpleSpec
from .spec import normalise_set_kwargs


class Geography(SimpleSpec):
    KEYS = ("latitudes", "longitudes", "projection", "unique_grid_id", "shape", "grid_type")

    @property
    @abstractmethod
    def latitudes(self):
        r"""array-like: Return the latitudes."""
        pass

    @property
    @abstractmethod
    def longitudes(self):
        r"""array-like: Return the longitudes."""
        pass

    @property
    @abstractmethod
    def distinct_latitudes(self):
        r"""Return the distinct latitudes."""
        pass

    @property
    @abstractmethod
    def distinct_longitudes(self):
        r"""Return the distinct longitudes."""
        pass

    @property
    @abstractmethod
    def x(self):
        r"""array-like: Return the x coordinates in the original CRS."""
        pass

    @property
    @abstractmethod
    def y(self):
        r"""array-like: Return the y coordinates in the original CRS."""
        pass

    @property
    @abstractmethod
    def shape(self):
        pass

    @property
    @abstractmethod
    def projection(self):
        """Return the projection."""
        pass

    @property
    @abstractmethod
    def bounding_box(self):
        """:obj:`BoundingBox <data.utils.bbox.BoundingBox>`: Return the bounding box."""
        pass

    @property
    @abstractmethod
    def unique_grid_id(self):
        r"""str: Return the unique id of the grid."""
        pass

    @property
    @abstractmethod
    def grid_spec(self):
        r"""Return the grid specification."""
        pass

    @property
    @abstractmethod
    def grid_type(self):
        r"""Return the grid specification."""
        pass


class SimpleGeography(Geography):
    @classmethod
    def from_dict(cls, data, values_shape=None):
        from .dict.geography import make_geography

        spec = make_geography(data, values_shape=values_shape)
        return spec

    @classmethod
    def from_grib(cls, handle):
        from .grib.geography import GribGeography

        return GribGeography(handle)

    @classmethod
    def from_xarray(cls, owner, selection):
        from .xarray.geography import XArrayGeography

        return XArrayGeography(owner, selection)

    def set(self, *args, **kwargs):
        kwargs = normalise_set_kwargs(self, *args, add_spec_keys=False, **kwargs)

        keys = set(kwargs.keys())

        if keys == {"latitudes", "longitudes"}:
            spec = self.from_dict(kwargs)
            return spec

        raise ValueError(f"Invalid {keys=} for Geography specification")

    @property
    def grid_spec(self):
        return None
