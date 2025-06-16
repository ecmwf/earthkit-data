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


class Vertical(metaclass=ABCMeta):
    @property
    @abstractmethod
    def level(self):
        """Return the metadata of the vertical object."""
        pass

    @property
    @abstractmethod
    def level_type(self):
        """Return the metadata of the vertical object."""
        pass
