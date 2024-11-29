# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
import re
from io import IOBase

from earthkit.data.encoders import _find_encoder

from . import Target

LOG = logging.getLogger(__name__)


class FileTarget(Target):
    def __init__(self, file, split_output=False, append=False, **kwargs):
        super().__init__(**kwargs)

        self._files = {}
        self.fileobj = None
        self.filename = None
        self.append = append
        self.ext = None

        if isinstance(file, IOBase):
            self.fileobj = file
            split_output = False
        else:
            self.filename = file
            if self.filename is not None:
                _, self.ext = os.path.splitext(self.filename)

        if split_output:
            self.split_output = re.findall(r"\{(.*?)\}", self.filename)
        else:
            self.split_output = None

    def close(self):
        for f in self._files.values():
            f.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, trace):
        self.close()

    def _f(self, handle):
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

    def write(self, data=None, encoder=None, template=None, **kwargs):
        if data is not None:
            # data._write_to_target(self, encoder=encoder, template=template, **kwargs)
            # data._write(self, encoder=encoder, template=template, **kwargs)
            data._to_target(self, encoder=encoder, template=template, **kwargs)
        else:
            pass

        # from earthkit.data.core.fieldlist import FieldList

        # if encoder is None:
        #     encoder = self._coder

        # if template is None:
        #     template = self.template

        # # kwargs = dict(**kwargs)
        # # kwargs["template"] = template

        # if isinstance(data, FieldList):
        #     data.to_target(self, encoder=encoder, template=template, **kwargs)
        # else:
        #     if encoder is None:
        #         encoder = self._coder

        #     # this can consume kwargs
        #     encoder = _find_encoder(data, encoder)
        #     # print("encoder", encoder)

        #     f, _ = self._f(encoder)
        #     data = encoder.encode(data, template=template, **kwargs)
        #     data.write(f)

    def _write_reader(self, reader, **kwargs):
        f, _ = self._f(None)

        if not reader.appendable:
            assert f.tell() == 0
        mode = "rb" if reader.binary else "r"
        with open(reader.path, mode) as g:
            while True:
                chunk = g.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)

    def _write(self, data, encoder=None, default_encoder=None, template=None, **kwargs):
        print("encoder", encoder, "template", template, "kwargs", kwargs.keys())
        if encoder is None:
            encoder = self._coder

        print("-> encoder", encoder)
        # this can consume kwargs
        encoder = _find_encoder(data, encoder, default_encoder=default_encoder, suffix=self.ext)
        print("-> encoder", encoder)

        f, _ = self._f(encoder)
        d = encoder.encode(data, template=template, **kwargs)
        d.to_file(f)

    # def _write_field(self, data, encoder=None, template=None, **kwargs):
    #     print("encoder", encoder, "template", template, "kwargs", kwargs.keys())
    #     if encoder is None:
    #         encoder = self._coder

    #     print("-> encoder", encoder)
    #     # this can consume kwargs
    #     encoder = _find_encoder(data, encoder, suffix=self.ext)
    #     print("-> encoder", encoder)

    #     f, _ = self._f(encoder)
    #     d = encoder.encode(data, template=template, **kwargs)
    #     d.write(f)

    # def _write_fieldlist(self, data, encoder=None, template=None, **kwargs):
    #     for f in data:
    #         f.to_target(self, encoder=encoder, template=template, **kwargs)

    # def _write_xr_fieldlist(self, data, encoder=None, template=None, **kwargs):
    #     encoder = _find_encoder(data, encoder, suffix=self.ext)
    #     f, _ = self._f(encoder)
    #     d = encoder.encode(data, template=template, **kwargs)
    #     d.write(f)


target = FileTarget
