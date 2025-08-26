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
import sys

import numpy as np
import pytest

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from forcings_fixtures import load_forcings_fs  # noqa: E402


@pytest.mark.parametrize("input_data", ["grib", "latlon"])
def test_forcings_single_index_bad(input_data):
    ds, _ = load_forcings_fs(input_data=input_data)
    idx = len(ds) + 10
    with pytest.raises(IndexError):
        ds[idx]


@pytest.mark.parametrize("input_data", ["grib", "latlon"])
@pytest.mark.parametrize("index", [0, 2, 95, -1, -96])
def test_forcings_single_index(input_data, index):
    ds, md = load_forcings_fs(input_data=input_data)
    num = len(ds)
    r = ds[index]

    ref_md = md[index]
    assert r.get(["valid_datetime", "param"]) == ref_md

    v = r.values
    assert v.shape == (209,)

    # check the original fieldlist
    assert len(ds) == num


@pytest.mark.parametrize("input_data", ["grib", "latlon"])
@pytest.mark.parametrize(
    "indexes",
    [
        slice(0, 4),
        slice(None, 4),
        slice(2, 9, 2),
        slice(8, 1, -2),
        slice(14, 18),
        slice(91, None),
    ],
)
def test_forcings_slice(input_data, indexes):
    ds, md = load_forcings_fs(input_data=input_data)
    num = len(ds)
    r = ds[indexes]

    ref_md = md[indexes]
    ref_num = len(ref_md)
    assert len(r) == ref_num
    assert r.get(["valid_datetime", "param"]) == ref_md

    v = r.values
    assert v.shape == (ref_num, 209)

    # check the original fieldlist
    assert len(ds) == num


@pytest.mark.parametrize("input_data", ["grib", "latlon"])
@pytest.mark.parametrize(
    "indexes1,indexes2",
    [
        (np.array([1, 16, 5, 9]), np.array([1, 3])),
        ([1, 16, 5, 9], [1, 3]),
        ((1, 16, 5, 9), (1, 3)),
    ],
)
def test_forcings_array_indexing(input_data, indexes1, indexes2):
    ds, md = load_forcings_fs(input_data=input_data)

    # first subset
    r = ds[indexes1]
    ref_md = [md[i] for i in indexes1]
    ref_num = len(ref_md)
    assert len(r) == ref_num
    assert r.get(["valid_datetime", "param"]) == ref_md

    # subsetting the first subset
    r1 = r[indexes2]
    ref_md = [ref_md[i] for i in indexes2]
    ref_num = len(ref_md)
    assert len(r1) == ref_num
    assert r1.get(["valid_datetime", "param"]) == ref_md


@pytest.mark.parametrize("input_data", ["grib", "latlon"])
@pytest.mark.skip(reason="Index range checking disabled")
@pytest.mark.parametrize(
    "indexes",
    [
        (np.array([1, 96, 5, 9])),
        ([1, 16, 5, 9], [1, 3]),
        ((1, 16, 5, 9), (1, 3)),
    ],
)
def test_forcings_array_indexing_bad(input_data, indexes):
    ds, _ = load_forcings_fs(input_data=input_data)
    with pytest.raises(IndexError):
        ds[indexes]


@pytest.mark.parametrize("input_data", ["grib", "latlon"])
def test_forcings_fieldlist_iterator(input_data):
    ds, md = load_forcings_fs(input_data=input_data)
    # sn = ds.metadata(["valid_datetime", "param"])
    sn = md
    assert len(sn) == len(ds)
    iter_sn = [f.get(["valid_datetime", "param"]) for f in ds]
    assert iter_sn == sn
    # repeated iteration
    iter_sn = [f.get(["valid_datetime", "param"]) for f in ds]
    assert iter_sn == sn


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
