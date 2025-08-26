# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import abstractmethod

from .spec import Spec


class GeographySpec(Spec):
    KEYS = ("latitudes", "longitudes", "projection", "unique_grid_id")

    @property
    @abstractmethod
    def shape(self):
        pass

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

    @classmethod
    def from_grib(cls, handle):
        from ...specs.grib.geography import GribGeography

        return GribGeography(handle)

    @classmethod
    def from_dict(cls, data):
        from ...specs.dict.geography import make_geography

        spec = make_geography(data)
        return spec

    def set(self, *args, **kwargs):
        kwargs = self.normalise_set_kwargs(*args, **kwargs)

        keys = set(kwargs.keys())

        if keys == {"latitudes", "longitudes"}:
            spec = self.from_dict(kwargs)
            return spec

        raise ValueError("Invalid keys for Geography specification")
