# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime

from . import ObjectWrapperData


class IntData(ObjectWrapperData):
    _TYPE_NAME = "int"

    @property
    def available_types(self) -> list:
        return [self._NUMPY, self._ARRAY, "value", "datetime", "datetime_list"]

    def describe(self):
        return f"Integer data: {self._data}"

    def to_datetime(self):
        if self._data <= 0:
            date = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(days=self._data)
            return datetime.datetime(date.year, date.month, date.day)
        else:
            return datetime.datetime(self._data // 10000, self._data % 10000 // 100, self._data % 100)

    def to_datetime_list(self):
        return [self.to_datetime()]

    def to_numpy(self, copy=False, **kwargs):
        import numpy as np

        return np.asarray(self._data)

    def to_value(self):
        return self._data


def wrapper(data, *args, **kwargs):
    if isinstance(data, int):
        return IntData(data)
    return None
