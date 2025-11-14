# (C) Copyright 2025- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from . import Reader
from .netcdf.fieldlist import XArrayFieldList


class IrisReader(XArrayFieldList, Reader):

    def __init__(self, source, path, **kwargs):
        Reader.__init__(self, source, path)
        XArrayFieldList.__init__(self, self._open_iris(**kwargs))

    def mutate_source(self):
        return self

    def to_xarray(self, **kwargs):
        return self._open_iris(**kwargs)

    def _open_iris(
        self,
        *,
        iris_open_kwargs: dict | None = None,
        iris_save_kwargs: dict | None = None,
        xr_load_kwargs: dict | None = None,
    ):
        import iris
        from ncdata.iris_xarray import cubes_to_xarray

        cubelist = iris.load(self.path, **iris_open_kwargs or {})
        return cubes_to_xarray(cubelist, iris_save_kwargs=iris_save_kwargs, xr_load_kwargs=xr_load_kwargs)

    def __repr__(self):
        return f"IrisReader({self.path})"


def reader(source, path, *, magic=None, deeper_check=False, **kwargs):
    if path.endswith(".pp"):
        return IrisReader(source, path)
