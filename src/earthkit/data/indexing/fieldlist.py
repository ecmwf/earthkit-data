# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.core.fieldlist import FieldList


class FieldArray(FieldList):
    def __init__(self, fields=None):
        self.fields = fields if fields is not None else []

    def append(self, field):
        self.fields.append(field)

    def _getitem(self, n):
        return self.fields[n]

    def __len__(self):
        return len(self.fields)

    def __repr__(self) -> str:
        return f"FieldArray({len(self.fields)})"
