# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.specs.data import SimpleData


class GribData(SimpleData):
    def __init__(self, handle):
        self._handle = handle

    def get_values(self, dtype=None):
        """Get the values stored in the field as an array."""
        return self._handle.get_values(dtype=dtype)
