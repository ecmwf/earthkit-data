# (C) Copyright 2021 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

# from earthkit.data.readers.netcdf import NetCDFFieldListUrlReader
from earthkit.data.readers.netcdf import NetCDFReader
from earthkit.data.readers.xarray.fieldlist import XArrayFieldList
from earthkit.data.sources import Source


class OpenDAP(Source):
    def __init__(self, url):
        self.url = url

    def mutate(self):
        import xarray as xr

        ds = xr.open_dataset(self.url, decode_timedelta=True)
        fl = XArrayFieldList.from_xarray(ds)
        if len(fl) > 0:
            return fl
        else:
            return NetCDFReader(OpenDAP, self.url)

        # fs = NetCDFFieldListUrlReader(source, self.url)
        # if len(fs) > 0:
        #     return fs
        # else:
        #     return NetCDFReader(source, self.path)


source = OpenDAP
