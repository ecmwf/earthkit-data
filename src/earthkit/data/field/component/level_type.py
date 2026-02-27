# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from enum import Enum

from earthkit.data.utils.units import Units

POSITIVE_UP = "up"
POSITIVE_DOWN = "down"


class LevelType:
    def __init__(
        self,
        name: str,
        abbreviation: str,
        standard_name: str,
        long_name: str,
        units: str,
        layer: bool,
        positive: str,
    ) -> None:
        self.name = name
        self.abbreviation = abbreviation
        self.standard_name = standard_name
        self.long_name = long_name
        self.units = Units.from_any(units)
        self.layer = layer
        self.positive = positive
        self.cf = {
            "standard_name": self.standard_name,
            "long_name": self.long_name,
        }

    def __eq__(self, other):
        if isinstance(other, LevelType):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other
        return False


_defs = {
    "PRESSURE": {
        "name": "pressure",
        "abbreviation": "pl",
        "standard_name": "air_pressure",
        "long_name": "pressure",
        "units": "hPa",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    # "PRESSURE_LAYER": {
    #     "name": "p_layer",
    #     "standard_name": "air_pressure",
    #     "long_name": "pressure",
    #     "units": "hPa",
    #     "layer": True,
    #     "positive": POSITIVE_DOWN,
    # },
    "MODEL": {
        "name": "hybrid",
        "abbreviation": "ml",
        "standard_name": "atmosphere_hybrid_sigma_pressure_coordinate",
        "long_name": "hybrid level",
        "units": "1",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "THETA": {
        "name": "potential_temperature",
        "abbreviation": "pt",
        "standard_name": "air_potential_temperature",
        "long_name": "air_potential temperature",
        "units": "K",
        "layer": False,
        "positive": POSITIVE_UP,
    },
    "PV": {
        "name": "potential_vorticity",
        "abbreviation": "pv",
        "standard_name": "ertel_potential_vorticity",
        "long_name": "potential vorticity",
        "units": "10E-9 K m2 kg-1 s-1",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "HEIGHT_ASL": {
        "name": "height_above_sea_level",
        "abbreviation": "h_asl",
        "standard_name": "height_above_sea_level",
        "long_name": "height above mean sea level",
        "units": "m",
        "layer": False,
        "positive": POSITIVE_UP,
    },
    "HEIGHT_AGL": {
        "name": "height_above_ground_level",
        "abbreviation": "h_agl",
        "standard_name": "height",
        "long_name": "height above the surface",
        "units": "m",
        "layer": False,
        "positive": POSITIVE_UP,
    },
    "SURFACE": {
        "name": "surface",
        "abbreviation": "sfc",
        "standard_name": "surface",
        "long_name": "surface",
        "units": "",
        "layer": False,
        "positive": "",
    },
    "DEPTH_BGL": {
        "name": "depth_below_ground_level",
        "abbreviation": "d_bgl",
        "standard_name": "depth",
        "long_name": "soil depth",
        "units": "m",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    # "DEPTH_BGL_LAYER": {
    #     "name": "d_bgl_layer",
    #     "standard_name": "depth",
    #     "long_name": "soil depth",
    #     "units": "m",
    #     "layer": True,
    #     "positive": POSITIVE_DOWN,
    # },
    "GENERAL": {
        "name": "general",
        "abbreviation": "gen",
        "standard_name": "general",
        "long_name": "general",
        "units": "1",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "MEAN_SEA": {
        "name": "mean_sea",
        "abbreviation": "mean_sea",
        "standard_name": "mean_sea",
        "long_name": "mean sea level",
        "units": "",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "SNOW": {
        "name": "snow",
        "abbreviation": "snow",
        "standard_name": "unknown",
        "long_name": "snow layer",
        "units": "1",
        "layer": True,
        "positive": POSITIVE_DOWN,
    },
    "UNKNOWN": {
        "name": "unknown",
        "abbreviation": "unknown",
        "standard_name": "unknown",
        "long_name": "unknown",
        "units": "",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "ENTIRE_ATMOSPHERE": {
        "name": "entire_atmosphere",
        "abbreviation": "entire_atmosphere",
        "standard_name": "entire_atmosphere",
        "long_name": "entire atmosphere",
        "units": "",
        "layer": False,
        "positive": "",
    },
}

LevelTypes = Enum("LevelTypes", [(k, LevelType(**v)) for k, v in _defs.items()])

_LEVEL_TYPES = {t.value.name: t.value for t in LevelTypes}


def get_level_type(item: str, default=LevelTypes.UNKNOWN) -> LevelType:
    if isinstance(item, LevelTypes):
        return item.value
    elif isinstance(item, LevelType):
        if item.name in _LEVEL_TYPES:
            return item
    elif isinstance(item, str):
        if item in _LEVEL_TYPES:
            return _LEVEL_TYPES[item]
    elif item is None:
        return default.value

    raise ValueError(f"Unsupported level type: {item}")
