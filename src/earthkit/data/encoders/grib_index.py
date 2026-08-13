# (C) Copyright 2023 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from . import EncodedData, Encoder

LOG = logging.getLogger(__name__)


class GribIndexEncodedData(EncodedData):
    def __init__(self, grib_index):
        self.grib_index = grib_index

    def to_bytes(self):
        return None

    def to_file(self, f):
        return None

    def get(self, key, default=None):
        raise NotImplementedError


class GribIndexEncoder(Encoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        **kwargs,
    ):
        if isinstance(data, str):
            data_path = data
            return self._encode_path(data_path, **kwargs)
        elif hasattr(data, "_encode"):
            return data._encode(self, **kwargs)

    def _encode(
        self,
        data=None,
        values=None,
        check_nans=False,
        metadata={},
        template=None,
        missing_value=9999,
        target=None,
        **kwargs,
    ):
        pass

    def _encode_field(self, field, *, target=None, **kwargs):
        raise NotImplementedError("GribIndexEncoder does not support encoding individual fields.")

    def _encode_fieldlist(self, data, *, target=None, **kwargs):
        from earthkit.data.readers.grib.index import GribIndex

        grib_index = GribIndex.from_fieldlist(data, **kwargs)
        return GribIndexEncodedData(grib_index)

    def _encode_xarray(self, data, *, target=None, **kwargs):
        raise NotImplementedError

    def _encode_featurelist(self, data, *, target=None, **kwargs):
        raise NotImplementedError

    def _encode_path(self, path_info, *, target=None, **kwargs):
        from earthkit.data.readers.grib.index import GribIndex

        if path_info is not None and path_info.path is not None:
            grib_index = GribIndex.from_path(path_info.path, **kwargs)
            return GribIndexEncodedData(grib_index)

        raise ValueError("Invalid path_info for GribIndex encoding.")


encoder = GribIndexEncoder
