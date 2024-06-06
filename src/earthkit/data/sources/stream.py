# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import itertools
import logging

from earthkit.data.core.fieldlist import FieldList
from earthkit.data.readers import stream_reader
from earthkit.data.sources.memory import MemoryBaseSource

from . import Source

LOG = logging.getLogger(__name__)


def parse_stream_kwargs(**kwargs):
    read_all = kwargs.pop("read_all", False)
    stream_kwargs = dict(read_all=read_all)
    return (stream_kwargs, kwargs)


class StreamMemorySource(MemoryBaseSource):
    def __init__(self, stream, **kwargs):
        super().__init__(**kwargs)
        if not isinstance(stream, Stream):
            raise ValueError(f"Invalid stream={stream}")
        self._stream = stream
        self._reader_ = None

    @property
    def _reader(self):
        if self._reader_ is None:
            self._reader_ = stream_reader(self, self._stream.stream, True, **self._kwargs)
            if self._reader_ is None:
                raise TypeError(f"could not create reader for stream={self._stream}")
        return self._reader_

    def mutate(self):
        source = self._reader.mutate_source()
        if source not in (None, self):
            source._parent = self
            return source
        return self


class StreamSource(Source):
    def __init__(self, stream, *, read_all=False, **kwargs):
        super().__init__()
        self._reader_ = None
        self._stream = self._wrap_stream(stream)
        self.memory = read_all
        for k in ["group_by", "batch_size"]:
            if k in kwargs:
                raise ValueError(f"Invalid argument '{k}' for StreamSource. Deprecated since 0.8.0.")

        self._kwargs = kwargs

    def __iter__(self):
        return iter(self._reader)

    def mutate(self):
        if isinstance(self._stream, (list, tuple)):
            return MultiStreamSource(self._stream, read_all=self.memory)
        else:
            if self.memory:
                return StreamMemorySource(self._stream, **self._kwargs)
            elif hasattr(self._reader, "to_fieldlist"):
                return StreamFieldList(self._reader, **self._kwargs)
        return self

    @property
    def _reader(self):
        if self._reader_ is None:
            self._reader_ = stream_reader(self, self._stream.stream, False, **self._kwargs)
            if self._reader_ is None:
                raise TypeError(f"could not create reader for stream={self._stream.stream}")
        return self._reader_

    def batched(self, n):
        """Iterate through the stream in batches of ``n``.

        Parameters
        ----------
        n: int
            Batch size.

        Returns
        -------
        object
            Returns an iterator yielding batches of ``n`` elements. Each batch is a new object
            containing a view to the data in the original object, so no data is copied. The last
            batch may contain fewer than ``n`` elements.

        """
        return self._reader.batched(n)

    def group_by(self, *keys, **kwargs):
        """Iterate through the stream in groups defined by metadata keys.

        Parameters
        ----------
        *keys: tuple
            Positional arguments specifying the metadata keys to group by.
            Keys can be a single or multiple str, or a list or tuple of str.

        Returns
        -------
        object
            Returns an iterator yielding batches of elements grouped by the metadata ``keys``. Each
            batch is a new object containing a view to the data in the original object, so no data
            is copied. It generates a new group every time the value of the ``keys`` change.

        """
        return self._reader.group_by(*keys)

    def _wrap_stream(self, stream):
        if isinstance(stream, (list, tuple)):
            r = []
            for s in stream:
                if not isinstance(s, Stream):
                    r.append(Stream(s))
                else:
                    r.append(s)
            return r
        elif not isinstance(stream, Stream):
            return Stream(stream)

        return stream

    def _status(self):
        """For testing purposes."""
        return {
            "reader": self._reader_ is not None,
            "stream": self._stream._stream is not None,
        }


class MultiStreamSource(Source):
    def __init__(self, sources, read_all=False, **kwargs):
        super().__init__(**kwargs)
        self.memory = read_all
        self.sources = self._from_sources(sources)

    def mutate(self):
        if self.memory:
            from .multi import MultiSource

            return MultiSource([s.mutate() for s in self.sources])
        else:
            first = self.sources[0]
            if hasattr(first._reader, "to_fieldlist"):
                return StreamFieldList(self, **self._kwargs)

        return self

    def __iter__(self):
        return itertools.chain(*self.sources)

    def batched(self, n):
        from earthkit.data.utils.batch import batched

        return batched(self, n)

    def group_by(self, *args):
        from earthkit.data.utils.batch import group_by

        return group_by(self, *args)

    def _from_sources(self, sources):
        r = []
        for s in sources:
            if isinstance(s, StreamSource):
                r.append(s)
            elif isinstance(s, Stream):
                r.append(StreamSource(s, read_all=self.memory))
            else:
                raise TypeError(f"Invalid source={s}")
        return r

    def _status(self):
        """For testing purposes."""
        return [s._status() for s in self.sources]


class StreamFieldList(FieldList, Source):
    def __init__(self, source, **kwargs):
        FieldList.__init__(self, **kwargs)
        self._source = source

    def mutate(self):
        return self

    def __iter__(self):
        return iter(self._source)

    def batched(self, n):
        return self._source.batched(n)

    def group_by(self, *keys, **kwargs):
        return self._source.group_by(*keys)


class Stream:
    def __init__(self, stream=None, maker=None, **kwargs):
        self._stream = stream
        self.maker = maker
        self.kwargs = kwargs
        if self._stream is None and self.maker is None:
            raise ValueError("Either stream or maker must be provided")

    @property
    def stream(self):
        if self._stream is None:
            self._stream = self.maker()
        return self._stream


def make_stream_source_from_other(source, **kwargs):
    stream_kwargs, kwargs = parse_stream_kwargs(**kwargs)

    if not isinstance(source, (list, tuple)):
        source = [source]

    for i, s in enumerate(source):
        stream = Stream(maker=s.to_stream)
        source[i] = StreamSource(stream, **stream_kwargs, **kwargs)

    if len(source) == 1:
        return source[0]
    else:
        return MultiStreamSource(source, **stream_kwargs)


source = StreamSource
