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

from earthkit.data.featurelist.simple import SimpleFeatureListBase
from earthkit.data.featurelist.stream import StreamFeatureList
from earthkit.data.readers import Reader

from .file import BUFRFeatureListMixin

LOG = logging.getLogger(__name__)


class BUFRFeatureListInMemory(BUFRFeatureListMixin, SimpleFeatureListBase):
    """A FeatureList implementation containing a list of BUFRMessages held in memory."""

    def __init__(self, messages=None):
        self.__features = messages if messages is not None else []

    @property
    def _features(self):
        return self.__features

    def __getstate__(self) -> dict:
        return {"_features": self._features}

    def __setstate__(self, state: dict):
        self.__init__(state.pop("_features"))

    def to_data_object(self):
        from earthkit.data.data.featurelist import FeatureListData

        return FeatureListData(self)


class BUFRStreamFeatureList(BUFRFeatureListMixin, StreamFeatureList):
    """A StreamFeatureList specialised to iterate BUFRMessages read from a stream."""

    in_memory_class = BUFRFeatureListInMemory


class BUFRMemoryReader(Reader):
    def __init__(self, **kwargs):
        self._peeked = None
        self.consumed_ = False

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
            from .handle import BUFRCodesHandle
            from .message import BUFRMessage

            handle = BUFRCodesHandle(handle, None, None)
            return BUFRMessage(None, None, None, handle=handle)

    def batched(self, n):
        from earthkit.data.utils.batch import batched

        return batched(self, n, create=self.to_featurelist)

    def group_by(self, *args, **kwargs):
        from earthkit.data.utils.batch import group_by

        return group_by(self, *args, create=self.to_featurelist, sort=False)

    def to_featurelist(self, messages):
        return BUFRFeatureListInMemory(messages)


class BUFRStreamReader(BUFRMemoryReader):
    """Wrapper around eccodes.StreamReader for BUFR data.

    As with :class:`~earthkit.data.readers.grib.memory.GribStreamReader`, iterating via the
    StreamReader returns an eccodes.BUFRMessage that releases the handle when deleted. However,
    the handle has to be managed by earthkit-data so we access it directly using ``_next_handle``.
    """

    _format = "bufr"
    stream_featurelist_class = BUFRStreamFeatureList

    def __init__(self, stream, **kwargs):
        super().__init__(**kwargs)
        self._stream = stream
        self._reader = eccodes.StreamReader(stream, kind=eccodes.CODES_PRODUCT_BUFR)

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

    def to_data_object(self):
        from earthkit.data.data.stream import StreamFeatureListData

        return StreamFeatureListData(self)

    def _encode_default(self, encoder, *args, **kwargs):
        return encoder._encode_featurelist(self.to_featurelist([m for m in self]), *args, **kwargs)
