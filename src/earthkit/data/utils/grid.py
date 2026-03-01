# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
import logging

from earthkit.utils.decorators import thread_safe_cached_property

LOG = logging.getLogger(__name__)


class _EckitGridSupport:
    """Support for eckit-based grid handling in ecCodes.

    This class checks for the availability of eckit and its grid support, as well as the
    ecCodes features related to eckit grid support. It is only evaluated once and cached
    for future use.
    """

    @thread_safe_cached_property
    def has_grid(self):
        try:
            from eckit.geo import Grid  # noqa: F401

            return True
        except ImportError:
            pass

        return False

    @thread_safe_cached_property
    def has_ecc_grid_spec(self):
        import os

        if os.environ.get("ECCODES_ECKIT_GEO") == "1":
            import eccodes

            try:
                r = eccodes.codes_get_features(eccodes.CODES_FEATURES_ENABLED)
                if isinstance(r, str) and "ECKIT_GEO" in r:
                    return True
            except Exception as e:
                LOG.warning(f"Failed to get ecCodes features: {e}")
                return False

        return False


ECKIT_GRID_SUPPORT = _EckitGridSupport()
