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
    @property
    @abstractmethod
    def latitudes(self):
        """Return the latitudes of the geometry object."""
        pass

    @property
    @abstractmethod
    def longitudes(self):
        """Return the longitudes of the geometry object."""
        pass

    @property
    @abstractmethod
    def projection(self):
        """Return the metadata of the geometry object."""
        pass
