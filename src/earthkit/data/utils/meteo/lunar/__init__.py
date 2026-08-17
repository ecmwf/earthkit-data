# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Lunar computations served from earthkit-meteo or from the local fallback.

See :mod:`earthkit.data.utils.meteo` for details.
"""

from earthkit.data.utils.meteo.registry import _resolve

from . import local as _EKD_MODULE

_EKM_MODULE_NAME = "lunar"
_METHOD_NAMES = [
    "distance_to_moon",
    "delta_distance_to_moon",
    "distance_from_earth_centre_to_moon",
]

globals().update(_resolve(_EKM_MODULE_NAME, _EKD_MODULE, _METHOD_NAMES))

__all__ = list(_METHOD_NAMES)
