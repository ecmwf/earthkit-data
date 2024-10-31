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
from abc import ABCMeta
from abc import abstractmethod
from io import IOBase

LOG = logging.getLogger(__name__)


class Target(metaclass=ABCMeta):
    @abstractmethod
    def write(
        self,
        *args,
        **kwargs,
    ):
        pass


# class FileTarget(Target):
#     def write(self, obj, *args, encoder=None, **kwargs):
#         if encoder is None:


#         obj = encoder(obj, *args, **kwargs)

#     def _write(self, filename, append=False, **kwargs):
#         flag = "wb" if not append else "ab"
#         with open(filename, flag) as f:
#             self.write(f, **kwargs)


def find_target(name):
    if name == "file":
        return FileTarget()


class FileTarget(Target):
    def __init__(self, file, split_output=False, template=None, encoder=None, **kwargs):
        self._files = {}
        self.fileobj = None
        self.filename = None

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
            self._files[path] = open(path, "wb")
        return self._files[path], path


class GribFileTarget(FileTarget):
    def write(self, values, check_nans=False, metadata={}, template=None, **kwargs):
        handle = self._coder.encode(
            values,
            check_nans=check_nans,
            metadata=metadata,
            template=template,
            **kwargs,
        )

        file, path = self.f(handle)
        handle.write(file)

        return handle, path
