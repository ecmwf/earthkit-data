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
from earthkit.utils.testing import check_array_type

import earthkit.data
from earthkit.data.testing import NO_GEO
from earthkit.data.testing import check_array
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_test_data_file
from earthkit.data.utils import projections

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from grib_fixtures import FL_NUMPY  # noqa: E402
from grib_fixtures import FL_TYPES  # noqa: E402
from grib_fixtures import load_grib_data  # noqa: E402


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("index", [0, None])
def test_grib_to_latlon_single(fl_type, index):
    f, array_backend = load_grib_data("test_single.grib", fl_type, folder="data")

    eps = 1e-5
    g = f[index] if index is not None else f
    v = g.to_latlon(flatten=True)
    assert isinstance(v, dict)
    check_array_type(v["lon"], array_backend, dtype="float64")
    check_array_type(v["lat"], array_backend, dtype="float64")
    check_array(
        array_backend.to_numpy(v["lon"]),
        (84,),
        first=0.0,
        last=330.0,
        meanv=165.0,
        eps=eps,
    )
    check_array(
        array_backend.to_numpy(v["lat"]),
        (84,),
        first=90,
        last=-90,
        meanv=0,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("index", [0, None])
def test_grib_to_latlon_single_shape(fl_type, index):
    f, array_backend = load_grib_data("test_single.grib", fl_type, folder="data")

    g = f[index] if index is not None else f
    v = g.to_latlon()
    assert isinstance(v, dict)
    check_array_type(v["lon"], array_backend, dtype="float64")
    check_array_type(v["lat"], array_backend, dtype="float64")

    # x
    assert v["lon"].shape == (7, 12)
    for x in v["lon"]:
        assert np.allclose(array_backend.to_numpy(x), np.linspace(0, 330, 12))

    # y
    assert v["lat"].shape == (7, 12)
    for i, y in enumerate(v["lat"]):
        assert np.allclose(array_backend.to_numpy(y), np.ones(12) * (90 - i * 30))


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_grib_to_latlon_multi(fl_type, dtype):
    f, _ = load_grib_data("test.grib", fl_type)

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
def test_grib_to_latlon_multi_non_shared_grid(fl_type):
    f1, _ = load_grib_data("test.grib", fl_type)
    f2, _ = load_grib_data("test4.grib", fl_type)
    f = f1 + f2

    with pytest.raises(ValueError):
        f.to_latlon()


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("index", [0, None])
def test_grib_to_points_single(fl_type, index):
    f, array_backend = load_grib_data("test_single.grib", fl_type, folder="data")

    eps = 1e-5
    g = f[index] if index is not None else f
    v = g.to_points(flatten=True)
    assert isinstance(v, dict)
    check_array_type(v["x"], array_backend, dtype="float64")
    check_array_type(v["y"], array_backend, dtype="float64")
    check_array(
        array_backend.to_numpy(v["x"]),
        (84,),
        first=0.0,
        last=330.0,
        meanv=165.0,
        eps=eps,
    )
    check_array(
        array_backend.to_numpy(v["y"]),
        (84,),
        first=90,
        last=-90,
        meanv=0,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_to_points_unsupported_grid(fl_type):
    f, _ = load_grib_data("mercator.grib", fl_type, folder="data")
    with pytest.raises(ValueError):
        f[0].to_points()


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("dtype", [np.float32, np.float64])
def test_grib_to_points_multi(fl_type, dtype):
    f, _ = load_grib_data("test.grib", fl_type)

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
def test_grib_to_points_multi_non_shared_grid(fl_type):
    f1, _ = load_grib_data("test.grib", fl_type)
    f2, _ = load_grib_data("test4.grib", fl_type)
    f = f1 + f2

    with pytest.raises(ValueError):
        f.to_points()


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_bbox(fl_type):
    ds, _ = load_grib_data("test.grib", fl_type)
    bb = ds.bounding_box()
    assert len(bb) == 2
    for b in bb:
        assert b.as_tuple() == (73, -27, 33, 45)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("index", [0, None])
def test_grib_projection_ll(fl_type, index):
    f, _ = load_grib_data("test.grib", fl_type)

    if index is not None:
        g = f[index]
    else:
        g = f
    assert isinstance(g.projection(), (projections.EquidistantCylindrical, projections.LongLat))


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_projection_mercator(fl_type):
    f, _ = load_grib_data("mercator.grib", fl_type, folder="data")
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


@pytest.mark.parametrize(
    "path,expected_value",
    [
        (earthkit_examples_file("test.grib"), 4.0),
        (earthkit_test_data_file("rgg_small_subarea_cellarea_ref.grib"), "O1280"),
        (earthkit_test_data_file("rotated_N32_subarea.grib"), "N32"),
        (earthkit_test_data_file("rotated_wind_20x20.grib"), 20),
        (earthkit_test_data_file("mercator.grib"), None),
        (earthkit_test_data_file("ll_10_20.grib"), None),
    ],
)
def test_grib_resolution(path, expected_value):
    ds = earthkit.data.from_source("file", path)

    if isinstance(expected_value, str):
        assert ds[0].resolution == expected_value
    elif expected_value is None:
        assert ds[0].resolution is None
    else:
        assert np.isclose(ds[0].resolution, expected_value)


@pytest.mark.parametrize(
    "path,expected_value",
    [
        (earthkit_examples_file("test.grib"), [73.0, -27.0, 33.0, 45.0]),
        (
            earthkit_test_data_file("rgg_small_subarea_cellarea_ref.grib"),
            [89.877, 36.233, 84.815, 46.185],
        ),
        (
            earthkit_test_data_file("rotated_N32_subarea.grib"),
            [26.511, 0.0, -12.558, 39.375],
        ),
        (
            earthkit_test_data_file("rotated_wind_20x20.grib"),
            [80.0, 0.0, -80.0, 340.0],
        ),
        (
            earthkit_test_data_file("mercator.grib"),
            [16.9775, 291.9722, 19.5221, 296.0156],
        ),
    ],
)
def test_grib_mars_area(path, expected_value):
    ds = earthkit.data.from_source("file", path)

    assert np.allclose(np.asarray(ds[0].mars_area), np.asarray(expected_value))


@pytest.mark.parametrize(
    "path,expected_value",
    [
        (earthkit_examples_file("test.grib"), [4.0, 4.0]),
        (
            earthkit_test_data_file("rgg_small_subarea_cellarea_ref.grib"),
            "O1280",
        ),
        (
            earthkit_test_data_file("rotated_N32_subarea.grib"),
            "N32",
        ),
        (
            earthkit_test_data_file("rotated_wind_20x20.grib"),
            [20.0, 20.0],
        ),
        (
            earthkit_test_data_file("mercator.grib"),
            [None, None],
        ),
    ],
)
def test_grib_mars_grid(path, expected_value):
    ds = earthkit.data.from_source("file", path)

    if isinstance(expected_value, str):
        assert ds[0].mars_grid == expected_value
    elif expected_value == [None, None]:
        assert ds[0].mars_grid == expected_value
    else:
        assert np.allclose(np.asarray(ds[0].mars_grid), np.asarray(expected_value))


@pytest.mark.skipif(NO_GEO, reason="No earthkit-geo support")
def test_grib_grid_points_rotated_ll():
    """The"""
    ds = earthkit.data.from_source("file", earthkit_test_data_file("rotated_wind_20x20.grib"))

    # grid points
    res = ds[0].grid_points()
    ref1 = np.array([30.0, 29.351052, 27.504876, 24.734374]), np.array(
        [140.0, 136.09296, 132.770576, 130.469424]
    )

    ref2 = np.array([-17.968188, -14.787578, -12.22927, -10.573044]), np.array(
        [-50.356844, -48.94784, -46.558096, -43.46374]
    )

    assert np.allclose(res[0][:4], ref1[0])
    assert np.allclose(res[1][:4], ref1[1])
    assert np.allclose(res[0][-4:], ref2[0])
    assert np.allclose(res[1][-4:], ref2[1])

    # unrotated grid points
    ds1 = earthkit.data.from_source("file", earthkit_test_data_file("wind_20x20.grib"))

    res = ds[0].grid_points_unrotated()
    ref = ds1[0].grid_points()

    assert np.allclose(res[0], ref[0])
    assert np.allclose(res[1], ref[1])


@pytest.mark.skipif(NO_GEO, reason="No earthkit-geo support")
def test_grib_grid_points_rotated_rgg():
    ds = earthkit.data.from_source("file", earthkit_test_data_file("rotated_N32_subarea.grib"))

    # grid points
    res = ds[0].grid_points()

    # front
    ref1 = np.array([85.489232, 84.81188, 83.171928, 81.086144]), np.array(
        [140.0, 110.950144, 92.460416, 82.07156]
    )

    # back
    ref2 = np.array([44.011184, 42.14694, 40.199948, 38.1796]), np.array(
        [4.244462, 7.003924, 9.575494, 11.973933]
    )

    assert np.allclose(res[0][:4], ref1[0])
    assert np.allclose(res[1][:4], ref1[1])
    assert np.allclose(res[0][-4:], ref2[0])
    assert np.allclose(res[1][-4:], ref2[1])

    # unrotated grid points
    res = ds[0].grid_points_unrotated()

    # front
    ref1 = np.array([26.510768, 26.51076943, 26.5107701, 26.51076846]), np.array(
        [1.28492181e-15, 2.81250046e00, 5.62500163e00, 8.43749805e00]
    )

    # back
    ref2 = np.array([-12.55775535, -12.55775697, -12.55775699, -12.5577565]), np.array(
        [30.93749931, 33.75000128, 36.56250084, 39.37500023]
    )

    assert np.allclose(res[0][:4], ref1[0])
    assert np.allclose(res[1][:4], ref1[1])
    assert np.allclose(res[0][-4:], ref2[0])
    assert np.allclose(res[1][-4:], ref2[1])


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
