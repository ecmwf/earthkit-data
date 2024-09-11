# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import math
from abc import ABCMeta
from abc import abstractmethod

LOG = logging.getLogger(__name__)


class Splitter(metaclass=ABCMeta):
    @staticmethod
    def grids(ds):
        v = ds.unique_values(["md5GridSection"])
        return v["md5GridSection"]

    @abstractmethod
    def split(self, ds, profile):
        pass

    @staticmethod
    def make(auto_split, split_dims):
        if not auto_split and not split_dims:
            return NoSplitter()
        elif split_dims:
            return DimSplitter(split_dims)
        elif auto_split:
            return AutoSplitter()
        else:
            raise ValueError("Invalid split configuration")


class NoSplitter(Splitter):
    def split(self, ds, profile):
        grids = self.grids(ds)
        # print(f"grids={grids}")
        if len(grids) != 1:
            raise ValueError(f"Expected one grid, got {len(grids)}")

        dims = profile.dim_keys
        yield dims, ds


class DimSplitter(Splitter):
    def __init__(self, split_dims):
        self.split_dims = split_dims

    def split(self, ds, profile):
        grids = self.grids(ds)
        from itertools import product

        dims = ds.unique_values(self.split_dims)
        if len(grids) > 1:
            dims["md5GridSection"] = grids

        for x in product(*dims.values()):
            y = dict(zip(dims.keys(), x))
            ds_sel = ds.sel(**y)
            yield profile.dims.to_list(), ds_sel


class AutoSplitter(Splitter):
    def split(self, ds, profile):
        grids = self.grids(ds)
        dims = {k: ds.index(k) for k in profile.dim_keys}

        for ds_gr, grid in self.ds_grids(grids, ds):
            holes = {k: False for k in profile.dim_keys}
            cube_vars = []
            dims = {k: ds_gr.index(k) for k in profile.dim_keys}
            t_dims = []
            for d in dims:
                if len(ds_gr.index(d)) > 1 or (not profile.squeeze and len(ds_gr.index(d)) == 1):
                    t_dims.append(d)

            # try to see if dims form a cube
            for v in profile.variables:
                keys = {profile.variable_key: v}
                ds_var = ds_gr.sel(**keys)

                if len(ds_var) > 0:
                    n = math.prod([len(ds_var.index(d)) for d in profile.dim_keys])
                    # print(f" -> n={n} len={len(ds_var)}")
                    if n == len(ds_var):
                        cube_vars.append(v)
                    else:
                        for h in self.dims_hole(ds_var, t_dims):
                            holes[h] = True

            holes = [k for k in holes if holes[k]]
            # print("holes=", holes)
            if not holes:
                yield t_dims, ds_gr
            else:
                splitter = DimSplitter(holes)
                yield splitter.split(ds, profile)

    def ds_grids(self, grids, ds):
        if len(grids) == 1:
            yield ds
        elif len(grids) > 1:
            for gr in grids:
                ds_sel = ds.sel(md5GridSection=gr)
                yield ds_sel, gr

    def dims_hole(self, ds, full_dims):
        holes = []
        dims = {k: ds.index(k) for k in full_dims}
        for d in dims:
            if dims[d] != full_dims[d]:
                holes.append(d)
        return holes
