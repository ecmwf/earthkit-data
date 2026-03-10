# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .. import Reader


class ZarrReaderBase(Reader):
    _format = None
    _binary = True
    _appendable = False

    def _open_zarr(self, **kwargs):
        import xarray as xr

        options = kwargs.get("xarray_open_zarr_kwargs", kwargs)
        return xr.open_zarr(self.path, **options)
