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
@pytest.mark.parametrize(
    "_kwargs,ref1,ref2",
    [
        (
            {"parameter.variable": "q", "parameter.units": "kg/kg"},
            {
                "parameter.variable": "q",
                "metadata.param": "t",
                "metadata.shortName": "t",
                "parameter.units": "kg/kg",
                "metadata.units": "K",
            },
            {
                "parameter.variable": "q",
                "metadata.param": "q",
                "metadata.shortName": "q",
                "metadata.units": "kg kg**-1",
            },
        ),
        # (
        #     {"param": "q", "units": "kg/kg"},
        #     {"variable": "q", "param": "q", "grib.shortName": "t", "units": "kg/kg", "grib.units": "K"},
        #     {"variable": "q", "param": "q", "grib.shortName": "q", "units": "kg kg**-1"},
        # ),
    ],
)
def test_grib_set_parameter_1(fl_type, _kwargs, ref1, ref2):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set(**_kwargs)

    for k, v in ref1.items():
        assert f.get(k) == v

    with temp_file() as tmp:
        f.to_target("file", tmp)
        f_saved = from_source("file", tmp)
        assert len(f_saved) == 1
        for k, v in ref2.items():
            assert f_saved[0].get(k) == v


@pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
def test_grib_set_parameter_2(
    fl_type,
):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set({"parameter.variable": "ta", "parameter.units": "kg/kg"})
    assert f.get("parameter.variable") == "ta"
    assert f.get("metadata.shortName") == "t"
    assert f.get("parameter.units") == "kg/kg"
    assert f.get("metadata.units") == "K"
