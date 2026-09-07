# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import warnings

import numpy as np

from . import Reader


class NumpyReader(Reader):
    def __init__(self, source, path, **kwargs):
        if kwargs:
            names = ", ".join(repr(name) for name in kwargs)
            warnings.warn(
                f"Arguments {names} have no effect for the NumPy reader.",
                UserWarning,
                stacklevel=2,
            )
        super().__init__(source, path)

    def to_numpy(self, numpy_load_kwargs={}):
        return np.load(self.path, **numpy_load_kwargs)

    def __iter__(self):
        return iter([self])


class NumpyZipReader(Reader):
    def __init__(self, source, path, **kwargs):
        if kwargs:
            names = ", ".join(repr(name) for name in kwargs)
            warnings.warn(
                f"Arguments {names} have no effect for the NumPy ZIP reader.",
                UserWarning,
                stacklevel=2,
            )
        super().__init__(source, path)

    def to_numpy(self, numpy_load_kwargs={}):
        return np.load(self.path, **numpy_load_kwargs)


def reader(source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    if magic is not None:
        if magic[:6] == b"\x93NUMPY":
            return NumpyReader(source, path, **kwargs)

        _, extension = os.path.splitext(path)
        if magic[:4] == b"PK\x03\x04" and extension == ".npz":
            return NumpyZipReader(source, path, **kwargs)


READER = reader
