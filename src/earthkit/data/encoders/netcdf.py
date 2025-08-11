# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from . import EncodedData
from . import Encoder

LOG = logging.getLogger(__name__)


class NetCDFEncodedData(EncodedData):
    # Prefer file path when writing to netCDF files. The reason is as follows:
    #
    # The Xarray.to_netcdf() documentation states that:
    # ... file-like objects are only supported by the scipy engine.
    # If no path is provided, this function returns the resulting netCDF file as bytes;
    # in this case, we need to use scipy, which does not support netCDF version 4
    # (the default format becomes NETCDF3_64BIT).
    prefer_file_path = True

    def __init__(self, ds):
        self.ds = ds

    def to_bytes(self):
        return self.ds.to_netcdf(None)

    def to_file(self, file):
        if hasattr(self.ds, "earthkit"):
            self.ds.earthkit.to_netcdf(file)

        else:
            self.ds.to_netcdf(file)

    def metadata(self, key):
        raise NotImplementedError


class NetCDFEncoder(Encoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        **kwargs,
    ):
        if data is not None:
            from earthkit.data.wrappers import get_wrapper

            data = get_wrapper(data, fieldlist=False)
            return data._encode(self, **kwargs)
        else:
            raise ValueError("No data to encode")

    def _encode(
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
        _kwargs = kwargs.copy()
        if data is not None:
            # TODO: find better way to check if the earthkit engine is used
            if hasattr(data, "to_xarray_earthkit"):
                earthkit_to_xarray_kwargs = _kwargs.pop("earthkit_to_xarray_kwargs", {})
                earthkit_to_xarray_kwargs["add_earthkit_attrs"] = False
                _kwargs = earthkit_to_xarray_kwargs
        else:
            _kwargs = {}

        return NetCDFEncodedData(data.to_xarray(**_kwargs))

    def _encode_field(self, field, **kwargs):
        return self._encode(field, **kwargs)

    def _encode_fieldlist(self, data, **kwargs):
        return self._encode(data, **kwargs)

    def _encode_xarray(self, data, **kwargs):
        return NetCDFEncodedData(data)


encoder = NetCDFEncoder
