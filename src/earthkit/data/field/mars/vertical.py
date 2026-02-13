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

from earthkit.data.field.component.level_type import LevelTypes


class Converter:
    def from_mars(self, value):
        return value


class PressurePaConverter(Converter):
    def from_mars(self, value):
        if value is not None:
            return value / 100.0
        return value


class MarsVerticalType(metaclass=ABCMeta):
    def __init__(self, key, component_type, converter=Converter()):
        self.key = key
        self.component_type = component_type
        self.converter = converter

    @abstractmethod
    def from_mars(self, handle):
        pass


def _get_one_of(request, keys, default=None):
    for k in keys:
        v = request.get(k, default)
        if v is not None:
            return v
    return default


class MarsLevelType(MarsVerticalType):
    def from_mars(self, request):
        level = _get_one_of(request, ["level", "levelist"])
        level = self.converter.from_mars(level)
        layer = None

        return level, layer, self.component_type


_TYPES = [
    MarsLevelType("pl", LevelTypes.PRESSURE),
    MarsLevelType("ml", LevelTypes.MODEL),
    MarsLevelType("pt", LevelTypes.THETA),
    MarsLevelType("pv", LevelTypes.PV),
    MarsLevelType("sfc", LevelTypes.SURFACE),
    MarsLevelType("sol", LevelTypes.SNOW),
]

# mapping from mars keys to MarsLevelType
_MARS_TYPES = {t.key: t for t in _TYPES}

assert len(_MARS_TYPES) == len(_TYPES), "Duplicate level type keys"


class MarsVerticalBuilder:
    @staticmethod
    def build(request, build_empty=False):
        from earthkit.data.field.component.vertical import Vertical
        from earthkit.data.field.vertical import VerticalFieldComponentHandler

        d = MarsVerticalBuilder._build_dict(request)
        if not d and not build_empty:
            return None

        component = Vertical.from_dict(d)
        handler = VerticalFieldComponentHandler.from_component(component)
        return handler

    @staticmethod
    def _build_dict(request):
        level_type = request.get("levtype", None)
        t = _MARS_TYPES.get(level_type)
        if t is None:
            raise ValueError(f"Unsupported level type: {level_type}")

        level, layer, level_type = t.from_mars(request)
        return dict(
            level=level,
            layer=layer,
            level_type=level_type,
        )
