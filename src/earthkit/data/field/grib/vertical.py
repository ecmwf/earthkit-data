# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
from abc import ABCMeta, abstractmethod
from collections import defaultdict

from earthkit.data.field.component.level_parameters import HybridLevelParametersBase
from earthkit.data.field.component.level_type import LevelTypes

from .collector import GribContextCollector
from .core import GribFieldComponentHandler


class GribHybridLevelParameters(HybridLevelParametersBase):
    def __init__(self, handle):
        self._handle = handle

    def number_of_levels(self):
        coeff_num = self._handle.get("NV", default=None)
        if coeff_num is not None:
            return int(coeff_num / 2) - 1
        return None

    def coefficients(self):
        pv = self._handle.get("pv", default=None)
        if pv is not None:
            import numpy as np

            coeff_num = int(len(pv) / 2)
            A = np.array(pv[:coeff_num])
            B = np.array(pv[coeff_num:])
            return A, B

        return None

    def coefficient_size(self):
        return 2 * (self.number_of_levels() + 1)


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
    def to_grib(self, component, handle=None):
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

        return {"level": level, "layer": layer, "level_type": self.component_type}

    def to_grib(self, component, handle=None):
        level = self.converter.to_grib(component.level())

        return {
            "level": level,
            "typeOfLevel": self.key,
        }

    def match(self, component):
        return self.component_matcher.match(component)


class GribSurfLevelType(GribVerticalType):
    def from_grib(self, handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        level = 0
        layer = None

        return {"level": level, "layer": layer, "level_type": self.component_type}

    def to_grib(self, component, handle=None):
        return {
            "level": 0,
            "typeOfLevel": self.key,
        }

    def match(self, component):
        return self.component_matcher.match(component)


class HybridGribLevelType(GribLevelType):
    def from_grib(self, handle):
        result = super().from_grib(handle)
        level_parameters = GribHybridLevelParameters(handle)
        result["coefficients"] = level_parameters
        return result

    def to_grib(self, component, handle=None):
        r = super().to_grib(component)

        # this tries to avoid writing the coefficients back to the handle if they are already
        # present and correct, which can be expensive for large coefficient arrays. The check
        # is not robust enough and should be improved.
        if handle is not None and hasattr(component, "level_parameters"):
            level_parameters = component._level_parameters
            if isinstance(level_parameters, GribFieldComponentHandler):
                nv = handle.get("NV", default=None)
                if level_parameters.coefficient_size() == nv:
                    return r

        coefficients = component.coefficients()
        if coefficients is not None:
            import numpy as np

            A, B = coefficients
            r["NV"] = len(A) + len(B)
            r["pv"] = np.concatenate([A, B])

        return r


class GribLayerType(GribVerticalType):
    def from_grib(self, handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        top = _get("topLevel")
        bottom = _get("bottomLevel")

        top = self.converter.from_grib(top)
        bottom = self.converter.from_grib(bottom)
        layer = (top, bottom)

        level = _get("level")

        if level is None:
            if self.component_type.value.level == "top":
                level = top
            else:
                level = bottom

        return {"level": level, "layer": layer, "level_type": self.component_type}

    def to_grib(self, component, handle=None):
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
    GribLevelType("depthBelowLand", LevelTypes.DEPTH_BL_LEVEL),
    GribLayerType("depthBelowLandLayer", LevelTypes.DEPTH_BL_LAYER),
    GribLayerType("depthBelowSeaLayer", LevelTypes.DEPTH_BS_LAYER),
    GribLevelType("entireAtmosphere", LevelTypes.ENTIRE_ATMOSPHERE),
    GribLevelType("generalVerticalLayer", LevelTypes.GENERAL),
    GribLevelType("heightAboveSea", LevelTypes.HEIGHT_AS_LEVEL),
    GribLevelType("heightAboveGround", LevelTypes.HEIGHT_AG_LEVEL),
    HybridGribLevelType("hybrid", LevelTypes.HYBRID),
    GribLevelType("iceLayerOnWater", LevelTypes.ICE_LAYER_ON_WATER),
    GribLayerType("isobaricLayer", LevelTypes.PRESSURE),  # hPa
    GribLevelType("isothermal", LevelTypes.TEMPERATURE),
    GribLevelType("meanSea", LevelTypes.MEAN_SEA),
    GribLevelType("mixedLayerDepthByDensity", LevelTypes.MIXED_LAYER_DEPTH_BY_DENSITY),
    GribLevelType("oceanSurface", LevelTypes.OCEAN_SURFACE),
    GribLevelType("potentialVorticity", LevelTypes.PV),
    GribLayerType("snowLayer", LevelTypes.SNOW),
    GribLevelType("surface", LevelTypes.SURFACE),
    GribLevelType("theta", LevelTypes.THETA),
    GribSurfLevelType("mixingLayer", LevelTypes.MIXING_LAYER),
    GribSurfLevelType("waterSurfaceToIsothermalOceanLayer", LevelTypes.WATER_SURFACE_TO_ISOTHERMAL_OCEAN_LAYER),
    GribSurfLevelType("entireLake", LevelTypes.ENTIRE_LAKE),
    GribLayerType("seaIceLayer", LevelTypes.SEA_ICE_LAYER),
    GribSurfLevelType("iceTopOnWater", LevelTypes.ICE_TOP_ON_WATER),
    GribSurfLevelType("entireMeltPond", LevelTypes.ENTIRE_MELT_POND),
    GribLayerType("lowCloudLayer", LevelTypes.LOW_CLOUD_LAYER),
    GribSurfLevelType("mostUnstableParcel", LevelTypes.MOST_UNSTABLE_PARCEL),
    GribSurfLevelType("snowLayerOverIceOnWater", LevelTypes.SNOW_LAYER_OVER_ICE_ON_WATER),
    GribSurfLevelType("stratosphere", LevelTypes.STRATOSPHERE),
    GribLayerType("highCloudLayer", LevelTypes.HIGH_CLOUD_LAYER),
    GribLayerType("soilLayer", LevelTypes.SOIL_LAYER),
    GribSurfLevelType("oceanSurfaceToBottom", LevelTypes.OCEAN_SURFACE_TO_BOTTOM),
    GribSurfLevelType("lakeBottom", LevelTypes.LAKE_BOTTOM),
    GribSurfLevelType("troposphere", LevelTypes.TROPOSPHERE),
    GribLayerType("mediumCloudLayer", LevelTypes.MEDIUM_CLOUD_LAYER),
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
        level_type = handle.get("typeOfLevel", default=None)
        t = _GRIB_TYPES.get(level_type)
        if t is None:
            from earthkit.data.field.component.level_type import get_level_type

            # level, layer = from_grib(handle)
            component = get_level_type(level_type)
            t = register_grib_level_type(
                key=level_type,
                component_type=component,
            )

        if t is None:
            raise ValueError(f"Unsupported level type: {level_type}")

        r = t.from_grib(handle)
        return r

        # level, layer, level_type = t.from_grib(handle)

        # level_parameters = None
        # if level_type  == LevelTypes.HYBRID:
        #     level_parameters = GribHybridLevelParameters(handle)

        # return dict(
        #     level=level,
        #     layer=layer,
        #     level_type=level_type,
        #      level_parameters=level_parameters,
        #  )


class GribVerticalContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(handler, context):
        component = handler.component
        handle = context.get("handle")
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

        r = grib_level_type.to_grib(component, handle)
        context.update(r)


COLLECTOR = GribVerticalContextCollector()


class GribVertical(GribFieldComponentHandler):
    BUILDER = GribVerticalBuilder
    COLLECTOR = COLLECTOR
