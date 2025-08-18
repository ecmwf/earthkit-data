# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import ABCMeta
from abc import abstractmethod


class Geography(metaclass=ABCMeta):
    KEYS = ("latitudes", "longitudes", "projection", "unique_grid_id")

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
