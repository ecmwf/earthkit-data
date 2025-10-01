# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from collections import defaultdict

from earthkit.data.specs.vertical import LevelType

from ..vertical import SimpleVerticalSpec
from .collector import GribContextCollector
from .spec import GribSpec


class GribLevelType:
    def __init__(self, key, spec_type):
        self.key = key
        self.spec_type = spec_type

    def level_from_grib(self, value):
        return value

    def level_to_grib(self, value):
        return value

    def match(self, spec):
        return spec.level_type == self.spec_type


class PressureHPaGribLevelType(GribLevelType):
    def __init__(self):
        super().__init__("isobaricInhPa", LevelType.PRESSURE)

    def match(self, spec):
        if spec.level_type == self.spec_type and spec.level is not None:
            return int(spec.level) == spec.level
        return False


class PressurePaGribLevelType(GribLevelType):
    def __init__(self):
        super().__init__("isobaricInPa", LevelType.PRESSURE)

    def level_from_grib(self, value):
        if value is not None:
            return value / 100.0
        return value

    def level_to_grib(self, value):
        if value is not None:
            return value * 100.0
        return value

    def match(self, spec):
        if spec.level_type == self.spec_type and spec.level is not None:
            return int(spec.level) != spec.level
        return False


_TYPES = [
    PressureHPaGribLevelType(),
    PressurePaGribLevelType(),
    GribLevelType("depthBelowLand", LevelType.DEPTH_BGL),
    GribLevelType("depthBelowLandLayer", LevelType.DEPTH_BGL_LAYER),
    GribLevelType("generalVerticalLayer", LevelType.GENERAL),
    GribLevelType("heightAboveSea", LevelType.HEIGHT_ASL),
    GribLevelType("heightAboveGround", LevelType.HEIGHT_AGL),
    GribLevelType("hybrid", LevelType.MODEL),
    GribLevelType("isobaricLayer", LevelType.PRESSURE_LAYER),
    GribLevelType("meanSea", LevelType.MEAN_SEA),
    GribLevelType("theta", LevelType.THETA),
    GribLevelType("potentialVorticity", LevelType.PV),
    GribLevelType("surface", LevelType.SURFACE),
    GribLevelType("snowLayer", LevelType.SNOW),
]

# mapping from GRIB typeOfLevel key to GribLevelType
_GRIB_TYPES = {t.key: t for t in _TYPES}

assert len(_GRIB_TYPES) == len(_TYPES), "Duplicate level type keys"

# mapping from LevelType to GribLevelType
_SPEC_TYPES = defaultdict(list)
for k, v in _GRIB_TYPES.items():
    _SPEC_TYPES[v.spec_type].append(v)

for k in list(_SPEC_TYPES.keys()):
    if len(_SPEC_TYPES[k]) == 1:
        _SPEC_TYPES[k] = _SPEC_TYPES[k][0]
    else:
        _SPEC_TYPES[k] = tuple(_SPEC_TYPES[k])


class GribVerticalBuilder:
    @staticmethod
    def build(handle):

        d = GribVerticalBuilder._build_dict(handle)
        spec = SimpleVerticalSpec.from_dict(d)
        # spec._set_private_data("handle", handle)
        return spec

    @staticmethod
    def _build_dict(handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        level = _get("level")
        if level is None:
            level = _get("topLevel")

        level_type = _get("typeOfLevel")
        try:
            t = _GRIB_TYPES.get(level_type)
            if t is not None:
                level = t.level_from_grib(level)
                level_type = t.spec_type
        except Exception as e:
            raise ValueError(f"Cannot convert level {level} of type {level_type}: {e}")

        return dict(
            level_value=level,
            level_type=level_type,
        )


class GribVerticalContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(spec, context):
        grib_level_type = _SPEC_TYPES.get(spec.level_type)
        if isinstance(grib_level_type, tuple):
            t = grib_level_type
            grib_level_type = None
            for x in t:
                if x.match(spec):
                    grib_level_type = x
                    break

        if grib_level_type is None:
            raise ValueError(f"Unknown level type: {spec.level_type}")

        level = grib_level_type.level_to_grib(spec.level)

        r = {
            "level": level,
            "typeOfLevel": grib_level_type.key,
        }

        context.update(r)


COLLECTOR = GribVerticalContextCollector()


class GribVertical(GribSpec):
    BUILDER = GribVerticalBuilder
    COLLECTOR = COLLECTOR


# class GribVerticalSpec(SimpleVerticalSpec):
#     def __init__(self, handle) -> None:
#         self._handle = handle

#     @thread_safe_cached_property
#     def data(self):
#         return self.BUILDER.build(self._handle)
