# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import importlib

from earthkit.data.utils.meteo.registry import _register

_EKM_MODULE_NAME = "solar"
_METHOD_NAMES = [
    "cos_solar_zenith_angle",
    "solar_declination_angle",
    "julian_day",
    "incoming_solar_radiation",
    "toa_incident_solar_radiation",
]

_EKD_MODULE = importlib.import_module("earthkit.data.utils.meteo.solar.local")

for method in _register(_EKM_MODULE_NAME, _EKD_MODULE, _METHOD_NAMES):
    globals()[method.__name__] = method
