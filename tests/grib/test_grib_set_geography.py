#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import os
import sys

import numpy as np
import pytest

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import load_grib_data  # noqa: E402


@pytest.mark.parametrize("fl_type", ["file"])
# @pytest.mark.parametrize("write_method", WRITE_TO_FILE_METHODS)
@pytest.mark.parametrize("write_method", ["target"])
@pytest.mark.parametrize(
    "_kwargs",
    [
        {
            "latitudes": np.array([10.0, 20.0, 30.0]),
            "longitudes": np.array([0.0, 10.0, 20.0]),
            "values": np.array([1.0, 2.0, 3.0]),
        },
    ],
)
def test_grib_set_geo(fl_type, write_method, _kwargs):
    ds_ori, _ = load_grib_data("test4.grib", fl_type)

    f = ds_ori[0].set(**_kwargs)
    assert np.allclose(f.get("geography.latitudes"), np.array([10.0, 20.0, 30.0]))
    assert np.allclose(f.get("geography.longitudes"), np.array([0.0, 10.0, 20.0]))
    assert np.allclose(f.values, np.array([1.0, 2.0, 3.0]))
    assert f.get("time.base_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert f.get("time.valid_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert f.get("time.step") == datetime.timedelta(hours=0)
    # assert f.get("time_span") == datetime.timedelta(hours=0)

    # the original field is unchanged
    assert ds_ori[0].get("geography.latitudes").shape == (181, 360)
    assert ds_ori[0].get("geography.longitudes").shape == (181, 360)
    assert ds_ori[0].values.shape == (65160,)
    assert ds_ori[0].get("time.base_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("time.valid_datetime") == datetime.datetime(2007, 1, 1, 12)
    assert ds_ori[0].get("time.step") == datetime.timedelta(hours=0)
    # assert ds_ori[0].get("time_span") == datetime.timedelta(hours=0)
