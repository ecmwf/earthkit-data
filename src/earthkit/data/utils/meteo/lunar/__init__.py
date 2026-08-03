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

_EKM_MODULE_NAME = "lunar"
_METHOD_NAMES = ["distance_to_moon", "delta_distance_to_moon", "distance_from_earth_centre_to_moon"]
_EKD_MODULE = importlib.import_module("earthkit.data.utils.meteo.lunar.local")

for method in _register(_EKM_MODULE_NAME, _EKD_MODULE, _METHOD_NAMES):
    globals()[method.__name__] = method
