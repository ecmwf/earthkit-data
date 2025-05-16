# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from abc import ABCMeta
from abc import abstractmethod
from itertools import product

LOG = logging.getLogger(__name__)


class Splitter(metaclass=ABCMeta):
    @staticmethod
    def grids(ds):
        v, _ = ds.unique_values(["md5GridSection"])
        return v["md5GridSection"]

    @abstractmethod
    def split(self, ds, profile):
        pass

    @staticmethod
    def make(split_dims, auto_split=False):
        """TODO: auto_split is not implemented"""
        if not auto_split and not split_dims:
            return NoSplitter()
        elif split_dims:
            return DimSplitter(split_dims)
        raise ValueError("Invalid split configuration")


class NoSplitter(Splitter):
    def split(self, ds, profile):
        grids = self.grids(ds)
        if len(grids) != 1:
            raise ValueError(f"Expected one grid, got {len(grids)}")

        dims = profile.dim_keys
        yield dims, ds


class DimSplitter(Splitter):
    def __init__(self, split_dims):
        self.split_dims = split_dims

    def split(self, builder):
        ds_xr, dims = builder.prepare(self.split_dims)

        for x in product(*dims.values()):
            y = dict(zip(dims.keys(), x))
            ds_sel = ds_xr.sel(**y)
            if len(ds_sel) == 0:
                continue
            ds_sort, profile = builder.parse(ds_sel, None)
            if len(ds_sort) == 0:
                raise ValueError(f"No field found for selection={y}")
            yield ds_sort, profile, y
