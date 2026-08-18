# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Meteorological computations shared with earthkit-meteo.

The "forcings" source relies on array-based solar and lunar parameter computations that are
implemented in earthkit-meteo. However, earthkit-meteo cannot be a dependency of earthkit-data
(not even an optional one), so its presence cannot be assumed. To handle this, equivalent
implementations are provided in the local ``solar`` and ``lunar`` subpackages as a fallback.

Each subpackage declares the set of methods it exposes for use within earthkit-data
(``_METHOD_NAMES``) and resolves each of them, one by one, in this order:

1. the matching ``earthkit.meteo.<name>.array`` module, if earthkit-meteo is installed;
2. the local ``local`` module otherwise.

Since resolution happens per method, a method available only locally (i.e. not yet in
earthkit-meteo) is served from the local module on a temporary basis until it can be upstreamed
to earthkit-meteo. The local implementations must stay numerically identical to their
earthkit-meteo counterparts, so that the resolution order is invisible to callers.

Usage::

    from earthkit.data.utils.meteo.solar import cos_solar_zenith_angle

Import the individual methods lazily (inside the function that uses them), as some of them have
optional third-party dependencies that are only needed at call time.
"""

# TODO: Find a better way to handle the situation.
