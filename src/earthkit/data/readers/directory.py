# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import fnmatch
import logging
import os
import shutil

from earthkit.data import from_source

from . import Reader

LOG = logging.getLogger(__name__)


class GlobFilter:
    def __init__(self, pattern, top):
        self.pattern = pattern
        self.skip = len(top) + 1

    def __call__(self, path):
        match = fnmatch.fnmatch(path[self.skip :], self.pattern)
        LOG.debug("GlobFilter %s %s %s", path[self.skip :], self.pattern, match)
        return match


def make_file_filter(filter, top):
    if filter is None:
        return lambda _: True

    if callable(filter):
        return filter

    if isinstance(filter, str):
        return GlobFilter(filter, top)

    raise TypeError(f"Invalid filter {filter}")


class DirectoryReader(Reader):
    def __init__(self, source, path):
        super().__init__(source, path)
        self._content = []

        filter = make_file_filter(self.filter, self.path)

        for root, _, files in os.walk(self.path):
            for file in files:
                full = os.path.join(root, file)
                LOG.debug("%s", full)
                if filter(full):
                    self._content.append(full)

    def mutate(self):
        return self

    def mutate_source(self):
        if (
            os.path.exists(os.path.join(self.path, ".zarray"))
            or os.path.exists(os.path.join(self.path, ".zgroup"))
            or os.path.exists(os.path.join(self.path, ".zmetadata"))
            or os.path.exists(os.path.join(self.path, ".zattrs"))
        ):
            if self.stream:
                raise ValueError("Cannot stream zarr directories")
            return from_source("zarr", self.path)

        if len(self._content) == 1:
            return from_source(
                "file",
                path=self._content[0],
                filter=self.filter,
                merger=self.merger,
                stream=self.stream,
                parts=self.parts,
                **self._source_kwargs,
            )

        return from_source(
            "multi",
            [
                from_source(
                    "file",
                    path=path,
                    filter=self.filter,
                    merger=self.merger,
                    stream=self.stream,
                    parts=self.parts,
                    **self._source_kwargs,
                )
                for path in sorted(self._content)
            ],
            filter=self.filter,
            merger=self.merger,
        )

    def save(self, path, **kwargs):
        shutil.copytree(self.path, path)

    def write(self, f, **kwargs):
        raise NotImplementedError()


def reader(source, path, *, magic=None, deeper_check=False, **kwargs):
    if (
        magic is None
        and os.path.isdir(path)
        and not (
            os.path.exists(os.path.join(path, ".zarray"))
            or os.path.exists(os.path.join(path, ".zgroup"))
            or os.path.exists(os.path.join(path, ".zmetadata"))
            or os.path.exists(os.path.join(path, ".zattrs"))
        )
    ):
        return DirectoryReader(source, path)
