# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os

from earthkit.data.readers.xarray.fieldlist import XArrayFieldList

from . import Reader


class ZarrReader(XArrayFieldList, Reader):

    def __init__(self, source, path, **kwargs):
        Reader.__init__(self, source, path, **kwargs)
        fl = XArrayFieldList.from_xarray(self._open_zarr(**kwargs))
        super().__init__(fl.ds, fl.variables)

    def mutate_source(self):
        return self

    def to_xarray(self, **kwargs):
        return self._open_zarr(**kwargs)

    def _open_zarr(self, **kwargs):
        import xarray as xr

        options = kwargs.get("xarray_open_zarr_kwargs", kwargs)
        return xr.open_zarr(self.path, **options)

    def __repr__(self):
        return f"ZarrReader({self.path})"


def reader(source, path, *, magic=None, deeper_check=False, **kwargs):
    if (
        os.path.exists(os.path.join(path, ".zarray"))
        or os.path.exists(os.path.join(path, ".zgroup"))
        or os.path.exists(os.path.join(path, ".zmetadata"))
        or os.path.exists(os.path.join(path, ".zattrs"))
    ):
        return ZarrReader(source, path)
