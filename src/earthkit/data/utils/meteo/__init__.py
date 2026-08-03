# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


# NOTE: The "forcings" source relies on array-based solar and lunar parameter computations that are
# implemented in earthkit-meteo. However, earthkit-meteo cannot be a dependency of earthkit-data
# (not even an optional one), so its presence cannot be assumed. To handle this, equivalent
# implementations are provided in the local `solar` and `lunar` submodules as a fallback.
#
# Resolution order:
#   1. Use earthkit-meteo if it is installed.
#   2. Fall back to the local submodule implementation otherwise.
#
# Each local submodule explicitly declares the set of methods it exposes for use within earthkit-data.
# Any method available only in a local submodule (and not yet in earthkit-meteo) will be served from
# there on a temporary basis until it can be upstreamed to earthkit-meteo.
#

# TODO: Find a better way to handle the situation.
