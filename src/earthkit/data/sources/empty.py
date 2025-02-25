# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.core.fieldlist import FieldList


class EmptySource(FieldList):
    def ignore(self):
        # Used by multi-source
        return True

    def __getitem__(self, key):
        raise IndexError("Empty source")

    def __len__(self):
        return 0

    def mutate_source(self):
        return self


source = EmptySource
