# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.sources import Source

from .indexed import IndexedFieldList


class StreamFieldList(IndexedFieldList, Source):
    def __init__(self, source, **kwargs):
        IndexedFieldList.__init__(self, **kwargs)
        self._source = source

    def mutate(self):
        return self

    def __len__(self):
        raise NotImplementedError("StreamFieldList does not support __len__")

    def _getitem(self, item):
        raise NotImplementedError("StreamFieldList does not support _getitem")

    def __iter__(self):
        return iter(self._source)

    def batched(self, n):
        return self._source.batched(n)

    def group_by(self, *keys, **kwargs):
        return self._source.group_by(*keys)

    def __getstate__(self):
        raise NotImplementedError("StreamFieldList cannot be pickled")

    def to_xarray(self, **kwargs):
        from .simple import SimpleFieldList

        fields = [f for f in self]
        return SimpleFieldList.from_fields(fields).to_xarray(**kwargs)

    @classmethod
    def merge(cls, sources):
        from earthkit.data.sources.stream import MultiStreamSource

        assert all(isinstance(s, StreamFieldList) for s in sources), sources
        assert len(sources) > 1
        return MultiStreamSource.merge(sources)

    def default_encoder(self):
        return None
