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


class StreamMemorySource(MemoryBaseSource):
    def __init__(self, reader, **kwargs):
        super().__init__(**kwargs)
        self._reader = reader

    def __iter__(self):
        return iter(self._reader)


class StreamSource(Source):
    def __init__(self, stream, group_by=1, **kwargs):
        super().__init__(**kwargs)
        self._stream = stream
        self._reader_ = None
        self._group_by = group_by

    @property
    def group_by(self):
        return self._group_by

    def mutate(self):
        if self.group_by == 0:
            source = StreamMemorySource(self._reader)
            return source
        else:
            return self

    def __iter__(self):
        return self

    def __next__(self):
        assert self.group_by > 0
        if self.group_by == 1:
            return self._reader.__next__()
        else:
            return self._reader.read_group(self.group_by)

    @property
    def _reader(self):
        if self._reader_ is None:
            self._reader_ = stream_reader(self, self._stream)
            self._stream = None
        return self._reader_


source = StreamSource
