# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import typing


class Data:
    def __init__(self, data):
        self._data = data

    def describe(self):
        """Return a description of the data"""
        r = ""
        if self.is_listable():
            r += "- listable (use ls() to list contents)"

        if True:
            r += "\n\nCan be converted to: \n"
            r += "  - fieldlist"

        return r

    def is_listable(self):
        from earthkit.data.core.fieldlist import FieldList

        """Return True if the data is listable (i.e. a list or tuple)"""

        if isinstance(self._data, FieldList):
            return True
        return False

    def to_fieldlist(self, **kwargs) -> typing.Any:
        from earthkit.data.core.fieldlist import FieldList

        if isinstance(self._data, FieldList):
            return self._data
        else:
            return self._data.to_fieldlist(**kwargs)

    def to_xarray(self, **kwargs):
        """Convert into an xarray dataset"""
        self._not_implemented()

    def to_pandas(self, **kwargs):
        """Convert into a pandas dataframe"""
        self._not_implemented()

    def ls(self, **kwargs):
        """List the contents of the data"""
        if self.is_listable():
            return self._data.ls(**kwargs)
        return None
