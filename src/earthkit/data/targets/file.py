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
    def __init__(self, file, split_output=False, append=False, **kwargs):
        super().__init__(**kwargs)

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
        from earthkit.data.core.fieldlist import FieldList

        if encoder is None:
            encoder = self._coder

        if template is None:
            template = self.template

        # kwargs = dict(**kwargs)
        # kwargs["template"] = template

        if isinstance(data, FieldList):
            data.to_target(self, encoder=encoder, template=template, **kwargs)
        else:
            if encoder is None:
                encoder = self._coder

            # this can consume kwargs
            encoder = _find_encoder(data, encoder)
            # print("encoder", encoder)

            f, _ = self._f(encoder)
            data = encoder.encode(data, template=template, **kwargs)
            data.write(f)


target = FileTarget
