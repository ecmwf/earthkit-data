# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from enum import Enum
from typing import TYPE_CHECKING, Union

from earthkit.utils.units import Units

if TYPE_CHECKING:
    from earthkit.utils.units import Units


POSITIVE_UP = "up"
POSITIVE_DOWN = "down"

TOP_LEVEL = "top"
BOTTOM_LEVEL = "bottom"


class LevelType:
    """Class representing a level type.

    This object is used to represent the type of vertical coordinate of a
    field. It contains metadata about the level type, such as its name,
    abbreviation, standard name, long name, units, whether it represents a layer
    or a single level, and the positive direction of the level type.

    LevelType object are immutable and they are not supposed to be created directly by users.
    Earthkit-data has a list of predefined level types. Additional level types are automatically registered
    as they appear in the data.

    LevelType objects are identified by their name. The predefined level types are:

       - "pressure"
       - "hybrid"
       - "potential_temperature"
       - "potential_vorticity"
       - "height_above_mean_sea_level"
       - "height_above_ground_level"
       - "surface"
       - "depth_below_ground_level"
       - "general"
       - "mean_sea"
       - "snow"
       - "unknown"
       - "entire_atmosphere"
       - "ocean_surface"
       - "temperature"
       - "depth_below_sea_layer"
       - "mixed_layer_depth_by_density"
       - "ice_layer_on_water"

    """

    def __init__(
        self,
        name: str,
        abbreviation: str,
        standard_name: str,
        long_name: str,
        units: Union[str, Units],
        layer: bool,
        positive: str,
        level: str = TOP_LEVEL,
        parametric: bool = False,
        coefficient_names: tuple[str, ...] | None = None,
    ) -> None:
        """Initialise the LevelType object.

        This is not supposed to be called directly by users. Use
        the `get_level_type` function instead.

        Parameters
        ----------
        name : str
            The name of the level type. The name must be one of the predefined level types.
            If the name is not one of the predefined level types, it will be registered a
            a new level type with the provided metadata using the `add_level_type` function.
        abbreviation : str
            The abbreviation of the level type.
        standard_name : str
            The CF standard name of the level type.
        long_name : str
            The CF long name of the level type.
        units : Union[str, Units]
            The units of the level type.
        layer : bool
            Whether the level type represents a layer or a single level.
        positive : str
            The positive direction of the level type. Can be either "up" or "down".
        level : str, optional
            Define how the levels is formed when the level type is a layer. Can be either "top" or "bottom".
            Default is "top".
        parametric : bool, optional
            Whether the level type is parametric. Default is False.
        coefficient_names : tuple[str, ...] | None, optional
            The names of the coefficients for the level type, if parametric is True.
        """
        self.name = name
        self.abbreviation = abbreviation
        self.standard_name = standard_name
        self.long_name = long_name
        self.units = Units.from_any(units)
        self.layer = layer
        self.level = level
        self.positive = positive
        self.parametric = parametric
        self.coefficient_names = coefficient_names
        self.cf = {
            "standard_name": self.standard_name,
            "long_name": self.long_name,
            "units": str(self.units),
            "positive": self.positive,
        }

    def __eq__(self, other) -> bool:
        """Check if this LevelType is equal to another LevelType or a string.

        Two LevelType objects are considered equal if they are the same object or have
        the same name. A LevelType object is considered equal to a string if its name
        is equal to that string.
        """
        if isinstance(other, LevelType):
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other
        if isinstance(other, LevelTypes):
            return self.name == other.value.name
        return False

    def __repr__(self):
        return self.name

    def __hash__(self):
        return hash(self.name)


_defs = {
    "ABSTRACT_SINGLE_LEVEL": {
        "name": "abstract_single_level",
        "abbreviation": "abstractSingleLevel",
        "standard_name": "abstract_single_level",
        "long_name": "abstract single level",
        "units": "",
        "layer": False,
        "positive": "",
    },
    "CLOUD_BASE": {
        "name": "cloud_base",
        "abbreviation": "cloudBase",
        "standard_name": "cloud_base",
        "long_name": "cloud base",
        "units": "",
        "layer": False,
        "positive": "",
    },
    "DEPTH_BL_LAYER": {
        "name": "depth_below_land_layer",
        "abbreviation": "d_bll_layer",
        "standard_name": "depth",
        "long_name": "soil depth",
        "units": "m",
        "layer": True,
        "level": TOP_LEVEL,
        "positive": POSITIVE_DOWN,
    },
    "DEPTH_BL_LEVEL": {
        "name": "depth_below_land_level",
        "abbreviation": "d_bll",
        "standard_name": "depth",
        "long_name": "soil depth",
        "units": "m",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "DEPTH_BS_LAYER": {
        "name": "depth_below_sea_layer",
        "abbreviation": "d_bsl_layer",
        "standard_name": "depth",
        "long_name": "depth",
        "units": "m",
        "layer": True,
        "level": TOP_LEVEL,
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
    "ENTIRE_LAKE": {
        "name": "entire_lake",
        "abbreviation": "entireLake",
        "standard_name": "entire_lake",
        "long_name": "entire lake",
        "units": "",
        "layer": False,
        "positive": "",
    },
    "ENTIRE_MELT_POND": {
        "name": "entire_melt_pond",
        "abbreviation": "entireMeltPond",
        "standard_name": "entire_melt_pond",
        "long_name": "entire melt pond",
        "units": "",
        "layer": False,
        "positive": "",
    },
    "GENERAL": {
        "name": "general",
        "abbreviation": "gen",
        "standard_name": "general",
        "long_name": "general",
        "units": "1",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "HEIGHT_AG_LEVEL": {
        "name": "height_above_ground_level",
        "abbreviation": "h_agl",
        "standard_name": "height",
        "long_name": "height above the surface",
        "units": "m",
        "layer": False,
        "positive": POSITIVE_UP,
    },
    "HEIGHT_AS_LEVEL": {
        "name": "height_above_mean_sea_level",
        "abbreviation": "h_asl",
        "standard_name": "height_above_mean_sea_level",
        "long_name": "height above mean sea level",
        "units": "m",
        "layer": False,
        "positive": POSITIVE_UP,
    },
    "HIGH_CLOUD_LAYER": {
        "name": "high_cloud_layer",
        "abbreviation": "highCloudLayer",
        "standard_name": "high_cloud_layer",
        "long_name": "high cloud layer",
        "units": "hPa",
        "layer": True,
        "level": TOP_LEVEL,
        "positive": "",
    },
    "HYBRID": {
        "name": "hybrid",
        "abbreviation": "ml",
        "standard_name": "atmosphere_hybrid_sigma_pressure_coordinate",
        "long_name": "hybrid level",
        "units": "1",
        "layer": False,
        "positive": POSITIVE_DOWN,
        "parametric": True,
        "coefficient_names": ("A", "B"),
    },
    "ICE_LAYER_ON_WATER": {
        "name": "ice_layer_on_water",
        "abbreviation": "iceLayerOnWater",
        "standard_name": "ice_layer_on_water",
        "long_name": "ice layer on water",
        "units": "1",
        "layer": True,
        "level": TOP_LEVEL,
        "positive": POSITIVE_UP,
    },
    "ICE_TOP_ON_WATER": {
        "name": "ice_top_on_water",
        "abbreviation": "iceTopOnWater",
        "standard_name": "ice_top_on_water",
        "long_name": "ice top on water",
        "units": "1",
        "layer": False,
        "positive": "",
    },
    "LAKE_BOTTOM": {
        "name": "lake_bottom",
        "abbreviation": "lakeBottom",
        "standard_name": "lake_bottom",
        "long_name": "lake bottom",
        "units": "1",
        "layer": False,
        "positive": "",
    },
    "LOW_CLOUD_LAYER": {
        "name": "low_cloud_layer",
        "abbreviation": "lowCloudLayer",
        "standard_name": "low_cloud_layer",
        "long_name": "low cloud layer",
        "units": "hPa",
        "layer": True,
        "level": TOP_LEVEL,
        "positive": "",
    },
    "MEAN_SEA": {
        "name": "mean_sea",
        "abbreviation": "mean_sea",
        "standard_name": "mean_sea",
        "long_name": "mean sea level",
        "units": "",
        "layer": False,
        "positive": "",
    },
    "MEDIUM_CLOUD_LAYER": {
        "name": "medium_cloud_layer",
        "abbreviation": "mediumCloudLayer",
        "standard_name": "medium_cloud_layer",
        "long_name": "medium cloud layer",
        "units": "hPa",
        "layer": True,
        "level": TOP_LEVEL,
        "positive": "",
    },
    "MIXED_LAYER_DEPTH_BY_DENSITY": {
        "name": "mixed_layer_depth_by_density",
        "abbreviation": "mixedLayerDepthByDensity",
        "standard_name": "mixed_layer_depth_by_density",
        "long_name": "mixed layer depth by density",
        "units": "m",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "MIXED_LAYER_PARCEL": {
        "name": "mixed_layer_parcel",
        "abbreviation": "mixedLayerParcel",
        "standard_name": "mixed_layer_parcel",
        "long_name": "mixed layer parcel",
        "units": "Pa",
        "layer": False,
        "positive": "",
    },
    "MIXING_LAYER": {
        "name": "mixing_layer",
        "abbreviation": "mixingLayer",
        "standard_name": "mixing_layer",
        "long_name": "mixing layer",
        "units": "",
        "layer": False,
        "positive": "",
    },
    "MOST_UNSTABLE_PARCEL": {
        "name": "most_unstable_parcel",
        "abbreviation": "mostUnstableParcel",
        "standard_name": "most_unstable_parcel",
        "long_name": "most unstable parcel",
        "units": "",
        "layer": False,
        "positive": "",
    },
    "NOMINAL_TOP_OF_ATMOSPHERE": {
        "name": "nominal_top_of_atmosphere",
        "abbreviation": "nominalTopOfAtmosphere",
        "standard_name": "nominal_top_of_atmosphere",
        "long_name": "nominal top of atmosphere",
        "units": "",
        "layer": False,
        "positive": "",
    },
    "OCEAN_MODEL": {
        "name": "ocean_model",
        "abbreviation": "oceanModel",
        "standard_name": "ocean_model",
        "long_name": "ocean model",
        "units": "1",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "OCEAN_MODEL_LAYER": {
        "name": "ocean_model_layer",
        "abbreviation": "oceanModelLayer",
        "standard_name": "ocean_model_layer",
        "long_name": "ocean model layer",
        "units": "1",
        "layer": True,
        "level": BOTTOM_LEVEL,
        "positive": POSITIVE_DOWN,
    },
    "OCEAN_SURFACE": {
        "name": "ocean_surface",
        "abbreviation": "ocean_surface",
        "standard_name": "ocean_surface",
        "long_name": "ocean surface",
        "units": "",
        "layer": False,
        "positive": "",
    },
    "OCEAN_SURFACE_TO_BOTTOM": {
        "name": "ocean_surface_to_bottom",
        "abbreviation": "oceanSurfaceToBottom",
        "standard_name": "ocean_surface_to_bottom",
        "long_name": "ocean surface to bottom",
        "units": "1",
        "layer": False,
        "positive": "",
    },
    "PRESSURE": {
        "name": "pressure",
        "abbreviation": "pl",
        "standard_name": "air_pressure",
        "long_name": "pressure",
        "units": "hPa",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "PRESSURE_LAYER": {
        "name": "pressure_layer",
        "abbreviation": "p_layer",
        "standard_name": "air_pressure",
        "long_name": "pressure",
        "units": "hPa",
        "layer": True,
        "level": TOP_LEVEL,
        "positive": POSITIVE_DOWN,
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
    "SEA_ICE_LAYER": {
        "name": "sea_ice_layer",
        "abbreviation": "seaIceLayer",
        "standard_name": "sea_ice_layer",
        "long_name": "sea ice layer",
        "units": "1",
        "layer": True,
        "level": BOTTOM_LEVEL,
        "positive": POSITIVE_DOWN,
    },
    "SNOW": {
        "name": "snow",
        "abbreviation": "snow",
        "standard_name": "unknown",
        "long_name": "snow layer",
        "units": "1",
        "layer": True,
        "level": BOTTOM_LEVEL,
        "positive": POSITIVE_DOWN,
    },
    "SNOW_LAYER_OVER_ICE_ON_WATER": {
        "name": "snow_layer_over_ice_on_water",
        "abbreviation": "snowLayerOverIceOnWater",
        "standard_name": "snow_layer_over_ice_on_water",
        "long_name": "snow layer over ice on water",
        "units": "1",
        "layer": False,
        "positive": "",
    },
    "SOIL_LAYER": {
        "name": "soil_layer",
        "abbreviation": "soilLayer",
        "standard_name": "soil_layer",
        "long_name": "soil layer",
        "units": "1",
        "layer": True,
        "level": BOTTOM_LEVEL,
        "positive": POSITIVE_DOWN,
    },
    "STRATOSPHERE": {
        "name": "stratosphere",
        "abbreviation": "stratosphere",
        "standard_name": "stratosphere",
        "long_name": "stratosphere",
        "units": "1",
        "layer": False,
        "positive": "",
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
    "TEMPERATURE": {
        "name": "temperature",
        "abbreviation": "isothermal",
        "standard_name": "temperature",
        "long_name": "temperature",
        "units": "K",
        "layer": False,
        "positive": "",
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
    "TROPOSPHERE": {
        "name": "troposphere",
        "abbreviation": "troposphere",
        "standard_name": "troposphere",
        "long_name": "troposphere",
        "units": "1",
        "layer": False,
        "positive": "",
    },
    "TROPOPAUSE": {
        "name": "tropopause",
        "abbreviation": "tropopause",
        "standard_name": "tropopause",
        "long_name": "tropopause",
        "units": "",
        "layer": False,
        "positive": "",
    },
    "UNKNOWN": {
        "name": "unknown",
        "abbreviation": "unknown",
        "standard_name": "unknown",
        "long_name": "unknown",
        "units": "",
        "layer": False,
        "positive": "",
    },
    "WATER_SURFACE_TO_ISOTHERMAL_OCEAN_LAYER": {
        "name": "water_surface_to_isothermal_ocean_layer",
        "abbreviation": "waterSurfaceToIsothermalOceanLayer",
        "standard_name": "water_surface_to_isothermal_ocean_layer",
        "long_name": "water surface to isothermal ocean layer",
        "units": "1",
        "layer": False,
        "positive": "",
    },
}

LevelTypes = Enum("LevelTypes", [(k, LevelType(**v)) for k, v in _defs.items()])

_LEVEL_TYPES = {t.value.name: t.value for t in LevelTypes}


# TODO: make it thread safe
def _register_level_type(name: str, metadata: dict | None = None) -> LevelType:
    if name in _LEVEL_TYPES:
        raise ValueError(f"Level type {name} already exists")

    if metadata is None:
        metadata = {}

    level_type = LevelType(
        name=name,
        abbreviation=metadata.get("abbreviation", name),
        standard_name=metadata.get("standard_name", name),
        long_name=metadata.get("long_name", name),
        units=metadata.get("units", ""),
        layer=metadata.get("layer", False),
        positive=metadata.get("positive", ""),
    )

    _LEVEL_TYPES[name] = level_type
    return level_type


def get_level_type(item: str, default=LevelTypes.UNKNOWN, metadata=None) -> LevelType:
    if isinstance(item, LevelTypes):
        return item.value
    elif isinstance(item, LevelType):
        if item.name in _LEVEL_TYPES:
            return item
    elif isinstance(item, str):
        if item in _LEVEL_TYPES:
            return _LEVEL_TYPES[item]
        else:
            return _register_level_type(item, metadata)
    elif item is None:
        return default.value

    raise ValueError(f"Unsupported level type: {item}")
