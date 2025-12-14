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

from earthkit.data.field.spec.level_type import LevelTypes
from earthkit.data.field.vertical import VerticalFieldPart

from .collector import GribContextCollector
from .core import GribFieldPart


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


class SpecMatcher:
    def match(self, spec):
        return True


class IntSpecMatcher(SpecMatcher):
    def match(self, spec):
        return int(spec.level) == spec.level


class NonIntSpecMatcher(SpecMatcher):
    def match(self, spec):
        return int(spec.level) != spec.level


class GribVerticalType(metaclass=ABCMeta):
    def __init__(self, key, spec_type, converter=Converter(), spec_matcher=SpecMatcher()):
        self.key = key
        self.spec_type = spec_type
        self.spec_matcher = spec_matcher
        self.converter = converter

    @abstractmethod
    def from_grib(self, handle):
        pass

    @abstractmethod
    def to_grib(self, spec):
        pass

    @abstractmethod
    def match(self, spec):
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

        return level, layer, self.spec_type

    def to_grib(self, spec):
        level = self.converter.to_grib(spec.level)

        return {
            "level": level,
            "typeOfLevel": self.key,
        }

    def match(self, spec):
        return self.spec_matcher.match(spec)


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

        return level, layer, self.spec_type

    def to_grib(self, spec):
        layer = self.converter.to_grib(spec.layer)
        top, bottom = layer

        return {
            "topLevel": top,
            "bottomLevel": bottom,
            "typeOfLevel": self.key,
        }

    def match(self, spec):
        return spec.layer is not None and self.spec_matcher.match(spec)


_TYPES = [
    GribLevelType("isobaricInhPa", LevelTypes.PRESSURE, spec_matcher=IntSpecMatcher()),
    GribLevelType(
        "isobaricInPa", LevelTypes.PRESSURE, converter=PressurePaConverter(), spec_matcher=NonIntSpecMatcher()
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
_SPEC_TYPES = defaultdict(list)
for k, v in _GRIB_TYPES.items():
    _SPEC_TYPES[v.spec_type.value.name].append(v)

for k in list(_SPEC_TYPES.keys()):
    if len(_SPEC_TYPES[k]) == 1:
        _SPEC_TYPES[k] = _SPEC_TYPES[k][0]
    else:
        _SPEC_TYPES[k] = tuple(_SPEC_TYPES[k])


class GribVerticalBuilder:
    @staticmethod
    def build(handle):
        d = GribVerticalBuilder._build_dict(handle)
        spec = VerticalFieldPart.from_dict(d)
        # spec._set_private_data("handle", handle)
        return spec

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
    def collect_keys(spec, context):
        grib_level_type = _SPEC_TYPES.get(spec.type)
        if isinstance(grib_level_type, tuple):
            t = grib_level_type
            grib_level_type = None
            for x in t:
                if x.match(spec):
                    grib_level_type = x
                    break

        if grib_level_type is None:
            raise ValueError(f"Unknown level type: {spec.type}")

        r = grib_level_type.to_grib(spec)
        context.update(r)


COLLECTOR = GribVerticalContextCollector()


class GribVertical(GribFieldPart):
    BUILDER = GribVerticalBuilder
    COLLECTOR = COLLECTOR
