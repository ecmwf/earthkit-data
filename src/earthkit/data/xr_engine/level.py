# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

GRIB_LEVEL_TYPES = [
    "depthBelowMeanSea",
    "depthBelowSurface",
    "entireAtmosphere",
    "generalVerticalLayer",
    "heightAboveGround",
    "hybrid",
    "iceLayerOnWater",
    "isobaricInhPa",
    "isobaricInPa",
    "isobaricLayer",
    "isothermal",
    "meanSea",
    "mixedLayerDepthByDensity",
    "oceanSurface",
    "potentialVorticity",
    "snowLayer",
    "surface",
    "theta",
]

MARS_LEVEL_TYPES = ["pl", "ml", "sfc", "pt", "pv", "sol"]

KNOWN_LEVEL_TYPE_NAMES = GRIB_LEVEL_TYPES + MARS_LEVEL_TYPES


def is_level_type(name):
    if name in KNOWN_LEVEL_TYPE_NAMES:
        return True
    else:
        from earthkit.data.field.component.level_type import _LEVEL_TYPES

        return name in _LEVEL_TYPES

    return False
