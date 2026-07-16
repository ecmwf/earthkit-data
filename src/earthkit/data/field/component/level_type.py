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
        units: Union[str, Units, None],
        layer: bool,
        positive: str | None = None,
        level: str | None = None,
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
        units : str | Units | None
            The units of the level type.
        layer : bool
            Whether the level type represents a layer or a single level.
        positive : str | None
            The positive direction of the level type. Can be either "up" or "down".
        level : str, optional
            Define how the level is formed. Can be "top", "bottom" or `None`. Default is `None`.
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

        _cf = {}
        if self.standard_name:
            _cf["standard_name"] = self.standard_name
        if self.long_name:
            _cf["long_name"] = self.long_name

        if units is None or str(units) in ("", "dimensionless", "1"):
            _cf["units"] = "1"
        else:
            _cf["units"] = str(units)

        if self.positive:
            _cf["positive"] = self.positive
        self.cf = _cf

        if layer and level not in (TOP_LEVEL, BOTTOM_LEVEL):
            raise ValueError(
                f"Invalid level value for layer type {name}: {level}. Must be one of: {TOP_LEVEL}, {BOTTOM_LEVEL}."
            )

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


# units `None` parse to dimensionless in pint and maps to "1" in CF
_defs = {
    "ABSTRACT_SINGLE_LEVEL": {
        "name": "abstract_single_level",
        "abbreviation": "abstractSingleLevel",
        "standard_name": None,  # "abstract_single_level",  # is not a CF standard name
        "long_name": "abstract single level",
        "units": None,
        "layer": False,
    },
    "CLOUD_BASE": {
        "name": "cloud_base",
        "abbreviation": "cloudBase",
        "standard_name": None,  # "cloud_base",  # is not a CF standard name
        "long_name": "cloud base",
        "units": None,
        "layer": False,
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
        "level": BOTTOM_LEVEL,
        "positive": POSITIVE_DOWN,
    },
    "ENTIRE_ATMOSPHERE": {
        "name": "entire_atmosphere",
        "abbreviation": "entire_atmosphere",
        "standard_name": None,  # "entire_atmosphere",  # is not a CF standard name
        "long_name": "entire atmosphere",
        "units": None,
        "layer": False,
    },
    "ENTIRE_LAKE": {
        "name": "entire_lake",
        "abbreviation": "entireLake",
        "standard_name": None,  # "entire_lake",  # is not a CF standard name
        "long_name": "entire lake",
        "units": None,
        "layer": False,
    },
    "ENTIRE_MELT_POND": {
        "name": "entire_melt_pond",
        "abbreviation": "entireMeltPond",
        "standard_name": None,  # "entire_melt_pond",  # is not a CF standard name
        "long_name": "entire melt pond",
        "units": None,
        "layer": False,
    },
    "GENERAL": {
        "name": "general",
        "abbreviation": "gen",
        "standard_name": None,  # "general",  # is not a CF standard name
        "long_name": "general",
        "units": None,
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
        "standard_name": None,  # "high_cloud_layer",  # is not a CF standard name
        "long_name": "high cloud layer",
        "units": "hPa",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "HYBRID": {
        "name": "hybrid",
        "abbreviation": "ml",
        "standard_name": "atmosphere_hybrid_sigma_pressure_coordinate",
        "long_name": "hybrid level",
        "units": None,
        "layer": False,
        "positive": POSITIVE_DOWN,
        "parametric": True,
        "coefficient_names": ("A", "B"),
    },
    "ICE_LAYER_ON_WATER": {
        "name": "ice_layer_on_water",
        "abbreviation": "iceLayerOnWater",
        "standard_name": None,  # "ice_layer_on_water",  # is not a CF standard name
        "long_name": "ice layer on water",
        "units": None,
        "layer": False,
    },
    "ICE_TOP_ON_WATER": {
        "name": "ice_top_on_water",
        "abbreviation": "iceTopOnWater",
        "standard_name": None,  # "ice_top_on_water",  # is not a CF standard name
        "long_name": "ice top on water",
        "units": None,
        "layer": False,
    },
    "LAKE_BOTTOM": {
        "name": "lake_bottom",
        "abbreviation": "lakeBottom",
        "standard_name": None,  # "lake_bottom",  # is not a CF standard name
        "long_name": "lake bottom",
        "units": None,
        "layer": False,
    },
    "LOW_CLOUD_LAYER": {
        "name": "low_cloud_layer",
        "abbreviation": "lowCloudLayer",
        "standard_name": None,  # "low_cloud_layer",  # is not a CF standard name
        "long_name": "low cloud layer",
        "units": "hPa",
        "layer": False,
        "positive": POSITIVE_DOWN,
        "level": BOTTOM_LEVEL,
    },
    "MEAN_SEA": {
        "name": "mean_sea",
        "abbreviation": "mean_sea",
        "standard_name": None,  # "mean_sea",  # is not a CF standard name
        "long_name": "mean sea level",
        "units": None,
        "layer": False,
    },
    "MEDIUM_CLOUD_LAYER": {
        "name": "medium_cloud_layer",
        "abbreviation": "mediumCloudLayer",
        "standard_name": None,  # "medium_cloud_layer",  # is not a CF standard name
        "long_name": "medium cloud layer",
        "units": "hPa",
        "layer": True,
        "level": BOTTOM_LEVEL,
        "positive": POSITIVE_DOWN,
    },
    "MIXED_LAYER_DEPTH_BY_DENSITY": {
        # TODO: this seems to be a parametric level type, with density [kg m-3] as a parameter;
        #  it is defined by the fixed surface type #169:
        #  https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_doc/grib2_table4-5.shtml
        "name": "mixed_layer_depth_by_density",
        "abbreviation": "mixedLayerDepthByDensity",
        "standard_name": None,  # "mixed_layer_depth_by_density",  # is not a CF standard name
        "long_name": "mixed layer depth by density",
        "units": "kg m-3",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "MIXED_LAYER_PARCEL": {
        "name": "mixed_layer_parcel",
        "abbreviation": "mixedLayerParcel",
        "standard_name": None,  # "mixed_layer_parcel",  # is not a CF standard name
        "long_name": "mixed layer parcel",
        "units": "Pa",
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "MIXING_LAYER": {
        "name": "mixing_layer",
        "abbreviation": "mixingLayer",
        "standard_name": "mixing_layer",
        "long_name": "mixing layer",
        "units": None,
        "layer": False,
    },
    "MOST_UNSTABLE_PARCEL": {
        "name": "most_unstable_parcel",
        "abbreviation": "mostUnstableParcel",
        "standard_name": None,  # "most_unstable_parcel",  # is not a CF standard name
        "long_name": "most unstable parcel",
        "units": None,
        "layer": False,
    },
    "NOMINAL_TOP_OF_ATMOSPHERE": {
        "name": "nominal_top_of_atmosphere",
        "abbreviation": "nominalTopOfAtmosphere",
        "standard_name": None,  # "nominal_top_of_atmosphere",  # is not a CF standard name
        "long_name": "nominal top of atmosphere",
        "units": None,
        "layer": False,
    },
    "OCEAN_MODEL": {
        "name": "ocean_model",
        "abbreviation": "oceanModel",
        "standard_name": None,  # "ocean_model",  # is not a CF standard name
        "long_name": "ocean model",
        "units": None,
        "layer": False,
        "positive": POSITIVE_DOWN,
    },
    "OCEAN_MODEL_LAYER": {
        "name": "ocean_model_layer",
        "abbreviation": "oceanModelLayer",
        "standard_name": None,  # "ocean_model_layer",  # is not a CF standard name
        "long_name": "ocean model layer",
        "units": None,
        "layer": True,
        "level": BOTTOM_LEVEL,
        "positive": POSITIVE_DOWN,
    },
    "OCEAN_SURFACE": {
        "name": "ocean_surface",
        "abbreviation": "ocean_surface",
        "standard_name": None,  # "ocean_surface",  # is not a CF standard name
        "long_name": "ocean surface",
        "units": None,
        "layer": False,
    },
    "OCEAN_SURFACE_TO_BOTTOM": {
        "name": "ocean_surface_to_bottom",
        "abbreviation": "oceanSurfaceToBottom",
        "standard_name": None,  # "ocean_surface_to_bottom",  # is not a CF standard name
        "long_name": "ocean surface to bottom",
        "units": None,
        "layer": False,
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
        "units": "nK m2 kg-1 s-1",
        "layer": False,
        # "positive": POSITIVE_DOWN,
    },
    "SEA_ICE_LAYER": {
        # cf. level type #152 in https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_table4-5.shtml
        "name": "sea_ice_layer",
        "abbreviation": "seaIceLayer",
        "standard_name": None,  # "sea_ice_layer",  # is not a CF standard name
        "long_name": "sea ice layer",
        "units": None,
        "layer": True,
        "level": BOTTOM_LEVEL,
        "positive": POSITIVE_DOWN,
    },
    "SNOW": {
        "name": "snow",
        "abbreviation": "snow",
        "standard_name": None,  # "unknown",
        "long_name": "snow layer",
        "units": None,
        "layer": True,
        "level": BOTTOM_LEVEL,
        "positive": POSITIVE_DOWN,
    },
    "SNOW_LAYER_OVER_ICE_ON_WATER": {
        "name": "snow_layer_over_ice_on_water",
        "abbreviation": "snowLayerOverIceOnWater",
        "standard_name": None,  # "snow_layer_over_ice_on_water",  # is not a CF standard name
        "long_name": "snow layer over ice on water",
        "units": None,
        "layer": False,
    },
    "SOIL_LAYER": {
        # cf. level type #151 in https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_table4-5.shtml
        "name": "soil_layer",
        "abbreviation": "soilLayer",
        "standard_name": None,  # "soil_layer",  # is not a CF standard name
        "long_name": "soil layer",
        "units": None,
        "layer": True,
        "level": BOTTOM_LEVEL,
        "positive": POSITIVE_DOWN,
    },
    "STRATOSPHERE": {
        "name": "stratosphere",
        "abbreviation": "stratosphere",
        "standard_name": None,  # "stratosphere",  # is not a CF standard name
        "long_name": "stratosphere",
        "units": None,
        "layer": False,
    },
    "SURFACE": {
        "name": "surface",
        "abbreviation": "sfc",
        "standard_name": "surface",
        "long_name": "surface",
        "units": None,
        "layer": False,
    },
    "TEMPERATURE": {
        "name": "temperature",
        "abbreviation": "isothermal",
        "standard_name": "air_temperature",
        "long_name": "temperature",
        "units": "K",
        "layer": False,
    },
    "THETA": {
        "name": "potential_temperature",
        "abbreviation": "pt",
        "standard_name": "air_potential_temperature",
        "long_name": "air_potential temperature",
        "units": "K",
        "layer": False,
        # "positive": POSITIVE_UP,
    },
    "TROPOSPHERE": {
        "name": "troposphere",
        "abbreviation": "troposphere",
        "standard_name": None,  # "troposphere",  # is not a CF standard name
        "long_name": "troposphere",
        "units": None,
        "layer": False,
    },
    "TROPOPAUSE": {
        "name": "tropopause",
        "abbreviation": "tropopause",
        "standard_name": None,  # "tropopause",  # is not a CF standard name
        "long_name": "tropopause",
        "units": None,
        "layer": False,
    },
    "UNKNOWN": {
        "name": "unknown",
        "abbreviation": "unknown",
        "standard_name": None,  # "unknown",
        "long_name": "unknown",
        "units": None,
        "layer": False,
    },
    "WATER_SURFACE_TO_ISOTHERMAL_OCEAN_LAYER": {
        # defined by two level types: #20 [m] and #160 [K]
        # cf. https://www.nco.ncep.noaa.gov/pmb/docs/grib2/grib2_table4-5.shtml
        "name": "water_surface_to_isothermal_ocean_layer",
        "abbreviation": "waterSurfaceToIsothermalOceanLayer",
        "standard_name": None,  # "water_surface_to_isothermal_ocean_layer",  # is not a CF standard name
        "long_name": "water surface to isothermal ocean layer",
        "units": None,
        "layer": False,
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
        units=metadata.get("units", None),
        layer=metadata.get("layer", False),
        positive=metadata.get("positive", None),
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
