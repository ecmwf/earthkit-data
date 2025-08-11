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


class _InternalPassThroughEncodedData(EncodedData):
    def __init__(self, d):
        self.d = d

    def to_bytes(self):
        raise NotImplementedError

    def to_file(self, f, **kwargs):
        # if not self.d.appendable:
        #     assert f.tell() == 0
        mode = "rb" if self.d.binary else "r"
        with open(self.d.path, mode) as g:
            while True:
                chunk = g.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

    def metadata(self, key):
        raise NotImplementedError


class _InternalPassThroughEncoder(Encoder):
    """A pass-through encoder implemented for Readers"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def encode(
        self,
        data=None,
        **kwargs,
    ):
        if data is not None:
            from earthkit.data.wrappers import get_wrapper

            data = get_wrapper(data)
            return data._encode(self, **kwargs)
        else:
            raise ValueError("No data to encode")

    def _encode(self, data, **kwargs):
        assert data is not None
        from earthkit.data.readers import Reader

        if issubclass(data.__class__, Reader):
            return _InternalPassThroughEncodedData(data)
        raise ValueError("data is not a Reader")

    def _encode_field(self, field, **kwargs):
        raise NotImplementedError

    def _encode_fieldlist(self, fieldlist, **kwargs):
        return self._encode(fieldlist, **kwargs)

    def _encode_xarray(self, data, **kwargs):
        raise NotImplementedError


encoder = _InternalPassThroughEncoder
