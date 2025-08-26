# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from ...core.spec.data import ArrayData
from ...core.spec.parameter import Parameter
from ...core.spec.vertical import Vertical
from ..labels import RawLabels


def missing_is_none(x):
    return None if x == 2147483647 else x


def _get(d, choices):
    for c in choices:
        if c in d:
            return d[c]
        if c.lower() in d:
            return d[c.lower()]

    return None


class LodData(ArrayData):
    def __init__(self, d):
        v = d["values"]
        if isinstance(v, list):
            import numpy as np

            v = np.array(v)

        super().__init__(v)


class LodParameter(Parameter):
    NAME_ALIASES = {"name", "param", "shortName"}
    UNITS_ALIASES = {"units", "unit"}

    def __init__(self, d):
        self._name = _get(d, LodParameter.NAME_ALIASES)
        self._units = _get(d, LodParameter.UNITS_ALIASES)

    @property
    def name(self):
        return self._name

    @property
    def units(self):
        return self._units


class LodVertical(Vertical):
    LEVEL_ALIASES = {"level", "levelist"}
    LEVEL_TYPE_ALIASES = {"level_type", "levtype", "typeOfLevel"}

    def __init__(self, d):
        self._level = _get(d, LodVertical.LEVEL_ALIASES)
        self._level_type = _get(d, LodVertical.LEVEL_TYPE_ALIASES)

    @property
    def level(self):
        return self._level

    @property
    def level_type(self):
        return self._level_type


# class LodTime(FieldTime):
#     def __init__(self, d):
#         k = {k: v for k, v in d.items() if k in TimeSpec.KEYS}
#         self._spec = TimeSpec.from_dict(k)

#     @property
#     def spec(self):
#         return self._spec


LodLabels = RawLabels
