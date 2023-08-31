# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import ABCMeta, abstractmethod


class Geography(metaclass=ABCMeta):
    """Geographical information about a field or data unit"""

    @abstractmethod
    def latitudes(self):
        r"""Return the latitudes.

        Returns
        -------
        ndarray
        """
        pass

    @abstractmethod
    def longitudes(self):
        r"""Return the longitudes.

        Returns
        -------
        ndarray
        """
        pass

    @abstractmethod
    def x(self):
        r"""Return the x coordinates in the original CRS.

        Returns
        -------
        ndarray
        """
        pass

    @abstractmethod
    def y(self):
        r"""Return the y coordinates in the original CRS.

        Returns
        -------
        ndarray
        """
        pass

    @property
    @abstractmethod
    def shape(self):
        r"""Return the shape of the grid or data values.

        Returns
        -------
        tuple
        """
        pass

    @abstractmethod
    def _unique_grid_id(self):
        r"""Return a unique id of the grid of a field."""
        pass

    @abstractmethod
    def projection(self):
        r"""Return information about projection.

        Returns
        -------
        :obj:`Projection`
        """
        pass

    @abstractmethod
    def bounding_box(self):
        r"""Return the bounding box.

        Returns
        -------
        :obj:`BoundingBox <data.utils.bbox.BoundingBox>`
        """
        pass
