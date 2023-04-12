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

from earthkit.data.readers import Reader
from earthkit.data.readers.grib.codes import CodesHandle, GribField
from earthkit.data.readers.grib.index import FieldSet

LOG = logging.getLogger(__name__)


class GribMemoryReader(Reader):
    def __iter__(self):
        return self

    def __next__(self):
        handle = self._next_handle()
        if handle is not None:
            return GribFieldInMemory(CodesHandle(handle, None, None))
        raise StopIteration

    def _next_handle(self):
        raise NotImplementedError

    def read_group(self, n):
        fields = [self.__next__() for _ in range(n)]
        return FieldSetInMemory.from_fields(fields)


class GribFileMemoryReader(GribMemoryReader):
    def __init__(self, path):
        self.fp = open(path, "rb")

    def __del__(self):
        self.fp.close()

    def _next_handle(self):
        return eccodes.codes_new_from_file(self.fp, eccodes.CODES_PRODUCT_GRIB)


class GribMessageMemoryReader(GribMemoryReader):
    def __init__(self, buf):
        self.buf = buf

    def __del__(self):
        self.buf = None

    def _next_handle(self):
        if self.buf is None:
            return None
        handle = eccodes.codes_new_from_message(self.buf)
        self.buf = None
        return handle


class GribStreamReader(GribMemoryReader):
    """Wrapper around eccodes.Streamreader. The problem is that when iterating via
    the StreamReader it returns an eccodes.GRIBMessage that releases the handle when deleted.
    However, the handle has to be managed by earthkit-data so we access it directly
    using _next_handle
    """

    def __init__(self, stream):
        self._stream = eccodes.StreamReader(stream)

    def _next_handle(self):
        return self._stream._next_handle()

    def mutate(self):
        return self

    def mutate_source(self):
        return self


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


class FieldSetInMemory(FieldSet, Reader):
    """Represent a GRIB field list in memory"""

    @staticmethod
    def from_fields(fields):
        fs = FieldSetInMemory(None, None)
        fs._fields = fields
        fs._loaded = True
        return fs

    def __init__(self, source, reader, *args, **kwargs):
        """
        The reader must support __next__.
        """
        if source is not None:
            Reader.__init__(self, source, None)
        FieldSet.__init__(self, *args, **kwargs)

        self._reader = reader
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
