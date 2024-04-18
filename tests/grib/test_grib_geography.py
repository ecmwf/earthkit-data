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

import numpy as np
import pytest

from earthkit.data.testing import ARRAY_BACKENDS, check_array_type
from earthkit.data.utils import projections

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_TYPES, load_grib_data  # noqa: E402


def check_array(v, shape=None, first=None, last=None, meanv=None, eps=1e-3):
    assert v.shape == shape
    assert np.isclose(v[0], first, eps)
    assert np.isclose(v[-1], last, eps)
    assert np.isclose(v.mean(), meanv, eps)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
@pytest.mark.parametrize("index", [0, None])
def test_grib_to_latlon_single(fl_type, array_backend, index):
    f = load_grib_data("test_single.grib", fl_type, array_backend, folder="data")

    eps = 1e-5
    g = f[index] if index is not None else f
    v = g.to_latlon(flatten=True)
    assert isinstance(v, dict)
    check_array_type(v["lon"], array_backend, dtype="float64")
    check_array_type(v["lat"], array_backend, dtype="float64")
    check_array(
        v["lon"],
        (84,),
        first=0.0,
        last=330.0,
        meanv=165.0,
        eps=eps,
    )
    check_array(
        v["lat"],
        (84,),
        first=90,
        last=-90,
        meanv=0,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
@pytest.mark.parametrize("index", [0, None])
def test_grib_to_latlon_single_shape(fl_type, array_backend, index):
    f = load_grib_data("test_single.grib", fl_type, array_backend, folder="data")

    g = f[index] if index is not None else f
    v = g.to_latlon()
    assert isinstance(v, dict)
    check_array_type(v["lon"], array_backend, dtype="float64")
    check_array_type(v["lat"], array_backend, dtype="float64")

    # x
    assert v["lon"].shape == (7, 12)
    for x in v["lon"]:
        assert np.allclose(x, np.linspace(0, 330, 12))

    # y
    assert v["lat"].shape == (7, 12)
    for i, y in enumerate(v["lat"]):
        assert np.allclose(y, np.ones(12) * (90 - i * 30))


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ["numpy"])
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_grib_to_latlon_multi(fl_type, array_backend, dtype):
    f = load_grib_data("test.grib", fl_type, array_backend)

    v_ref = f[0].to_latlon(flatten=True, dtype=dtype)
    v = f.to_latlon(flatten=True, dtype=dtype)
    assert isinstance(v, dict)
    assert v.keys() == v_ref.keys()

    assert isinstance(v, dict)
    assert np.allclose(v["lat"], v_ref["lat"])
    assert np.allclose(v["lon"], v_ref["lon"])
    assert v["lat"].dtype == dtype
    assert v["lon"].dtype == dtype


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
def test_grib_to_latlon_multi_non_shared_grid(fl_type, array_backend):
    f1 = load_grib_data("test.grib", fl_type, array_backend)
    f2 = load_grib_data("test4.grib", fl_type, array_backend)
    f = f1 + f2

    with pytest.raises(ValueError):
        f.to_latlon()


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
@pytest.mark.parametrize("index", [0, None])
def test_grib_to_points_single(fl_type, array_backend, index):
    f = load_grib_data("test_single.grib", fl_type, array_backend, folder="data")

    eps = 1e-5
    g = f[index] if index is not None else f
    v = g.to_points(flatten=True)
    assert isinstance(v, dict)
    check_array_type(v["x"], array_backend, dtype="float64")
    check_array_type(v["y"], array_backend, dtype="float64")
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


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
def test_grib_to_points_unsupported_grid(fl_type, array_backend):
    f = load_grib_data("mercator.grib", fl_type, array_backend, folder="data")
    with pytest.raises(ValueError):
        f[0].to_points()


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ["numpy"])
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_grib_to_points_multi(fl_type, array_backend, dtype):
    f = load_grib_data("test.grib", fl_type, array_backend)

    v_ref = f[0].to_points(flatten=True, dtype=dtype)
    v = f.to_points(flatten=True, dtype=dtype)
    assert isinstance(v, dict)
    assert v.keys() == v_ref.keys()

    assert isinstance(v, dict)
    assert np.allclose(v["x"], v_ref["x"])
    assert np.allclose(v["y"], v_ref["y"])
    assert v["x"].dtype == dtype
    assert v["y"].dtype == dtype


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
def test_grib_to_points_multi_non_shared_grid(fl_type, array_backend):
    f1 = load_grib_data("test.grib", fl_type, array_backend)
    f2 = load_grib_data("test4.grib", fl_type, array_backend)
    f = f1 + f2

    with pytest.raises(ValueError):
        f.to_points()


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
def test_bbox(fl_type, array_backend):
    ds = load_grib_data("test.grib", fl_type, array_backend)
    bb = ds.bounding_box()
    assert len(bb) == 2
    for b in bb:
        assert b.as_tuple() == (73, -27, 33, 45)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
@pytest.mark.parametrize("index", [0, None])
def test_grib_projection_ll(fl_type, array_backend, index):
    f = load_grib_data("test.grib", fl_type, array_backend)

    if index is not None:
        g = f[index]
    else:
        g = f
    assert isinstance(
        g.projection(), (projections.EquidistantCylindrical, projections.LongLat)
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("array_backend", ARRAY_BACKENDS)
def test_grib_projection_mercator(fl_type, array_backend):
    f = load_grib_data("mercator.grib", fl_type, array_backend, folder="data")
    projection = f[0].projection()
    assert isinstance(projection, projections.Mercator)
    assert projection.parameters == {
        "true_scale_latitude": 20,
        "central_latitude": 0,
        "central_longitude": 0,
        "false_easting": 0,
        "false_northing": 0,
    }
    assert projection.globe == dict()


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
