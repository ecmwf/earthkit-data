# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.specs.vertical import LevelTypes

from .collector import GribContextCollector


class GribLevelType:
    def __init__(self, key, item):
        if not isinstance(item, tuple):
            item = (item, None)

        assert len(item) == 2

        self.key = key
        self.type = item[0]
        self.converter = item[1]

    def convert(self, value):
        if self.converter:
            return self.converter(value)
        return value


GRIB_LEVEL_TYPES = {
    "depthBelowLand": LevelTypes.DEPTH_BGL,
    "depthBelowLandLayer": LevelTypes.DEPTH_BGL_LAYER,
    "generalVerticalLayer": LevelTypes.GENERAL,
    "heightAboveSea": LevelTypes.HEIGHT_ASL,
    "heightAboveGround": LevelTypes.HEIGHT_AGL,
    "hybrid": LevelTypes.MODEL,
    "isobaricInhPa": LevelTypes.PRESSURE,
    "isobaricInPa": (LevelTypes.PRESSURE, lambda x: x / 100.0),
    "isobaricLayer": (LevelTypes.PRESSURE_LAYER, lambda x: x / 100.0),
    "meanSea": LevelTypes.MEAN_SEA,
    "theta": LevelTypes.THETA,
    "potentialVorticity": LevelTypes.PV,
    "surface": LevelTypes.SURFACE,
    "snowLayer": LevelTypes.SNOW,
}

GRIB_LEVEL_TYPES = {k: GribLevelType(k, v) for k, v in GRIB_LEVEL_TYPES.items()}


class GribVerticalBuilder:
    @staticmethod
    def build(handle):
        from earthkit.data.specs.vertical import SimpleVertical

        d = GribVerticalBuilder._build_dict(handle)
        spec = SimpleVertical.from_dict(d)
        spec._set_private_data("handle", handle)
        return spec

    @staticmethod
    def _build_dict(handle):
        def _get(key, default=None):
            return handle.get(key, default=default)

        level = _get("level")
        if level is None:
            level = _get("topLevel")

        level_type = _get("typeOfLevel")

        t = GRIB_LEVEL_TYPES.get(level_type)
        if t is not None:
            level = t.convert(level)
            level_type = t.type

        return dict(
            level=level,
            level_type=level_type,
        )


class GribVerticalContextCollector(GribContextCollector):
    @staticmethod
    def collect_keys(spec, context):
        level_type = None
        for k, v in GRIB_LEVEL_TYPES.items():
            if v.type.name == spec.level_type:
                level_type = k
                break

        if level_type is None:
            raise ValueError(f"Unknown level type: {spec.level_type.name}")

        r = {
            "level": spec.level,
            "typeOfLevel": level_type,
        }

        context.update(r)
