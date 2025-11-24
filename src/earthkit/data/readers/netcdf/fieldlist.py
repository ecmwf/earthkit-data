# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.decorators import thread_safe_cached_property
from earthkit.data.loaders.xarray.fieldlist import XArrayFieldList

LOG = logging.getLogger(__name__)


class NetCDFFieldList(XArrayFieldList):
    def __init__(self, path, *args, **kwargs):
        self.path = path
        import xarray as xr

        ds = xr.open_dataset(self.path, decode_timedelta=True)

        ds = XArrayFieldList.from_xarray(ds)
        super().__init__(ds.ds, ds.variables)

    # @classmethod
    # def merge(cls, sources):
    #     assert all(isinstance(_, NetCDFFieldList) for _ in sources)
    #     raise NotImplementedError
    #     # return NetCDFMultiFieldList(sources)

    # @classmethod
    # def new_mask_index(cls, *args, **kwargs):
    #     return NotImplementedError
    #     # return NetCDFMaskFieldList(*args, **kwargs)

    def to_xarray(self, **kwargs):
        # if self.path.startswith("http"):
        #     return xr.open_dataset(self.path, **kwargs)
        return type(self).to_xarray_multi_from_paths([self.path], **kwargs)

    def xr_dataset(self):
        import xarray as xr

        return xr.open_dataset(self.path_or_url)

    # def save(self, *args, **kwargs):xw
    #     return self.to_netcdf(*args, **kwargs)

    # def write(self, *args, **kwargs):
    #     return self.to_netcdf(*args, **kwargs)


class NetCDFFieldListFromFileOrURL(NetCDFFieldList):
    def __init__(self, path_or_url, **kwargs):
        assert isinstance(path_or_url, str), path_or_url
        super().__init__(path_or_url, **kwargs)
        self.path_or_url = path_or_url

    @thread_safe_cached_property
    def xr_dataset(self):
        import xarray as xr

        return xr.open_dataset(self.path_or_url)

    # def _getitem(self, n):
    #     if isinstance(n, int):
    #         return self.fields[n]

    # def __len__(self):
    #     return len(self.fields)


class NetCDFFieldListFromFile(NetCDFFieldListFromFileOrURL):
    def __init__(self, path):
        super().__init__(path)

    def __repr__(self):
        return "NetCDFFieldListFromFile(%s)" % (self.path_or_url,)

    def write(self, f, **kwargs):
        import shutil

        with open(self.path, "rb") as s:
            shutil.copyfileobj(s, f, 1024 * 1024)


class NetCDFFieldListFromURL(NetCDFFieldListFromFileOrURL):
    def __init__(self, url):
        super().__init__(url)

    def __repr__(self):
        return "NetCDFFieldListFromURL(%s)" % (self.path_or_url,)
