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


class Time(metaclass=ABCMeta):
    @property
    @abstractmethod
    def base_datetime(self):
        """Return the valid datetime of the time object."""
        pass

    @property
    def forecast_reference_time(self):
        """Return the forecast reference time of the time object."""
        return self.base_datetime

    @property
    @abstractmethod
    def valid_datetime(self):
        """Return the valid datetime of the time object."""
        pass

    @property
    @abstractmethod
    def step(self):
        """Return the forecast period of the time object."""
        pass

    @property
    @abstractmethod
    def range(self):
        """Return the forecast period of the time object."""
        pass
