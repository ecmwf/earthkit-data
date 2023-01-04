# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import fnmatch
import os
import shutil

import emohawk
from emohawk.wrappers.xarray import XArrayDatasetWrapper

from . import Reader, get_reader


class GlobFilter:
    def __init__(self, pattern, top):
        self.pattern = pattern
        self.skip = len(top) + 1

    def __call__(self, path):
        match = fnmatch.fnmatch(path[self.skip :], self.pattern)
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
    """
    Class for reading and polymorphing files stored in directories.
    """

    def __init__(self, source):
        super().__init__(source)
        self.__xarray_wrapper = None
        self.__xarray_kwargs = dict()

        self._content = []

        filter = make_file_filter(None, self.source)

        for root, _, files in os.walk(self.source):
            for file in files:
                full = os.path.join(root, file)
                if filter(full):
                    self._content.append(full)

    def mutate(self):
        if len(self._content) == 1:
            return get_reader(self._content[0])
        return self

    def mutate_source(self):
        return [emohawk.open(path) for path in sorted(self._content)]

    def save(self, path):
        shutil.copytree(self.path, path)

    def write(self, f):
        raise NotImplementedError()

    def _xarray_wrapper_concat(self, **kwargs):
        if self.__xarray_wrapper is None or kwargs != self.__xarray_kwargs:
            m_sources = self.mutate_source()
            dataset = type(m_sources[0]).to_xarray_multi_from_paths(
                sorted(self._content), **kwargs
            )
            self.__xarray_kwargs = kwargs.copy()
            self.__xarray_wrapper = XArrayDatasetWrapper(dataset)
        return self.__xarray_wrapper

    def _xarray_wrapper_list(self, **kwargs):
        if self.__xarray_wrapper is None or kwargs != self.__xarray_kwargs:
            m_sources = self.mutate_source()
            dataset_list = [m_source.to_xarray(**kwargs) for m_source in m_sources]
            self.__xarray_wrapper = [
                XArrayDatasetWrapper(dataset) for dataset in dataset_list
            ]
            self.__xarray_kwargs = kwargs.copy()
        return self.__xarray_wrapper

    def _to_xarray(self, *args, **kwargs):

        if not kwargs.get("concat", True):
            return [
                _xr_wrapper.to_xarray()
                for _xr_wrapper in self._xarray_wrapper_list(**kwargs)
            ]

        try:
            return self._xarray_wrapper_concat(**kwargs)._to_xarray()
        except:  # noqa: E722
            # If any incompatibility issue with directory contents, return a list of xarrays
            return [
                _xr_wrapper.to_xarray()
                for _xr_wrapper in self._xarray_wrapper_list(**kwargs)
            ]


def reader(path, magic=None, deeper_check=False, **kwargs):
    if magic is None or os.path.isdir(path):
        return DirectoryReader(path)
