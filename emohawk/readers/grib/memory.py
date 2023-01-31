# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import logging

import eccodes

from emohawk.readers import Reader
from emohawk.readers.grib.codes import CodesHandle, GribField
from emohawk.readers.grib.index import FieldSet

LOG = logging.getLogger(__name__)


class GribMemoryReader:
    def __iter__(self):
        return self

    def __next__(self):
        handle = self._next_handle()
        if handle is not None:
            return GribFieldInMemory(CodesHandle(handle, None, None))
        raise StopIteration

    def _next_handle(self):
        raise NotImplementedError


class GribFileMemoryReader(GribMemoryReader):
    def __init__(self, path):
        self.fp = open(path, "rb")

    def __del__(self):
        self.fp.close()

    def _next_handle(self):
        return eccodes.codes_new_from_file(self.fp, eccodes.CODES_PRODUCT_GRIB)


class GribStreamReader(GribMemoryReader):
    """Wrapper around eccodes.Streamreader. The problem is that when iterating via
    the StreamReader it returns an eccodes.GRIBMessage that releases the handle when deleted.
    However, the handle has to be managed emohawk so we access the handle directly
    using _next_handle
    """

    def __init__(self, stream):
        self._stream = eccodes.StreamReader(stream)

    def _next_handle(self):
        return self._stream._next_handle()


class GribFieldInMemory(GribField):
    """Represents a GRIB message in memory"""

    def __init__(self, handle):
        super().__init__(None, None, None)
        self._handle = handle

    @GribField.handle.getter
    def handle(self):
        return self._handle

    @GribField.handle.getter
    def offset(self):
        return None

    def write(self, f):
        eccodes.codes_write(self.handle, f)


class FieldSetInMemory(FieldSet, Reader):
    """Represent a GRIB field list in memory"""

    def __init__(self, source, stream, *args, **kwargs):
        """
        The reader must support __next__.
        """
        Reader.__init__(self, source, None)
        FieldSet.__init__(self, *args, **kwargs)

        self._reader = GribStreamReader(stream)
        self._loaded = False
        self._fields = []

    def __len__(self):
        self._load()
        return len(self._fields)

    def __getitem__(self, n):
        self._load()
        return self._fields[n]

    def _load(self):
        if not self._loaded:
            for f in self._reader:
                self._fields.append(f)
            self._loaded = True
            self._reader = None
