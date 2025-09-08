# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


POSITIVE_UP = "up"
POSITIVE_DOWN = "down"

LEVEL_TYPES = {}


class LevelType:
    def __init__(
        self, name: str, standard_name: str, long_name: str, units: str, layer: bool, positive: str
    ) -> None:
        self.name = name
        self.standard_name = standard_name
        self.long_name = long_name
        self.units = units
        self.layer = layer
        self.positive = positive

    def __eq__(self, other):
        return self.name == other.name


_defs = {
    "pl": {
        "name": "pl",
        "standard_name": "air_pressure",
        "long_name": "pressure",
        "units": "hPa",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "p_layer": {
        "name": "p_layer",
        "standard_name": "air_pressure",
        "long_name": "pressure",
        "units": "hPa",
        "layer": True,
        "positive": POSITIVE_DOWN,
    },
    "ml": {
        "name": "ml",
        "standard_name": "atmosphere_hybrid_sigma_pressure_coordinate",
        "long_name": "hybrid level",
        "units": "1",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "pt": {
        "name": "pt",
        "standard_name": "air_potential temperature",
        "long_name": "air_potential temperature",
        "units": "K",
        "layer": False,
        "positive": POSITIVE_UP,
    },
    "pv": {
        "name": "pv",
        "standard_name": "ertel_potential vorticity",
        "long_name": "potential vorticity",
        "units": "10-9 K m2 kg-1 s-1",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "h_asl": {
        "name": "h_asl",
        "standard_name": "height_above_sea_level",
        "long_name": "height above mean sea level",
        "units": "m",
        "layer": False,
        "positive": POSITIVE_UP,
    },
    "h_agl": {
        "name": "h_agl",
        "standard_name": "height",
        "long_name": "height above the surface",
        "units": "m",
        "layer": False,
        "positive": POSITIVE_UP,
    },
    "sfc": {
        "name": "sfc",
        "standard_name": "surface",
        "long_name": "surface",
        "units": "",
        "layer": False,
        "positive": "",
    },
    "d_bgl": {
        "name": "d_bgl",
        "standard_name": "depth",
        "long_name": "soil depth",
        "units": "m",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "d_bgl_layer": {
        "name": "d_bgl_layer",
        "standard_name": "depth",
        "long_name": "soil depth",
        "units": "m",
        "layer": True,
        "positive": POSITIVE_DOWN,
    },
    "general": {
        "name": "general",
        "standard_name": "general",
        "long_name": "general",
        "units": "1",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "mean_sea": {
        "name": "mean_sea",
        "standard_name": "mean_sea",
        "long_name": "mean sea level",
        "units": "",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "snow": {
        "name": "snow",
        "standard_name": "unknown",
        "long_name": "snow layer",
        "units": "1",
        "layer": True,
        "positive": POSITIVE_DOWN,
    },
    "unknown": {
        "name": "unknown",
        "standard_name": "unknown",
        "long_name": "unknown",
        "units": "",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
}

for _, v in _defs.items():
    t = LevelType(**v)
    assert t.name not in LEVEL_TYPES, f"Level type {t.name} already defined"
    LEVEL_TYPES[t.name] = t


class LevelTypes:
    PRESSURE = LEVEL_TYPES["pl"]
    PRESSURE_LAYER = LEVEL_TYPES["p_layer"]
    MODEL = LEVEL_TYPES["ml"]
    THETA = LEVEL_TYPES["pt"]
    PV = LEVEL_TYPES["pv"]
    HEIGHT_ASL = LEVEL_TYPES["h_asl"]
    HEIGHT_AGL = LEVEL_TYPES["h_agl"]
    SURFACE = LEVEL_TYPES["sfc"]
    DEPTH_BGL = LEVEL_TYPES["d_bgl"]
    DEPTH_BGL_LAYER = LEVEL_TYPES["d_bgl_layer"]
    GENERAL = LEVEL_TYPES["general"]
    MEAN_SEA = LEVEL_TYPES["mean_sea"]
    SNOW = LEVEL_TYPES["snow"]
    UNKNOWN = LEVEL_TYPES["unknown"]

    @staticmethod
    def get(name_or_object, default=UNKNOWN):
        if isinstance(name_or_object, LevelType):
            if name_or_object in LEVEL_TYPES.values():
                return name_or_object
            else:
                raise ValueError(f"Unsupported level type: {type(name_or_object)}")
        return LEVEL_TYPES.get(name_or_object, default)

    def is_level_type(data):
        return isinstance(data, LevelType)
