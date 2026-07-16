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

import numpy as np
import pytest

from earthkit.data.utils.testing import earthkit_test_data_file, load_nc_or_xr_source


@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize(
    "_kwargs",
    [
        {
            "geography.latitudes": np.array([10.0, 20.0, 30.0]),
            "geography.longitudes": np.array([0.0, 10.0, 20.0]),
            "values": np.array([1.0, 2.0, 3.0]),
        },
    ],
)
def test_netcdf_set_geo_1(mode, _kwargs):
    ds_ori = load_nc_or_xr_source(earthkit_test_data_file("test4.nc"), mode)

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


@pytest.mark.parametrize("mode", ["nc", "xr"])
@pytest.mark.parametrize(
    "_kwargs,shape,grid_spec,area_1",
    [
        (
            {
                "geography.grid_spec": {"grid": [5, 5]},
                "values": np.ones((37, 72)),
            },
            (37, 72),
            {"grid": [5, 5]},
            (90, 0, -90, 360),
        ),
    ],
)
def test_netcdf_set_geo_grid_spec(mode, _kwargs, shape, grid_spec, area_1):
    # the input is a 1/1 grid
    ds_ori = load_nc_or_xr_source(earthkit_test_data_file("test4.nc"), mode)

    assert ds_ori[0].shape == (181, 360)

    f = ds_ori[0].set(**_kwargs)
    assert f.shape == shape
    assert f.get("geography.shape") == shape
    assert f.get("geography.area") == area_1
    assert f.get("geography.grid_spec") == grid_spec
    # assert f.get("geography.grid_type") == grid_type
    assert f.get("geography.latitudes").shape == shape
    assert f.get("geography.longitudes").shape == shape
    assert np.allclose(f.to_numpy(), _kwargs["values"])
