# (C) Copyright 2025- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.readers.xarray.fieldlist import XArrayFieldList

from .core import PPReaderBase


class PPFieldList(XArrayFieldList, PPReaderBase):
    def __init__(self, source, path, **kwargs):
        PPReaderBase.__init__(self, source, path)
        ds = self._open_pp(**kwargs)

        fl = XArrayFieldList.from_xarray(ds)
        super().__init__(fl.ds, fl.variables)

    def mutate_source(self):
        return self

    def to_xarray(self, **kwargs):
        return self._open_pp(**kwargs)

    def __repr__(self):
        return f"PPFieldList({self.path})"
