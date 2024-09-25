#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np

from earthkit.data import from_source
from earthkit.data.utils.xarray.fieldlist import WrappedFieldList


def load_fieldlist(d):
    assert isinstance(d, dict)
    r = []

    prototype = {
        "gridType": "regular_ll",
        "Nx": 2,
        "Ny": 3,
        "distinctLatitudes": [-10.0, 0.0, 10.0],
        "distinctLongitudes": [0.0, 10.0],
        "values": [[1, 2], [3, 4], [5, 6]],
    }

    from itertools import product

    for x in list(product(*d.values())):
        y = dict(zip(d.keys(), x))
        r.append({**y, **prototype})

    return from_source("list-of-dicts", r)


def load_wrapped_fieldlist(d, profile, **kwargs):
    if isinstance(d, list):
        ds = []
        for x in d:
            ds.extend(load_fieldlist(x))
    elif isinstance(d, dict):
        ds = load_fieldlist(d)
    else:
        raise ValueError(f"Invalid data type={type(d)}")

    return WrappedFieldList(ds, keys=profile.index_keys, **kwargs)


def compare_dims(ds, ref_coords, order_ref_var=None):
    compare_dim_order(ds, ref_coords, order_ref_var=order_ref_var)
    for k, v in ref_coords.items():
        compare_coord(ds, k, v, mode="dim")


def compare_coords(ds, ref_coords):
    for k, v in ref_coords.items():
        compare_coord(ds, k, v, mode="coord")


def compare_coord(ds, name, ref_vals, mode="coord"):
    assert name in ds.coords, f"{name=} not in {ds.coords}"
    if mode == "dim":
        assert name in ds.sizes, f"{name=} not in {ds.sizes}"
        assert ds.sizes[name] == len(ref_vals), f"{name=} {ds.sizes[name]} != {len(ref_vals)}"

    vals = ds.coords[name].values
    if isinstance(ref_vals[0], str):
        assert vals.tolist() == ref_vals
    else:
        vals = np.asarray(vals).flatten()
        ref_vals = np.asarray(ref_vals).flatten()

        assert vals.shape == ref_vals.shape, f"{name=} {vals.shape} != {ref_vals.shape}"
        # datetime/timedelta 64
        if np.issubdtype(vals.dtype, np.datetime64) or np.issubdtype(vals.dtype, np.timedelta64):
            for i in range(len(ref_vals)):
                assert vals[i] == ref_vals[i], f"{name=} {vals[i]} != {ref_vals[i]}"
        # other arrays
        else:
            assert np.allclose(ds.coords[name].values, vals), f"{name=} {ds.coords[name].values} != {vals}"


def compare_dim_order(ds, dims, order_ref_var):
    if order_ref_var is None:
        return

    dim_order = []
    for d in ds[order_ref_var].dims:
        if d in dims:
            dim_order.append(d)
    assert dim_order == list(dims.keys()), f"{dim_order=} != {list(dims.keys())}"
