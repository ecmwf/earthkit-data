# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.readers import stream_reader
from earthkit.data.sources.memory import MemoryBaseSource

from . import Source

LOG = logging.getLogger(__name__)


class StreamMemorySource(MemoryBaseSource):
    def __init__(self, reader, **kwargs):
        super().__init__(**kwargs)
        self._reader = reader

    def __iter__(self):
        return iter(self._reader)


class StreamSource(Source):
    def __init__(self, stream, batch_size=1, **kwargs):
        super().__init__(**kwargs)
        self._stream = stream
        self._reader_ = None
        self._batch_size = batch_size

    @property
    def batch_size(self):
        return self._batch_size

    def mutate(self):
        if self.batch_size == 0:
            source = StreamMemorySource(self._reader)
            return source
        else:
            return self

    def __iter__(self):
        return self

    def __next__(self):
        assert self.batch_size > 0
        if self.batch_size == 1:
            return self._reader.__next__()
        else:
            return self._reader.read_batch(self.batch_size)

    @property
    def _reader(self):
        if self._reader_ is None:
            self._reader_ = stream_reader(self, self._stream)
            self._stream = None
        return self._reader_


source = StreamSource
