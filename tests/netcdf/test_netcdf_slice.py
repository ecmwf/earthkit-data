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
import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import load_nc_or_xr_source


@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize(
    "index,expected_meta",
    [
        (0, ["t", 1000]),
        (2, ["t", 700]),
        (17, ["v", 300]),
        (-1, ["v", 300]),
        (-5, ["v", 850]),
    ],
)
def test_netcdf_single_index(mode, index, expected_meta):
    f = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.nc"), mode)

    r = f[index]
    assert r.metadata(["variable", "level"]) == expected_meta
    v = r.values
    assert v.shape == (84,)
    # eps = 0.001
    # assert np.isclose(v[1088], 304.5642, eps)


def test_netcdf_single_index_bad():
    f = from_source("file", earthkit_examples_file("tuv_pl.nc"))
    with pytest.raises(IndexError):
        f[27]


@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize(
    "indexes,expected_meta",
    [
        (slice(0, 4), [["t", 1000], ["t", 850], ["t", 700], ["t", 500]]),
        (slice(None, 4), [["t", 1000], ["t", 850], ["t", 700], ["t", 500]]),
        (slice(2, 9, 2), [["t", 700], ["t", 400], ["u", 1000], ["u", 700]]),
        (slice(8, 1, -2), [["u", 700], ["u", 1000], ["t", 400], ["t", 700]]),
        (slice(14, 18), [["v", 700], ["v", 500], ["v", 400], ["v", 300]]),
        (slice(14, None), [["v", 700], ["v", 500], ["v", 400], ["v", 300]]),
    ],
)
def test_netcdf_slice_single_file(mode, indexes, expected_meta):
    f = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.nc"), mode)
    r = f[indexes]
    assert len(r) == 4
    assert r.metadata(["variable", "level"]) == expected_meta
    v = r.values
    assert v.shape == (4, 84)
    # check the original fieldlist
    assert len(f) == 18
    assert f.metadata("variable") == ["t"] * 6 + ["u"] * 6 + ["v"] * 6


@pytest.mark.xfail
@pytest.mark.parametrize(
    "indexes,expected_meta",
    [
        (slice(1, 4), [["msl", 0], ["t", 500], ["z", 500]]),
        (slice(1, 6, 2), [["msl", 0], ["z", 500], ["z", 850]]),
        (slice(5, 0, -2), [["z", 850], ["z", 500], ["msl", 0]]),
        (slice(3, 6), [["z", 500], ["t", 850], ["z", 850]]),
    ],
)
def test_netcdf_slice_multi_file(indexes, expected_meta):
    f = from_source(
        "file",
        [earthkit_examples_file("test.nc"), earthkit_examples_file("tuv_pl.nc")],
    )
    r = f[indexes]
    assert len(r) == 3
    assert r.metadata(["variable", "level"]) == expected_meta
    # v = r.values
    # assert v.shape == (3, 84)
    # check the original fieldlist
    assert len(f) == 2 + 18
    assert f.metadata("shortName") == ["2t", "msl", "t", "z", "t", "z"]


@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize(
    "indexes1,indexes2",
    [
        (np.array([1, 16, 5, 9]), np.array([1, 3])),
        ([1, 16, 5, 9], [1, 3]),
        ((1, 16, 5, 9), (1, 3)),
    ],
)
def test_netcdf_array_indexing(mode, indexes1, indexes2):
    f = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.nc"), mode)

    r = f[indexes1]
    assert len(r) == 4
    assert r.metadata("variable") == ["t", "v", "t", "u"]

    r1 = r[indexes2]
    assert len(r1) == 2
    assert r1.metadata("variable") == ["v", "u"]


@pytest.mark.skip(reason="Index range checking disabled")
@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize(
    "indexes",
    [
        (np.array([1, 19, 5, 9])),
        ([1, 16, 5, 9], [1, 3]),
        ((1, 16, 5, 9), (1, 3)),
    ],
)
def test_netcdf_array_indexing_bad(mode, indexes):
    f = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.nc"), mode)
    with pytest.raises(IndexError):
        f[indexes]


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_fieldlist_iterator(mode):
    g = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.nc"), mode)
    sn = g.metadata("variable")
    assert len(sn) == 18
    iter_sn = [f.metadata("variable") for f in g]
    assert iter_sn == sn
    # repeated iteration
    iter_sn = [f.metadata("variable") for f in g]
    assert iter_sn == sn


def test_netcdf_fieldlist_iterator_with_zip():
    # this tests something different with the iterator - this does not try to
    # 'go off the edge' of the fieldlist, because the length is determined by
    # the list of levels
    g = from_source("file", earthkit_examples_file("tuv_pl.nc"))
    ref_levs = g.metadata("level")
    assert len(ref_levs) == 18
    levs1 = []
    levs2 = []
    for k, f in zip(g.metadata("level"), g):
        levs1.append(k)
        levs2.append(f.metadata("level"))
    assert levs1 == ref_levs
    assert levs2 == ref_levs


def test_netcdf_fieldlist_iterator_with_zip_multiple():
    # same as test_fieldlist_iterator_with_zip() but multiple times
    g = from_source("file", earthkit_examples_file("tuv_pl.nc"))
    ref_levs = g.metadata("level")
    assert len(ref_levs) == 18
    for i in range(2):
        levs1 = []
        levs2 = []
        for k, f in zip(g.metadata("level"), g):
            levs1.append(k)
            levs2.append(f.metadata("level"))
        assert levs1 == ref_levs, i
        assert levs2 == ref_levs, i


@pytest.mark.parametrize("mode", ["nc", "xr"])
def test_netcdf_fieldlist_reverse_iterator(mode):
    g = load_nc_or_xr_source(earthkit_examples_file("tuv_pl.nc"), mode)
    sn = g.metadata("variable")
    sn_reversed = list(reversed(sn))
    assert sn_reversed[0] == "v"
    assert sn_reversed[17] == "t"
    gr = reversed(g)
    iter_sn = [f.metadata("variable") for f in gr]
    assert len(iter_sn) == len(sn_reversed)
    assert iter_sn == sn_reversed
    assert iter_sn == ["v"] * 6 + ["u"] * 6 + ["t"] * 6


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
