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

from earthkit.data import from_source
from earthkit.data.core.temporary import temp_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_grib_data  # noqa: E402


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.parametrize("write_method", ["target"])
@pytest.mark.parametrize(
    "_kwargs,ref_ori, ref_set,ref_saved",
    [
        (
            {"member": 3},
            {
                "member": "1",
                "grib.number": 1,
                "grib.level": 850,
            },
            {
                "member": "3",
                "grib.number": 1,
                "grib.level": 850,
            },
            {
                "member": "3",
                "grib.number": 3,
                "grib.level": 850,
            },
        ),
    ],
)
def test_grib_set_ensemble(fl_type, write_method, _kwargs, ref_ori, ref_set, ref_saved):
    ds_ori, _ = load_grib_data("ens_50.grib", fl_type, folder="data")

    f = ds_ori[0].set(**_kwargs)

    for k, v in ref_set.items():
        assert f.get(k) == v

    # the original field is unchanged
    for k, v in ref_ori.items():
        assert ds_ori[0].get(k) == v

    with temp_file() as tmp:
        f.to_target("file", tmp)
        f_saved = from_source("file", tmp)
        assert len(f_saved) == 1
        for k, v in ref_saved.items():
            assert f_saved[0].get(k) == v, f"key {k} expected {v} got {f_saved[0].get(k)}"
