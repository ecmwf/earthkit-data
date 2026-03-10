# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from . import ObjectWrapperData


class FloatData(ObjectWrapperData):
    _TYPE_NAME = "float"

    @property
    def available_types(self) -> list:
        return [self._NUMPY, self._ARRAY, "value"]

    def describe(self):
        return f"Float data: {self._data}"

    def to_numpy(self, copy=False, **kwargs):
        import numpy as np

        return np.asarray(self._data)

    def to_value(self) -> float:
        return self._data


def wrapper(data, *args, **kwargs):
    if isinstance(data, float):
        return FloatData(data)
    return None
