# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from . import EncodedData, Encoder, FilePathEncodedData

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

    def get(self, key, default=None):
        raise NotImplementedError


class NetCDFEncoder(Encoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        target=None,
        **kwargs,
    ):
        if data is not None:
            from earthkit.data.data import Data
            from earthkit.data.data.wrappers import from_object

            path_allowed = target is not None and target._name == "file"
            hints = {"path_allowed": path_allowed}

            data = from_object(data)
            if hasattr(data, "_encode"):
                return data._encode(self, hints=hints, target=target, **kwargs)
            elif isinstance(data, Data):
                return self._call_encode(data, target=target, **kwargs)

        else:
            raise ValueError("No data to encode")

    def _call_encode(self, data, *, target=None, **kwargs):
        types = data.available_types
        for t in types:
            if t == self._XARRAY:
                return self._encode_xarray(data.to_xarray(), target=target, **kwargs)
            elif t == self._FIELDLIST:
                return self._encode_fieldlist(data.to_fieldlist(), target=target, **kwargs)

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
        target=None,
        **kwargs,
    ):
        _kwargs = kwargs.copy()
        if data is not None:
            # TODO: find better way to check if the earthkit engine is used
            if hasattr(data, "_default_encoder") and data._default_encoder() != "netcdf":
                earthkit_to_xarray_kwargs = _kwargs.pop("earthkit_to_xarray_kwargs", {})
                earthkit_to_xarray_kwargs["add_earthkit_attrs"] = False
                _kwargs = earthkit_to_xarray_kwargs
        else:
            _kwargs = {}

        return NetCDFEncodedData(data.to_xarray(**_kwargs))

    def _encode_field(self, field, *, target=None, **kwargs):
        return self._encode(field, target=target, **kwargs)

    def _encode_fieldlist(self, data, *, target=None, **kwargs):
        return self._encode(data, target=target, **kwargs)

    def _encode_xarray(self, data, *, target=None, **kwargs):
        return NetCDFEncodedData(data)

    def _encode_featurelist(self, data, *, target=None, **kwargs):
        raise NotImplementedError

    def _encode_path(self, path_info=None, *, target=None, **kwargs):
        # Write file as is if target is file and path is provided.
        if (
            path_info is not None
            and path_info.path is not None
            and path_info.default_encoder == "betcdf"
            and target is not None
            and target._name == "file"
        ):
            return FilePathEncodedData(path_info.path, binary=path_info.binary)
        else:
            return None


encoder = NetCDFEncoder
