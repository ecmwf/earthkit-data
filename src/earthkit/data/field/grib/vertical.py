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


def from_grib(handle):
    def _get(key, default=None):
        return handle.get(key, default=default)

    level = _get("level")
    if level is None:
        level = _get("topLevel")

    level = level
    layer = None

    return level, layer


_TYPES = [
    GribLevelType("isobaricInhPa", LevelTypes.PRESSURE, component_matcher=IntComponentMatcher()),
    GribLevelType(
        "isobaricInPa",
        LevelTypes.PRESSURE,
        converter=PressurePaConverter(),
        component_matcher=NonIntComponentMatcher(),
    ),
    GribLevelType("depthBelowLand", LevelTypes.DEPTH_BG_LEVEL),
    GribLayerType("depthBelowLandLayer", LevelTypes.DEPTH_BG_LEVEL),
    GribLayerType("depthBelowSeaLayer", LevelTypes.DEPTH_BS_LAYER),
    GribLevelType("entireAtmosphere", LevelTypes.ENTIRE_ATMOSPHERE),
    GribLevelType("generalVerticalLayer", LevelTypes.GENERAL),
    GribLevelType("heightAboveSea", LevelTypes.HEIGHT_AS_LEVEL),
    GribLevelType("heightAboveGround", LevelTypes.HEIGHT_AG_LEVEL),
    GribLevelType("hybrid", LevelTypes.MODEL),
    GribLevelType("iceLayerOnWater", LevelTypes.ICE_LAYER_ON_WATER),
    GribLayerType("isobaricLayer", LevelTypes.PRESSURE),  # hPa
    GribLevelType("isothermal", LevelTypes.TEMPERATURE),
    GribLevelType("meanSea", LevelTypes.MEAN_SEA),
    GribLevelType("mixedLayerDepthByDensity", LevelTypes.MIXED_LAYER_DEPTH_BY_DENSITY),
    GribLevelType("oceanSurface", LevelTypes.OCEAN_SURFACE),
    GribLevelType("potentialVorticity", LevelTypes.PV),
    GribLevelType("snowLayer", LevelTypes.SNOW),
    GribLevelType("surface", LevelTypes.SURFACE),
    GribLevelType("theta", LevelTypes.THETA),
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


# TODO: make it thread safe
def register_grib_level_type(
    key: str,
    component_type: LevelTypes,
    converter: Converter = Converter(),
    component_matcher: ComponentMatcher = ComponentMatcher(),
):
    if key in _GRIB_TYPES:
        raise ValueError(f"GRIB level type {key} already exists")

    grib_level_type = GribLevelType(key, component_type, converter, component_matcher)
    _GRIB_TYPES[key] = grib_level_type
    _COMPONENT_TYPES[component_type.name].append(grib_level_type)
    return grib_level_type


class GribVerticalBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.field.component.vertical import Vertical
        from earthkit.data.field.handler.vertical import VerticalFieldComponentHandler

        d = GribVerticalBuilder._build_dict(handle)
        component = Vertical.from_dict(d)
        handler = VerticalFieldComponentHandler.from_component(component)
        return handler

    @staticmethod
    def _build_dict(handle):
        level_type = handle.get("typeOfLevel", None)
        t = _GRIB_TYPES.get(level_type)
        if t is None:
            from earthkit.data.field.component.level_type import get_level_type

            level, layer = from_grib(handle)
            component = get_level_type(level_type)
            t = register_grib_level_type(
                key=level_type,
                component_type=component,
            )

        if t is None:
            raise ValueError(f"Unsupported level type: {level_type}")

        level, layer, level_type = t.from_grib(handle)

        return dict(
            level=level,
            layer=layer,
            level_type=level_type,
        )


class GribVerticalContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(handler, context):
        component = handler.component
        grib_level_type = _COMPONENT_TYPES.get(component.level_type())
        if isinstance(grib_level_type, tuple):
            t = grib_level_type
            grib_level_type = None
            for x in t:
                if x.match(component):
                    grib_level_type = x
                    break

        if grib_level_type is None:
            raise ValueError(f"Unknown level type: {component.level_type()}")

        r = grib_level_type.to_grib(component)
        context.update(r)


COLLECTOR = GribVerticalContextCollector()


class GribVertical(GribFieldComponentHandler):
    BUILDER = GribVerticalBuilder
    COLLECTOR = COLLECTOR
