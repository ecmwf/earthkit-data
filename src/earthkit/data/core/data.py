# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import typing

from .fieldlist import FieldList


class Data:
    def __init__(self, data):
        self._data = data

    def describe(self):
        """Return a description of the data"""
        r = ""
        if self.is_listable():
            r += "\n- listable (use ls() to list contents)"
        if self.is_slicable():
            r += "\n- slicable (use [ ] to slice)"
        if self.is_iterable():
            r += "\n- iterable (use for ... in ... to iterate)"
        if self.is_selectable():
            r += "\n- selectable (use sel() to select)"
        if self.is_sortable():
            r += "\n- sortable (use order_by() to sort)"
        if self.is_streamable():
            r += "- streamable (use stream() to stream)"

        if True:
            r += "\n\nCan be converted to: \n"
            r += "  - fieldlist"
            r += "\n  - xarray dataset"
            r += "\n  - pandas dataframe"
            r += "\n  - numpy array"
            r += "\n  - array (other than numpy)"
        return r

    def is_slicable(self):
        """Return True if the data is slicable (i.e. a field or dataset)"""

        from earthkit.data.core.index import Index

        if isinstance(self._data, (Index, FieldList)):
            return True
        return False

    def is_listable(self):
        from earthkit.data.core.fieldlist import FieldList

        """Return True if the data is listable (i.e. a list or tuple)"""

        if isinstance(self._data, FieldList):
            return True
        elif hasattr(self._data, "ls"):
            return True
        return False

    def is_iterable(self):
        """Return True if the data is iterable (i.e. a list or tuple)"""

        from earthkit.data.core.fieldlist import FieldList

        """Return True if the data is listable (i.e. a list or tuple)"""

        if isinstance(self._data, FieldList):
            return True
        return False

    def is_selectable(self):
        """Return True if the data is selectable (i.e. a field or dataset)"""

        from earthkit.data.core.index import Index

        if isinstance(self._data, Index):
            return True
        elif hasattr(self._data, "sel"):
            return True
        return False

    def is_sortable(self):
        """Return True if the data is selectable (i.e. a field or dataset)"""

        from earthkit.data.core.index import Index

        if isinstance(self._data, Index):
            return True
        elif hasattr(self._data, "order_by"):
            return True
        return False

    def is_streamable(self):
        """Return True if the data is streamable (i.e. a field or dataset)"""

        from earthkit.data.core.index import Index

        if isinstance(self._data, Index):
            return True
        elif hasattr(self._data, "stream"):
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

    def to_numpy(self, **kwargs):
        """Convert into a numpy array"""
        self._not_implemented()

    def to_array(self, **kwargs):
        """Convert into an array (numpy or xarray)"""
        self._not_implemented()

    def ls(self, **kwargs):
        """List the contents of the data"""
        if self.is_listable():
            return self._data.ls(**kwargs)
        return None

    def head(self, **kwargs):
        """List the contents of the data"""
        if self.is_listable():
            return self._data.head(**kwargs)
        return None

    def tail(self, **kwargs):
        """List the contents of the data"""
        if self.is_listable():
            return self._data.tail(**kwargs)
        return None

    def __iter__(self):
        """Iterate over the contents of the data"""
        if self.is_iterable():
            return iter(self._data)
        return iter([])

    def __getitem__(self, key):
        """Slice the data"""
        if self.is_slicable():
            return self._data[key]
        return None
