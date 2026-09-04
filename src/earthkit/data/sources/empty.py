# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.sources import Source


class EmptySource(Source):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def mutate(self):
        return self

    def ignore(self):
        return True

    def to_fieldlist(self, *args, **kwargs):
        from earthkit.data.indexing.empty import EmptyFieldList

        return EmptyFieldList()

    def to_data_object(self):
        from earthkit.data.data.empty import EmptyData

        return EmptyData()


source = EmptySource
