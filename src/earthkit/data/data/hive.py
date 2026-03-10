# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .source import SourceData


class HiveFilePatternData(SourceData):
    _TYPE_NAME = "HiveFilePattern"

    @property
    def available_types(self):
        return [self._FIELDLIST]

    def describe(self):
        pass

    def to_fieldlist(self, *args, **kwargs):
        return self._source.to_fieldlist(*args, **kwargs)
