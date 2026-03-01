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

import pytest

from earthkit.data import concat
from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file
from earthkit.data.utils.testing import IN_GITHUB
from earthkit.data.utils.testing import earthkit_examples_file


@pytest.mark.skip(reason="Some runners crash in Xarray")
def test_netcdf_fieldlist_save():
    ds = from_source("file", earthkit_examples_file("test.nc"))

    # the file must be saved without loading the fields
    # assert ds._reader._fields is None
    assert ds._fields is None

    with temp_file() as tmp:
        ds.to_target("file", tmp)
        # assert ds._reader._fields is None
        assert ds._fields is None
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        assert len(r_tmp) == 2


def test_netcdf_fieldlist_subset_save_1():
    ds = from_source("file", earthkit_examples_file("test.nc"))
    assert len(ds) == 2
    r = ds[1]

    with temp_file() as tmp:
        with pytest.raises(ValueError):
            r.to_target("file", tmp)


def test_netcdf_fieldlist_subset_save_2():
    ds = from_source("file", earthkit_examples_file("tuv_pl.nc"))
    assert len(ds) == 18
    r = ds[1:4]

    with temp_file() as tmp:
        with pytest.raises(ValueError):
            r.to_target("file", tmp)


@pytest.mark.skip(reason="Some runners crash in Xarray")
@pytest.mark.skipif(IN_GITHUB, reason="Some runners crash in Xarray")
def test_netcdf_fieldlist_multi_subset_save_1():
    ds1 = from_source("file", earthkit_examples_file("test.nc"))
    ds2 = from_source("file", earthkit_examples_file("tuv_pl.nc"))

    ds = concat(ds1, ds2)
    assert len(ds) == 20

    with temp_file() as tmp:
        ds.to_target("file", tmp)
        assert os.path.exists(tmp)
        r_tmp = from_source("file", tmp)
        assert len(r_tmp) == 20


@pytest.mark.skipif(IN_GITHUB, reason="Some runners crash in Xarray")
def test_netcdf_fieldlist_multi_subset_save_bad():
    ds1 = from_source("file", earthkit_examples_file("test.nc"))
    ds2 = from_source("file", earthkit_examples_file("tuv_pl.nc"))

    ds = concat(ds1, ds2[1:5])
    assert len(ds) == 6

    with temp_file() as tmp:
        with pytest.raises(AttributeError):
            ds.to_target("file", tmp)
