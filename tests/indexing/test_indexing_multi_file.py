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

import pytest

import earthkit.data

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from indexing_fixtures import unique_grib_file_list  # noqa: E402


def _check_metadata(fs, ref):
    for k, v in ref.items():
        assert fs.metadata(k) == v, k


def test_indexing_multi_file_db():
    files = unique_grib_file_list()
    fs = earthkit.data.from_source("file", [f.path for f in files], indexing=True)

    assert len(fs.indexes) == 2
    assert hasattr(fs.indexes[0], "db"), "db,0"
    assert hasattr(fs.indexes[1], "db"), "db,1"
    assert len(fs.indexes[0]) == 2, "len,0"
    assert len(fs.indexes[1]) == 4, "len,1"


def test_indexing_multi_file_iterator():
    files = unique_grib_file_list()
    fs = earthkit.data.from_source("file", [f.path for f in files], indexing=True)

    ref = {
        "param": ["2t", "msl", "t", "z", "t", "z"],
        "level": [0, 0, 500, 500, 850, 850],
    }

    for i, f in enumerate(fs):
        assert f.metadata("param") == ref["param"][i], f"param,{i}"
        assert f.metadata("level") == ref["level"][i], f"level,{i}"


def test_indexing_multi_file_sel():
    files = unique_grib_file_list()
    fs = earthkit.data.from_source("file", [f.path for f in files], indexing=True)

    assert len(fs) == 6

    r = fs.sel(level=500)
    ref = {"param": ["t", "z"], "level": [500, 500], "levtype": ["pl", "pl"]}
    _check_metadata(r, ref)


def test_indexing_multi_file_sel_invalid_key():
    files = unique_grib_file_list()
    fs = earthkit.data.from_source("file", [f.path for f in files], indexing=True)

    assert len(fs) == 6
    with pytest.raises(KeyError):
        fs.sel(gridType="regular_ll")


def test_indexing_multi_file_isel():

    files = unique_grib_file_list()
    fs = earthkit.data.from_source("file", [f.path for f in files], indexing=True)

    # fs.ls(print=True)
    assert len(fs) == 6

    r = fs.isel(level=2)
    ref = {"param": ["t", "z"], "level": [850, 850], "levtype": ["pl", "pl"]}
    _check_metadata(r, ref)


def test_indexing_multi_file_isel_invalid_key():
    files = unique_grib_file_list()
    fs = earthkit.data.from_source("file", [f.path for f in files], indexing=True)

    assert len(fs) == 6
    with pytest.raises(KeyError):
        fs.isel(gridType=0)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
