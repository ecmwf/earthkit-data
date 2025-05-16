#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import pickle
import sys

import pytest

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)

# Testing internal structures in the xarray engine


def _pickle(data, representation):
    if representation == "file":
        with temp_file() as tmp:
            with open(tmp, "wb") as f:
                pickle.dump(data, f)

            with open(tmp, "rb") as f:
                data_res = pickle.load(f)
    elif representation == "memory":
        pickled_data = pickle.dumps(data)
        data_res = pickle.loads(pickled_data)
    else:
        raise ValueError(f"Invalid representation: {representation}")
    return data_res


@pytest.mark.cache
@pytest.mark.parametrize("representation", ["file", "memory"])
def test_xr_engine_builder_fieldlist(representation):
    ds_in = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl_small.grib"))

    from earthkit.data.utils.xarray.fieldlist import XArrayInputFieldList

    r = XArrayInputFieldList(ds_in)
    assert not isinstance(r.ds, XArrayInputFieldList)
    assert r.unwrap() is ds_in
    r_p = _pickle(r, representation)
    assert r_p is not r
    assert r_p.ds is not r.ds
    assert r_p.ds.metadata("time", astype=int) == [
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1200,
        1200,
        1200,
        1200,
        1200,
        1200,
        1200,
        1200,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        0,
        1200,
        1200,
        1200,
        1200,
        1200,
        1200,
        1200,
        1200,
    ]

    r0 = r.sel(param="t", level=500)
    assert not isinstance(r0.ds, XArrayInputFieldList)
    assert len(r0) == 8
    assert r0.ds.metadata("time", astype=int) == [0, 0, 1200, 1200, 0, 0, 1200, 1200]
    r0_uw = r0.unwrap()
    assert not isinstance(r0_uw, XArrayInputFieldList)
    assert r0_uw.metadata("time", astype=int) == [0, 0, 1200, 1200, 0, 0, 1200, 1200]
    r0_p = _pickle(r0, representation)
    assert r0_p is not r0
    assert r0_p.ds is not r0.ds
    assert r0_p.ds.metadata("time", astype=int) == [0, 0, 1200, 1200, 0, 0, 1200, 1200]

    r1 = r0.order_by("time")
    assert not isinstance(r1.ds, XArrayInputFieldList)
    assert r1.ds.metadata("time", astype=int) == [0, 0, 0, 0, 1200, 1200, 1200, 1200]
    r1_uw = r1.unwrap()
    assert not isinstance(r1_uw, XArrayInputFieldList)
    assert r1_uw.metadata("time", astype=int) == [0, 0, 0, 0, 1200, 1200, 1200, 1200]
    r1_p = _pickle(r1, representation)
    assert r1_p is not r1
    assert r1_p.ds is not r1.ds
    assert r1_p.ds.metadata("time", astype=int) == [0, 0, 0, 0, 1200, 1200, 1200, 1200]

    r2 = r1.order_by("step")
    assert not isinstance(r2.ds, XArrayInputFieldList)
    assert r2.ds.metadata("time", astype=int) == [0, 0, 1200, 1200, 0, 0, 1200, 1200]
    assert r2.ds.metadata("step", astype=int) == [0, 0, 0, 0, 6, 6, 6, 6]
    r2_uw = r2.unwrap()
    assert not isinstance(r2_uw, XArrayInputFieldList)
    assert r2_uw.metadata("time", astype=int) == [0, 0, 1200, 1200, 0, 0, 1200, 1200]
    assert r2_uw.metadata("step", astype=int) == [0, 0, 0, 0, 6, 6, 6, 6]
    r2_p = _pickle(r2, representation)
    assert r2_p is not r2
    assert r2_p.ds is not r2.ds
    assert r2_p.ds.metadata("time", astype=int) == [0, 0, 1200, 1200, 0, 0, 1200, 1200]
    assert r2_p.ds.metadata("step", astype=int) == [0, 0, 0, 0, 6, 6, 6, 6]
