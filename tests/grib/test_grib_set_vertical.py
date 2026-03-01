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
@pytest.mark.parametrize("write_method", ["target"])
@pytest.mark.parametrize(
    "_kwargs,ref1,ref2",
    [
        (
            {
                "vertical.level": 320,
                "vertical.level_type": "potential_temperature",
            },
            {
                "vertical.level": 320,
                "vertical.level_type": "potential_temperature",
                "vertical.units": "K",
                "vertical.abbreviation": "pt",
                "metadata.levelist": 500,
                "metadata.level": 500,
                "metadata.levtype": "pl",
                "metadata.typeOfLevel": "isobaricInhPa",
            },
            {
                "vertical.level": 320,
                "vertical.level_type": "potential_temperature",
                "metadata.levelist": 320,
                "metadata.level": 320,
                "metadata.levtype": "pt",
                "metadata.typeOfLevel": "theta",
            },
        ),
    ],
)
def test_grib_set_vertical(fl_type, write_method, _kwargs, ref1, ref2):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set(**_kwargs)

    for k, v in ref1.items():
        assert f.get(k) == v

    # the original field is unchanged
    assert ds_ori[0].get("vertical.level") == 500
    assert ds_ori[0].get("vertical.level_type") == "pressure"

    with temp_file() as tmp:
        f.to_target("file", tmp)
        f_saved = from_source("file", tmp)
        assert len(f_saved) == 1
        for k, v in ref2.items():
            assert f_saved[0].get(k) == v, f"key {k} expected {v} got {f_saved[0].get(k)}"
