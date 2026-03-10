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
from . import FilePathEncodedData

LOG = logging.getLogger(__name__)


class CSVEncodedData(EncodedData):
    def __init__(self, df):
        self.df = df

    def to_bytes(self):
        raise NotImplementedError

    def to_file(self, f, **kwargs):
        self.df.to_csv(f, **kwargs)

    def get(self, key, default=None):
        raise NotImplementedError


class CSVEncoder(Encoder):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        target=None,
        **kwargs,
    ):
        if data is not None:
            from earthkit.data.data.wrappers import from_object

            data = from_object(data)
            return data._encode(self, **kwargs)
        else:
            raise ValueError("No data to encode")

    def _encode(self, data, **kwargs):
        assert data is not None
        return CSVEncodedData(data.to_pandas())

    def _encode_field(self, field, **kwargs):
        return self._encode(field, **kwargs)

    def _encode_fieldlist(self, data, *, target=None, **kwargs):
        raise NotImplementedError

    def _encode_xarray(self, data, *, target=None, **kwargs):
        raise NotImplementedError

    def _encode_featurelist(self, data, *, target=None, **kwargs):
        raise NotImplementedError

    def _encode_path(self, path_info, target=None, **kwargs):
        # Write file as is if target is file and path is provided.
        if (
            path_info is not None
            and path_info.path is not None
            and path_info.default_encoder == "csv"
            and target is not None
            and target._name == "file"
        ):
            return FilePathEncodedData(path_info.path, binary=path_info.binary)
        else:
            return None


encoder = CSVEncoder
