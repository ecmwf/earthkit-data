# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import re
from io import IOBase

from earthkit.data.encoders import _find_encoder

from . import Target

LOG = logging.getLogger(__name__)


class FileTarget(Target):
    def __init__(self, file, split_output=False, template=None, encoder=None, append=False, **kwargs):
        self._files = {}
        self.fileobj = None
        self.filename = None
        self.append = append

        if isinstance(file, IOBase):
            self.fileobj = file
            split_output = False
        else:
            self.filename = file

        if split_output:
            self.split_output = re.findall(r"\{(.*?)\}", self.filename)
        else:
            self.split_output = None

        self._coder = encoder

        # self._coder = GribCoder(template=template, **kwargs)

    def close(self):
        for f in self._files.values():
            f.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.close()

    # @abstractmethod
    # def write(
    #     self,
    #     values,
    #     check_nans=False,
    #     metadata={},
    #     template=None,
    #     **kwargs,
    # ):
    #     pass

    def f(self, handle):
        if self.fileobj:
            return self.fileobj, None

        if self.split_output:
            path = self.filename.format(**{k: handle.get(k) for k in self.split_output})
        else:
            path = self.filename

        if path not in self._files:
            flag = "wb" if not self.append else "ab"
            self._files[path] = open(path, flag)

        return self._files[path], path

    def write(self, data, data_format=None, encoder=None, **kwargs):
        from earthkit.data.core.fieldlist import FieldList

        if isinstance(data, FieldList):
            # if encoder is None:
            #     encoder = self._coder

            # encoder = _find_encoder(data, encoder, data_format, **kwargs)

            # print("encoder", encoder)
            # f, path = self.f(encoder)

            self._write_fieldlist(data, encoder, data_format, **kwargs)
        else:
            if encoder is None:
                encoder = self._coder

            encoder = _find_encoder(data, encoder, data_format, **kwargs)

            f, _ = self.f(encoder)
            data = encoder.encode(data)
            data.write(f)

    def _write_fieldlist(self, data, encoder, data_format, **kwargs):
        if encoder is None:
            encoder = self._coder

        encoder = _find_encoder(data[0], encoder, data_format, **kwargs)

        print("encoder", encoder)
        f, _ = self.f(encoder)

        for field in data:
            d = encoder.encode(template=field)
            d.write(f)


Target = FileTarget
