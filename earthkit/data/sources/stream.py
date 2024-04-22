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
        self._stream = stream
        self._reader_ = None

    @property
    def _reader(self):
        if self._reader_ is None:
            self._reader_ = stream_reader(self, self._stream, True, **self._kwargs)
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
        self._stream = stream
        self.memory = read_all
        for k in ["group_by", "batch_size"]:
            if k in kwargs:
                raise ValueError(
                    f"Invalid argument '{k}' for StreamSource. Deprecated since 0.8.0."
                )

        self._kwargs = kwargs

    def __iter__(self):
        return iter(self._reader)

    def mutate(self):
        if self.memory:
            return StreamMemorySource(self._stream, **self._kwargs)

        return self

    @property
    def _reader(self):
        if self._reader_ is None:
            self._reader_ = stream_reader(self, self._stream, False, **self._kwargs)
            if self._reader_ is None:
                raise TypeError(f"could not create reader for stream={self._stream}")
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


class MultiStreamSource(Source):
    def __init__(self, sources, read_all=False, **kwargs):
        self.sources = sources
        self.memory = read_all

    def mutate(self):
        if self.memory:
            from .multi import MultiSource

            return MultiSource([s() for s in self.sources])

        return self

    def __iter__(self):
        return itertools.chain(*self.sources)

    def batched(self, n):
        from earthkit.data.utils.batch import batched

        return batched(self, n)

    def group_by(self, *args):
        from earthkit.data.utils.batch import group_by

        return group_by(self, *args)


class StreamSourceMaker:
    def __init__(self, source, stream_kwargs, **kwargs):
        self.in_source = source
        self._kwargs = kwargs
        self.stream_kwargs = dict(stream_kwargs)
        self.source = None

    def __call__(self):
        if self.source is None:
            stream = self.in_source.to_stream()
            self.source = self._from_stream(
                stream, **self.stream_kwargs, **self._kwargs
            )

            prev = None
            src = self.source
            while src is not prev:
                prev = src
                src = src.mutate()
            self.source = src

        return self.source

    def __iter__(self):
        return iter(self())

    @staticmethod
    def _from_stream(stream, read_all, **kwargs):
        _kwargs = dict(read_all=read_all)
        if read_all:
            return StreamMemorySource(stream, **kwargs)
        else:
            return StreamSource(stream, **_kwargs, **kwargs)


def _from_source(source, **kwargs):
    stream_kwargs, kwargs = parse_stream_kwargs(**kwargs)

    if not isinstance(source, (list, tuple)):
        source = [source]

    if len(source) == 1:
        maker = StreamSourceMaker(source[0], stream_kwargs, **kwargs)
        return maker()
    else:
        sources = [StreamSourceMaker(s, stream_kwargs, **kwargs) for s in source]
        return MultiStreamSource(sources, **stream_kwargs)


source = StreamSource
