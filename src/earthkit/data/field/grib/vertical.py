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
from collections import defaultdict

from earthkit.data.field.component.level_type import LevelTypes

from .collector import GribContextCollector
from .core import GribFieldComponentHandler


class Converter:
    def from_grib(self, value):
        return value

    def to_grib(self, value):
        return value


class PressurePaConverter(Converter):
    def from_grib(self, value):
        if value is not None:
            return value / 100.0
        return value

    def to_grib(self, value):
        if value is not None:
            return value * 100.0
        return value


class ComponentMatcher:
    def match(self, component):
        return True


class IntComponentMatcher(ComponentMatcher):
    def match(self, component):
        return int(component.level()) == component.level()


class NonIntComponentMatcher(ComponentMatcher):
    def match(self, component):
        return int(component.level()) != component.level()


class GribVerticalType(metaclass=ABCMeta):
    def __init__(self, key, component_type, converter=Converter(), component_matcher=ComponentMatcher()):
        self.key = key
        self.component_type = component_type
        self.component_matcher = component_matcher
        self.converter = converter

    @abstractmethod
    def from_grib(self, handle):
        pass

    @abstractmethod
    def to_grib(self, component):
        pass

    @abstractmethod
    def match(self, component):
        pass


class GribLevelType(GribVerticalType):
    def from_grib(self, handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        level = _get("level")
        if level is None:
            level = _get("topLevel")

        level = self.converter.from_grib(level)
        layer = None

        return level, layer, self.component_type

    def to_grib(self, component):
        level = self.converter.to_grib(component.level())

        return {
            "level": level,
            "typeOfLevel": self.key,
        }

    def match(self, component):
        return self.component_matcher.match(component)


class GribLayerType(GribVerticalType):
    def from_grib(self, handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        top = _get("topLevel")
        bottom = _get("bottomLevel")

        top = self.converter.from_grib(top)
        bottom = self.converter.from_grib(bottom)
        level = top
        layer = (top, bottom)

        return level, layer, self.component_type

    def to_grib(self, component):
        layer = self.converter.to_grib(component.layer())
        top, bottom = layer

        return {
            "topLevel": top,
            "bottomLevel": bottom,
            "typeOfLevel": self.key,
        }

    def match(self, component):
        return component.layer is not None and self.component_matcher.match(component)


_TYPES = [
    GribLevelType("isobaricInhPa", LevelTypes.PRESSURE, component_matcher=IntComponentMatcher()),
    GribLevelType(
        "isobaricInPa",
        LevelTypes.PRESSURE,
        converter=PressurePaConverter(),
        component_matcher=NonIntComponentMatcher(),
    ),
    GribLevelType("depthBelowLand", LevelTypes.DEPTH_BGL),
    GribLayerType("depthBelowLandLayer", LevelTypes.DEPTH_BGL),
    GribLevelType("generalVerticalLayer", LevelTypes.GENERAL),
    GribLevelType("heightAboveSea", LevelTypes.HEIGHT_ASL),
    GribLevelType("heightAboveGround", LevelTypes.HEIGHT_AGL),
    GribLevelType("hybrid", LevelTypes.MODEL),
    GribLayerType("isobaricLayer", LevelTypes.PRESSURE),  # hPa
    GribLevelType("meanSea", LevelTypes.MEAN_SEA),
    GribLevelType("theta", LevelTypes.THETA),
    GribLevelType("potentialVorticity", LevelTypes.PV),
    GribLevelType("surface", LevelTypes.SURFACE),
    GribLevelType("snowLayer", LevelTypes.SNOW),
]

# mapping from GRIB typeOfLevel key to GribLevelType
_GRIB_TYPES = {t.key: t for t in _TYPES}

assert len(_GRIB_TYPES) == len(_TYPES), "Duplicate level type keys"

# mapping from LevelType to GribLevelType
_COMPONENT_TYPES = defaultdict(list)
for k, v in _GRIB_TYPES.items():
    _COMPONENT_TYPES[v.component_type.value.name].append(v)

for k in list(_COMPONENT_TYPES.keys()):
    if len(_COMPONENT_TYPES[k]) == 1:
        _COMPONENT_TYPES[k] = _COMPONENT_TYPES[k][0]
    else:
        _COMPONENT_TYPES[k] = tuple(_COMPONENT_TYPES[k])


class GribVerticalBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.component.vertical import Vertical
        from earthkit.data.field.vertical import VerticalFieldComponentHandler

        d = GribVerticalBuilder._build_dict(handle)
        component = Vertical.from_dict(d)
        handler = VerticalFieldComponentHandler.from_component(component)
        return handler

    @staticmethod
    def _build_dict(handle):
        level_type = handle.get("typeOfLevel", None)
        t = _GRIB_TYPES.get(level_type)
        if t is None:
            raise ValueError(f"Unsupported level type: {level_type}")

        level, layer, level_type = t.from_grib(handle)
        return dict(
            level=level,
            layer=layer,
            type=level_type,
        )


class GribVerticalContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(handler, context):
        component = handler.component
        grib_level_type = _COMPONENT_TYPES.get(component.type())
        if isinstance(grib_level_type, tuple):
            t = grib_level_type
            grib_level_type = None
            for x in t:
                if x.match(component):
                    grib_level_type = x
                    break

        if grib_level_type is None:
            raise ValueError(f"Unknown level type: {component.type()}")

        r = grib_level_type.to_grib(component)
        context.update(r)


COLLECTOR = GribVerticalContextCollector()


class GribVertical(GribFieldComponentHandler):
    BUILDER = GribVerticalBuilder
    COLLECTOR = COLLECTOR
