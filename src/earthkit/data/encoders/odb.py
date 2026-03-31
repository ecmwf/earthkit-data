# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
#

from . import Encoder, FilePathEncodedData


class ODBEncoder(Encoder):
    """Encode ODB data."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        target=None,
        **kwargs,
    ):
        path_allowed = target is not None and target._name == "file"
        hints = {"path_allowed": path_allowed}

        return data._encode(self, hints=hints, target=target)

    def _encode(self, data, *, target=None, **kwargs):
        return self._encode_path(data, target=target, **kwargs)

    def _encode_featurelist(self, data, *, target=None, **kwargs):
        raise

    def _encode_field(self, data, *, target=None, **kwargs):
        raise NotImplementedError

    def _encode_fieldlist(self, data, *, target=None, **kwargs):
        raise NotImplementedError

    def _encode_xarray(self, data, *, target=None, **kwargs):
        raise NotImplementedError

    def _encode_path(self, path_info, *, target=None, **kwargs):
        # Write file as is if target is file and path is provided.
        if (
            path_info is not None
            and path_info.path is not None
            and path_info.default_encoder == "odb"
            and target is not None
            and target._name == "file"
        ):
            return FilePathEncodedData(path_info.path, binary=path_info.binary)
        else:
            return None


encoder = ODBEncoder
