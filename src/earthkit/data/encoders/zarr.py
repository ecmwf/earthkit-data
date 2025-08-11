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


class ZarrEncodedData(EncodedData):
    def __init__(self, ds):
        self.ds = ds

    def to_bytes(self):
        return None

    def to_file(self, f):
        return None

    def to_xarray(self):
        return self.ds

    def metadata(self, key):
        raise NotImplementedError


class ZarrEncoder(Encoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        **kwargs,
    ):
        if data is not None:
            from earthkit.data.wrappers import get_wrapper

            # data = get_wrapper(data, fieldlist=False)
            data = get_wrapper(data)

            if hasattr(data, "_encode"):
                return data._encode(self, **kwargs)
            else:
                return data
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
        return ZarrEncodedData(data.to_xarray(add_earthkit_attrs=False))

    def _encode_field(self, field, **kwargs):
        raise NotImplementedError("ZarrEncoder does not support encoding individual fields.")

    def _encode_fieldlist(self, data, **kwargs):
        earthkit_to_xarray_kwargs = kwargs.pop("earthkit_to_xarray_kwargs", {})
        # earthkit_to_xarray_kwargs.update(kwargs)
        earthkit_to_xarray_kwargs["add_earthkit_attrs"] = False
        kwargs = earthkit_to_xarray_kwargs

        ds = data.to_xarray(**kwargs)
        return ZarrEncodedData(ds)

    def _encode_xarray(self, data, **kwargs):
        raise NotImplementedError


encoder = ZarrEncoder
