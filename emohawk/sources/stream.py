# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from emohawk.readers import stream_reader
from emohawk.sources.memory import MemoryBaseSource

from . import Source

LOG = logging.getLogger(__name__)


class StreamSingleIterSource(Source):
    def __init__(self, reader, **kwargs):
        super().__init__(**kwargs)
        self._reader = reader

    def __iter__(self):
        return self._reader


class StreamSource(MemoryBaseSource):
    def __init__(self, stream, single_iter=True, **kwargs):
        super().__init__(**kwargs)
        self._stream = stream
        self._reader_ = None
        self._single_iter = single_iter

    @property
    def single_iter(self):
        return self._single_iter

    def mutate(self):
        if self.single_iter:
            source = StreamSingleIterSource(self._reader)
            return source
        else:
            return self

    @property
    def _reader(self):
        if self._reader_ is None:
            self._reader_ = stream_reader(self, self._stream)
            self._stream = None
        return self._reader_


source = StreamSource
