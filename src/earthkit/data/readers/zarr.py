# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .. import from_object
from . import Reader


class ZarrReader(Reader):
    """"""

    def __init__(self, source, path, **kwargs):
        super().__init__(source, path, **kwargs)
        self._path = path
        self._kwargs = kwargs

    def mutate_source(self):
        import xarray as xr

        ds = xr.open_zarr(self._path, **self._kwargs)
        return from_object(ds)


def reader(source, path, *, magic=None, **kwargs):
    return None
