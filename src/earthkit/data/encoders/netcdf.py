# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from . import Encoder

LOG = logging.getLogger(__name__)


class NetCDFAdaptor:
    def __init__(self, ds):
        self.ds = ds

    def to_bytes(self, data):
        return self.ds.to_netcdf(None)

    def to_file(self, f):
        self.ds.to_netcdf(f)

    # def write(self, f):
    #     self.ds.to_netcdf(f)


class NetCDFEncoder(Encoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        values=None,
        min=None,
        max=None,
        check_nans=False,
        metadata={},
        template=None,
        # return_bytes=False,
        missing_value=9999,
        **kwargs,
    ):
        from earthkit.data.wrappers import get_wrapper

        if data is not None:
            data = get_wrapper(data)

        return NetCDFAdaptor(data.to_xarray())

    # def _from_grib(self, data, **kwargs):
    #     return data.to_xarray()


Encoder = NetCDFEncoder
