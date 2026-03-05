# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from . import SimpleData


class StreamFieldListData(SimpleData):
    _TYPE_NAME = "Stream"

    def __init__(self, reader):
        self._reader = reader

    @property
    def available_types(self):
        return [self._FIELDLIST]

    def describe(self):
        return f"Stream data from {self._reader.path}"

    def to_fieldlist(self, *args, read_all=False, **kwargs):
        print("Stream", self._reader)
        if read_all:
            from earthkit.data.indexing.simple import SimpleFieldList

            fields = [f for f in self._reader]
            r = SimpleFieldList(fields)
            return r

        return self._reader
