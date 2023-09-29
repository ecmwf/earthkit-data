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
from earthkit.data.testing import (
    earthkit_examples_file,
    earthkit_remote_test_data_file,
    earthkit_test_data_file,
)
from earthkit.data.utils import projections


def check_array(v, shape=None, first=None, last=None, meanv=None, eps=1e-3):
    assert v.shape == shape
    assert np.isclose(v[0], first, eps)
    assert np.isclose(v[-1], last, eps)
    assert np.isclose(v.mean(), meanv, eps)


@pytest.mark.parametrize(
    "dtype,expected_dtype",
    [(None, np.float64), (np.float32, np.float32), (np.float64, np.float64)],
)
def test_netcdf_to_points_1(dtype, expected_dtype):
    ds = from_source("file", earthkit_test_data_file("test_single.nc"))

    eps = 1e-5
    v = ds[0].to_points(flatten=True, dtype=dtype)
    assert isinstance(v, dict)
    assert isinstance(v["x"], np.ndarray)
    assert isinstance(v["y"], np.ndarray)
    assert v["x"].dtype == expected_dtype
    assert v["y"].dtype == expected_dtype
    check_array(
        v["x"],
        (84,),
        first=0.0,
        last=330.0,
        meanv=165.0,
        eps=eps,
    )
    check_array(
        v["y"],
        (84,),
        first=90,
        last=-90,
        meanv=0,
        eps=eps,
    )


def test_bbox():
    ds = from_source("file", earthkit_examples_file("test.nc"))
    bb = ds.bounding_box()
    assert len(bb) == 2
    for b in bb:
        assert b.as_tuple() == (73, -27, 33, 45)


def test_netcdf_proj_string_non_cf():
    f = from_source("file", earthkit_examples_file("test.nc"))
    with pytest.raises(AttributeError):
        f[0].projection()


def test_netcdf_projection_laea():
    f = from_source("url", earthkit_remote_test_data_file("examples", "efas.nc"))
    projection = f[0].projection()
    assert isinstance(projection, projections.LambertAzimuthalEqualArea)
    assert projection.parameters == {
        "central_latitude": 52.0,
        "central_longitude": 10.0,
        "false_northing": 3210000.0,
        "false_easting": 4321000.0,
    }
    assert projection.globe == {
        "ellipse": "GRS80",
    }


def test_netcdf_proj_string_laea():
    f = from_source("url", earthkit_remote_test_data_file("examples", "efas.nc"))
    r = f[0].projection()
    assert (
        r.to_proj_string()
        == "+proj=laea +lat_0=52 +lon_0=10 +x_0=4321000 +y_0=3210000 +ellps=GRS80 +units=m +no_defs"
    )


if __name__ == "__main__":
    from earthkit.data.testing import main

    # test_datetime()
    main(__file__)
