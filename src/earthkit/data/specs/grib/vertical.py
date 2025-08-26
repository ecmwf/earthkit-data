# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.specs.vertical import LEVEL_TYPES
from earthkit.data.specs.vertical import Vertical


class GribLevelType:
    def __init__(self, key, item):
        if not isinstance(item, tuple):
            item = (item, None)

        assert len(item) == 2

        self.key = key
        self.type = LEVEL_TYPES[item[0]]
        self.converter = item[1]

    def convert(self, value):
        if self.converter:
            return self.converter(value)
        return value


GRIB_LEVEL_TYPES = {
    "depthBelowLand": "d_bgl",
    "depthBelowLandLayer": "d_bgl",
    "generalVerticalLayer": "general",
    "heightAboveSea": "h_asl",
    "heightAboveGround": "h_agl",
    "hybrid": "ml",
    "isobaricInhPa": "pl",
    "isobaricInPa": ("pl", lambda x: x / 100.0),
    "isobaricLayer": ("pl", lambda x: x / 100.0),
    "meanSea": "mean_sea",
    "theta": "pt",
    "potentialVorticity": "pv",
    "surface": "sfc",
}

GRIB_LEVEL_TYPES = {k: GribLevelType(k, v) for k, v in GRIB_LEVEL_TYPES.items()}


def from_grib(handle):
    def _get(key, default=None):
        return handle.get(key, default=default)

    level = _get("level")
    level_type = _get("typeOfLevel")

    t = GRIB_LEVEL_TYPES.get(level_type)
    if t is not None:
        level = t.convert(level)
        level_type = t.type

    return dict(
        level=level,
        level_type=level_type,
    )


def to_grib(spec, altered=True):
    if isinstance(spec, Vertical):
        if altered:
            if hasattr(spec, "_handle"):
                return {}

        level_type = None
        for k, v in GRIB_LEVEL_TYPES.items():
            if v.type.name == spec.level_type:
                level_type = k
                break

        if level_type is None:
            raise ValueError(f"Unknown level type: {spec.level_type.name}")

        return {
            "level": spec.level,
            "typeOfLevel": level_type,
        }
    raise TypeError("Expected a Vertical instance.")
