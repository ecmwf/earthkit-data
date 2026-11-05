# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


class GribEncoderContext(dict):
    """A dictionary of context values gathered when a field is encoded to GRIB."""

    _MODE = "encoder"


class GribIndexerContext(dict):
    """A dictionary of context values gathered when a GRIB file is indexed."""

    _MODE = "indexer"
