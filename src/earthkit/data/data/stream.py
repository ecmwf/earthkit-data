# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .source import SourceData


class StreamIteratorData(SourceData):
    _TYPE_NAME = "StreamIterator"

    def __init__(self, source_or_reader, data_type=None):
        super().__init__(source_or_reader)
        self._data_type = data_type

    def is_stream(self):
        return True

    @property
    def available_types(self):
        return ["value"]

    def describe(self):
        return f"Stream data from {self._reader.path}"

    def to_iterator(self):
        return self._reader


class StreamFieldListData(SourceData):
    _TYPE_NAME = "StreamFieldList"

    def is_stream(self):
        return True

    @property
    def available_types(self):
        return [self._FIELDLIST]

    def describe(self):
        return f"Stream data from {self._reader.path}"

    def to_fieldlist(self, *args, read_all=False, **kwargs):
        if read_all:
            from earthkit.data.indexing.simple import SimpleFieldList

            fields = [f for f in self._reader]
            r = SimpleFieldList(fields)
            return r

        return self._reader
