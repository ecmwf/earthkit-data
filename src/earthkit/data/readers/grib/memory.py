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

from earthkit.data.indexing.fieldlist import ClonedFieldCore
from earthkit.data.indexing.fieldlist import SimpleFieldList
from earthkit.data.readers import Reader
from earthkit.data.readers.grib.codes import GribCodesHandle
from earthkit.data.readers.grib.codes import GribField

LOG = logging.getLogger(__name__)


def get_use_grib_metadata_cache():
    from earthkit.data.core.config import CONFIG

    return CONFIG.get("use-grib-metadata-cache")


class GribMemoryReader(Reader):
    def __init__(self, use_grib_metadata_cache=None, **kwargs):
        self._peeked = None
        self.consumed_ = False
        self._use_metadata_cache = (
            use_grib_metadata_cache if use_grib_metadata_cache is not None else get_use_grib_metadata_cache()
        )

    def __iter__(self):
        return self

    def __next__(self):
        if self._peeked is not None:
            msg = self._peeked
            self._peeked = None
            return msg
        handle = self._next_handle()
        msg = self._message_from_handle(handle)
        if handle is not None:
            return msg
        self.consumed_ = True
        raise StopIteration

    def _next_handle(self):
        raise NotImplementedError

    def _message_from_handle(self, handle):
        if handle is not None:
            return GribFieldInMemory(
                GribCodesHandle(handle, None, None), use_metadata_cache=self._use_metadata_cache
            )

    def batched(self, n):
        from earthkit.data.utils.batch import batched

        return batched(self, n, create=self.to_fieldlist)

    def group_by(self, *args, **kwargs):
        from earthkit.data.utils.batch import group_by

        return group_by(self, *args, create=self.to_fieldlist, sort=False)

    def to_fieldlist(self, fields):
        return GribFieldListInMemory.from_fields(fields)


class GribFileMemoryReader(GribMemoryReader):
    def __init__(self, path, **kwargs):
        super().__init__(**kwargs)
        self.fp = open(path, "rb")

    def __del__(self):
        self.fp.close()

    def _next_handle(self):
        return eccodes.codes_new_from_file(self.fp, eccodes.CODES_PRODUCT_GRIB)


class GribMessageMemoryReader(GribMemoryReader):
    def __init__(self, buf, **kwargs):
        super().__init__(**kwargs)
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

    def __init__(self, stream, **kwargs):
        super().__init__(**kwargs)
        self._stream = stream
        self._reader = eccodes.StreamReader(stream)

    def __del__(self):
        try:
            self._stream.close()
        except Exception:
            pass

    def _next_handle(self):
        try:
            return self._reader._next_handle()
        except Exception:
            self._stream.close()
            raise

    def mutate(self):
        return self

    def mutate_source(self):
        return self


class GribFieldInMemory(GribField):
    """Represents a GRIB message in memory"""

    def __init__(self, handle, use_metadata_cache=False):
        super().__init__(None, None, None, use_metadata_cache=use_metadata_cache)
        self._handle = handle

    @GribField.handle.getter
    def handle(self):
        return self._handle

    @GribField.handle.getter
    def offset(self):
        return None

    # @cached_property
    # def _metadata(self):
    #     return GribFieldMetadata(self)

    @staticmethod
    def to_fieldlist(fields):
        return GribFieldListInMemory.from_fields(fields)

    @staticmethod
    def from_buffer(buf):
        handle = eccodes.codes_new_from_message(buf)
        return GribFieldInMemory(
            GribCodesHandle(handle, None, None), use_metadata_cache=get_use_grib_metadata_cache()
        )

    def _release(self):
        self._handle = None

    def clone(self, **kwargs):
        return ClonedGribFieldInMemory(self, **kwargs)

    def __getstate__(self):
        return {"message": self.message()}

    def __setstate__(self, state):
        self.__init__(GribCodesHandle.from_message(state["message"]))


class ClonedGribFieldInMemory(ClonedFieldCore, GribFieldInMemory):
    def __init__(self, field, **kwargs):
        ClonedFieldCore.__init__(self, field, **kwargs)
        self._handle = field._handle
        GribFieldInMemory.__init__(
            self,
            field._handle,
            use_metadata_cache=field._use_metadata_cache,
        )


class GribFieldListInMemory(SimpleFieldList):
    """Represent a GRIB field list in memory loaded lazily"""

    def __init__(self, source, reader, *args, **kwargs):
        """The reader must support __next__."""
        self._reader = reader
        self._loaded = False

    def __len__(self):
        self._load()
        return super().__len__()

    def __getitem__(self, n):
        self._load()
        return super().__getitem__(n)

    def _load(self):
        # TODO: make it thread safe
        if not self._loaded:
            self.fields = [f for f in self._reader]
            self._loaded = True
            self._reader = None

    def mutate_source(self):
        return self

    @classmethod
    def merge(cls, readers):
        assert all(isinstance(s, GribFieldListInMemory) for s in readers), readers
        assert len(readers) > 1

        from itertools import chain

        return GribFieldListInMemory.from_fields(list(chain(*[f for f in readers])))

    def __getstate__(self):
        self._load()
        r = {"messages": [f.message() for f in self]}
        return r

    def __setstate__(self, state):
        fields = [GribFieldInMemory.from_buffer(m) for m in state["messages"]]
        self.__init__(None, None)
        self.fields = fields
        self._loaded = True
