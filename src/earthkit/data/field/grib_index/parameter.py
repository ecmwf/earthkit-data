# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


class IndexParameterBuilder:
    """Builder for creating parameter components from MARS requests.

    This builder extracts parameter metadata from MARS request dictionaries and creates
    the appropriate parameter component subclass using :func:`create_parameter`.
    """

    @staticmethod
    def build(handle):
        from earthkit.data.field.grib.parameter import GribParameterBuilder

        return GribParameterBuilder.build(handle)
