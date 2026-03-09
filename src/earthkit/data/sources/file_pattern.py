# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from typing import Any as TypingAny
from typing import Dict
from typing import Optional
from typing import Tuple
from typing import Union

from earthkit.data import concat
from earthkit.data.data import SourceData
from earthkit.data.sources import Source
from earthkit.data.sources import from_source_internal
from earthkit.data.sources.empty import EmptySource
from earthkit.data.sources.file import File
from earthkit.data.sources.multi import MultiSource
from earthkit.data.utils.patterns import HivePattern
from earthkit.data.utils.patterns import Pattern


class HiveFilePatternData(SourceData):
    _TYPE_NAME = "HiveFilePattern"

    @property
    def available_types(self):
        return [self._FIELDLIST]

    def describe(self):
        pass

    def to_source(self):
        return self._source

    def to_fieldlist(self, *args, **kwargs):
        return self._source.to_fieldlist(*args, **kwargs)


# class StreamFieldList(FieldList, Source):
#     def __init__(self, source, **kwargs):
#         IndexFieldListBase.__init__(self, **kwargs)
#         self._source = source

#     def mutate(self):
#         return self

#     def __len__(self):
#         raise NotImplementedError("StreamFieldList does not support __len__")

#     def _getitem(self, item):
#         raise NotImplementedError("StreamFieldList does not support _getitem")

#     def __iter__(self):
#         return iter(self._source)

#     def batched(self, n):
#         raise

#     def group_by(self, *keys, **kwargs):
#         raise NotImplementedError("StreamFieldList does not support group_by")

#     def __getstate__(self):
#         raise NotImplementedError("StreamFieldList cannot be pickled")

#     def to_xarray(self, **kwargs):
#         raise NotImplementedError("StreamFieldList does not support to_xarray")

#     @classmethod
#     def merge(cls, sources):
#         raise NotImplementedError("StreamFieldList does not support merge")

#     def _default_encoder(self):
#         return None

#     def to_data_object(self):
#         return HiveFilePatternData(self)


class HiveFilePattern(Source):
    def __init__(self, pattern: str, params: Dict[str, TypingAny], **kwargs: TypingAny) -> None:
        self.scanner = HivePattern(pattern, params)

    def sel(
        self,
        *args: Tuple[Dict[str, TypingAny]],
        _hive_diag: Optional[TypingAny] = None,
        **kwargs: TypingAny,
    ) -> Union[EmptySource, MultiSource]:
        from earthkit.data.core.index import normalise_selection

        kwargs, _ = normalise_selection(*args, **kwargs)

        rest = {k: v for k, v in kwargs.items() if k not in self.scanner.params}
        for k in rest:
            del kwargs[k]

        if rest:
            out = EmptySource()
            for f in self.scanner.scan(**kwargs):
                ds = from_source_internal("file", f).to_fieldlist()
                out = concat(out, ds.sel(**rest))
                if _hive_diag:
                    _hive_diag.file(1)
                    _hive_diag.sel(1)

            return out
        else:
            sources = [File(f) for f in self.scanner.scan(**kwargs)]

            if _hive_diag:
                _hive_diag.file(len(sources))

            src = MultiSource(sources)

            prev = None
            while src is not prev:
                prev = src
                src = src.mutate()

            return src.to_fieldlist()
            return src

    def to_data_object(self):
        return HiveFilePatternData(self)


class FilePattern(MultiSource):
    def __init__(
        self,
        pattern: str,
        *args: Tuple[Dict[str, TypingAny]],
        filter: Optional[TypingAny] = None,
        merger: Optional[TypingAny] = None,
        hive_partitioning: bool = False,
        **kwargs: TypingAny,
    ) -> None:
        self.hive_partitioning = hive_partitioning

        if not self.hive_partitioning:
            files = Pattern(pattern).substitute(*args, **kwargs)
            if not isinstance(files, list):
                files = [files]

            sources = [File(file) for file in sorted(files)]
            super().__init__(sources, filter=filter, merger=merger)

        else:
            self.pattern = pattern
            params = {}
            for a in args:
                params.update(a)
            params.update(kwargs)
            self.params = params

    def mutate(self) -> Union["HiveFilePattern", "FilePattern"]:
        if self.hive_partitioning:
            return HiveFilePattern(self.pattern, self.params)
        else:
            return super().mutate()


source = FilePattern
