# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .source import SourceData


class FieldListData(SourceData):
    _TYPE_NAME = "FieldList"

    @property
    def available_types(self):
        r = [self._FIELDLIST]
        if hasattr(self._source, "to_xarray"):
            r.append(self._XARRAY)
        return r

    def describe(self):
        return f"FieldList data with {len(self._fieldlist)} fields"

    def to_fieldlist(self, *args, **kwargs):
        return self._source

    def to_xarray(self, *args, **kwargs):
        if hasattr(self._source, "to_xarray"):
            return self._source.to_xarray(*args, **kwargs)
        self._conversion_not_implemented()
