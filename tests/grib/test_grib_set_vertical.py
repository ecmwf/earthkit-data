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

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_grib_data  # noqa: E402


# @pytest.mark.parametrize("fl_type", ["file", "array", "memory"])
@pytest.mark.parametrize("fl_type", ["file"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.parametrize("write_method", ["target"])
def test_grib_set_vertical(fl_type, write_method):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set(level=700, level_type="ml")
    assert f.get("level") == 700
    assert f.get("levelist") == 700
    assert f.get("level_type") == "ml"

    assert ds_ori[0].get("level") == 500
    assert ds_ori[0].get("level_type") == "pl"

    f = ds_ori[0].set(levelist=700, level_type="ml")
    assert f.get("level") == 700
    assert f.get("levelist") == 700
    assert f.get("level_type") == "ml"
