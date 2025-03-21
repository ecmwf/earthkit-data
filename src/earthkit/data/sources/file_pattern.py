# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.sources import Source
from earthkit.data.sources import from_source
from earthkit.data.sources.empty import EmptySource
from earthkit.data.sources.file import File
from earthkit.data.sources.multi import MultiSource
from earthkit.data.utils.patterns import HivePattern
from earthkit.data.utils.patterns import Pattern


class HiveFilePattern(Source):
    def __init__(self, pattern, params, **kwargs):
        self.scanner = HivePattern(pattern, params)

    def sel(self, *args, file_count_diag=None, **kwargs):
        from earthkit.data.core.index import normalize_selection

        kwargs = normalize_selection(*args, **kwargs)

        rest = {k: v for k, v in kwargs.items() if k not in self.scanner.keys}
        for k in rest:
            del kwargs[k]

        if rest:
            out = EmptySource()
            for f in self.scanner.scan(**kwargs):
                print(f"{f=}")
                print(f"{rest=}")
                ds = from_source("file", f)
                out += ds.sel(**rest)
                if file_count_diag:
                    file_count_diag.count += 1
            return out
        else:
            sources = [File(f) for f in self.scanner.scan(**kwargs)]

            if file_count_diag:
                file_count_diag.count += len(sources)

            src = MultiSource(sources)

            prev = None
            while src is not prev:
                prev = src
                src = src.mutate()
            return src


class FilePattern(MultiSource):
    def __init__(self, pattern, *args, filter=None, merger=None, hive_partitioning=False, **kwargs):
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

    def mutate(self):
        if self.hive_partitioning:
            return HiveFilePattern(self.pattern, self.params)
        else:
            return self


source = FilePattern
