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
from earthkit.utils.array import convert as array_convert
from grib_fixtures import (
    FL_NUMPY,  # noqa: E402
    FL_TYPES,  # noqa: E402
    load_grib_data,  # noqa: E402
)

import earthkit.data
from earthkit.data import concat
from earthkit.data.utils import projections
from earthkit.data.utils.testing import (
    NO_ECCODES_GRID,
    NO_GEO,
    check_array,
    check_array_type,
    earthkit_remote_test_data_file,
    earthkit_test_data_file,
)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("index", [0, None])
def test_grib_latlon_single_1(fl_type, index):
    f, array_backend = load_grib_data("test_single.grib", fl_type, folder="data")

    array_namespace = array_backend.array_namespace
    dtype = "float64"
    if array_backend.dtype is not None:
        dtype = array_backend.dtype

    eps = 1e-5
    g = f[index] if index is not None else f
    lat = g.geography.latitudes().flatten()
    lon = g.geography.longitudes().flatten()

    # TODO: make geography array backend aware
    check_array_type(lat, array_namespace, dtype=dtype)
    check_array_type(lon, array_namespace, dtype=dtype)
    check_array(
        array_convert(lon, array_namespace="numpy"),
        (84,),
        first=0.0,
        last=330.0,
        meanv=165.0,
        eps=eps,
    )
    check_array(
        array_convert(lat, array_namespace="numpy"),
        (84,),
        first=90,
        last=-90,
        meanv=0,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("index", [0, None])
def test_grib_latlon_single_shape(fl_type, index):
    f, array_backend = load_grib_data("test_single.grib", fl_type, folder="data")

    array_namespace = array_backend.array_namespace
    dtype = "float64"
    if array_backend.dtype is not None:
        dtype = array_backend.dtype

    if index is not None:
        g = f[index]
        lat = g.geography.latitudes()
        lon = g.geography.longitudes()
    else:
        g = f
        lat = g.geography.latitudes()
        lon = g.geography.longitudes()

    # TODO: make geography array backend aware
    check_array_type(lon, array_namespace, dtype=dtype)
    check_array_type(lat, array_namespace, dtype=dtype)

    # x
    assert lon.shape == (7, 12)
    for x in lon:
        assert np.allclose(array_convert(x, array_namespace="numpy"), np.linspace(0, 330, 12))

    # y
    assert lon.shape == (7, 12)
    for i, y in enumerate(lat):
        assert np.allclose(array_convert(y, array_namespace="numpy"), np.ones(12) * (90 - i * 30))


@pytest.mark.parametrize("fl_type", FL_NUMPY)
@pytest.mark.parametrize("dtype", [np.float64])
def test_grib_latlon_multi(fl_type, dtype):
    ds, _ = load_grib_data("test.grib", fl_type)

    f = ds[0]
    # flatten=True, dtype=dtype
    lat_ref = f.geography.latitudes()
    lon_ref = f.geography.longitudes()

    # flatten=True, dtype=dtype
    lat = ds.geography.latitudes()
    lon = ds.geography.longitudes()

    assert np.allclose(lat, lat_ref)
    assert np.allclose(lon, lon_ref)
    assert lat.dtype == dtype
    assert lon.dtype == dtype


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_latlon_multi_non_shared_grid(fl_type):
    f1, _ = load_grib_data("test.grib", fl_type)
    f2, _ = load_grib_data("test4.grib", fl_type)
    f = concat(f1, f2)

    with pytest.raises(ValueError):
        f.geography.latitudes()

    with pytest.raises(ValueError):
        f.geography.longitudes()


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("index", [0, None])
def test_grib_points_single_flatten(fl_type, index):
    f, array_backend = load_grib_data("test_single.grib", fl_type, folder="data")

    array_namespace = array_backend.array_namespace
    dtype = "float64"
    if array_backend.dtype is not None:
        dtype = array_backend.dtype

    eps = 1e-5
    if index is not None:
        g = f[index]
        x = g.geography.x().flatten()
        y = g.geography.y().flatten()
    else:
        g = f
        x = g.geography.x().flatten()
        y = g.geography.y().flatten()

    check_array_type(x, array_namespace, dtype=dtype)
    check_array_type(y, array_namespace, dtype=dtype)
    check_array(
        array_convert(x, array_namespace="numpy"),
        (84,),
        first=0.0,
        last=330.0,
        meanv=165.0,
        eps=eps,
    )
    check_array(
        array_convert(y, array_namespace="numpy"),
        (84,),
        first=90,
        last=-90,
        meanv=0,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_NUMPY)
def test_grib_points_multi(fl_type):
    ds, _ = load_grib_data("test.grib", fl_type)
    f = ds[0]

    # flatten=True, dtype=dtype
    x_ref = f.geography.x().flatten()
    y_ref = f.geography.y().flatten()

    # flatten=True, dtype=dtype
    x = ds.geography.x().flatten()
    y = ds.geography.y().flatten()

    assert np.allclose(x, x_ref)
    assert np.allclose(y, y_ref)


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_points_multi_non_shared_grid(fl_type):
    f1, _ = load_grib_data("test.grib", fl_type)
    f2, _ = load_grib_data("test4.grib", fl_type)
    f = concat(f1, f2)

    with pytest.raises(ValueError):
        f.geography.x()

    with pytest.raises(ValueError):
        f.geography.y()


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("index", [0, None])
def test_grib_points_single(fl_type, index):
    f, array_backend = load_grib_data("test_single.grib", fl_type, folder="data")

    array_namespace = array_backend.array_namespace
    dtype = "float64"
    if array_backend.dtype is not None:
        dtype = array_backend.dtype

    eps = 1e-5
    g = f[index] if index is not None else f
    x, y = g.geography.points(flatten=True, dtype=dtype)

    check_array_type(x, array_namespace, dtype=dtype)
    check_array_type(y, array_namespace, dtype=dtype)
    check_array(
        array_convert(x, array_namespace="numpy"),
        (84,),
        first=0.0,
        last=330.0,
        meanv=165.0,
        eps=eps,
    )
    check_array(
        array_convert(y, array_namespace="numpy"),
        (84,),
        first=90,
        last=-90,
        meanv=0,
        eps=eps,
    )


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_points_unsupported_grid(fl_type):
    f, _ = load_grib_data("mercator.grib", fl_type, folder="data")
    with pytest.raises(ValueError):
        f[0].geography.points()


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_bbox(fl_type):
    ds, _ = load_grib_data("test.grib", fl_type)
    print(ds[0].geography.grid_spec())
    bb = ds[0].geography.bounding_box()
    assert bb.as_tuple() == (70, -20, 35, 40)


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_bbox_2(fl_type):
    ds, _ = load_grib_data("test.grib", fl_type)
    bb = ds.geography.bounding_box()
    assert bb.as_tuple() == (70, -20, 35, 40)


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize("index", [0, None])
def test_grib_projection_ll(fl_type, index):
    f, _ = load_grib_data("test.grib", fl_type)

    if index is not None:
        g = f[index]
        proj = g.geography.projection()
    else:
        g = f
        proj = g.geography.projection()
    assert isinstance(proj, (projections.EquidistantCylindrical, projections.LongLat))


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_projection_mercator(fl_type):
    f, _ = load_grib_data("mercator.grib", fl_type, folder="data")
    projection = f[0].geography.projection()
    assert isinstance(projection, projections.Mercator)
    assert projection.parameters == {
        "true_scale_latitude": 20,
        "central_latitude": 0,
        "central_longitude": 0,
        "false_easting": 0,
        "false_northing": 0,
    }
    assert projection.globe == dict()


@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "filename,expected_shape, expected_lat, expected_lon, expected_area",
    [
        (
            "mercator.grib",
            (
                225,
                339,
            ),
            [16.9775, 16.9775, 16.9775, 16.9775],
            [291.9722, 291.9841626, 291.9961252, 292.0080878],
            [16.9775, 291.9722, 19.5221, 296.0156],
        ),
        (
            "rgg_small_subarea_cellarea_ref.grib",
            (340,),
            [89.87647835, 89.80635732, 89.73614327, 89.66589394],
            [45.0, 38.57142857, 45.0, 40.0],
            [89.877, 36.233, 84.815, 46.185],
        ),
        (
            "rotated_N32_subarea.grib",
            (225,),
            [85.489232, 84.81188, 83.171928, 81.086144],
            [140.0, 110.950144, 92.460416, 82.07156],
            [26.511, 0.0, -12.558, 39.375],
        ),
        (
            "rotated_wind_20x20.grib",
            (9, 18),
            [30.0, 29.351052, 27.504876, 24.734374],
            [140.0, 136.09296, 132.770576, 130.469424],
            [80.0, 0.0, -80.0, 340.0],
        ),
        (
            "ll_10_20.grib",
            (
                9,
                36,
            ),
            [80.0, 80.0, 80.0, 80.0],
            [0.0, 10.0, 20.0, 30.0],
            [80.0, 0.0, -80.0, 350.0],
        ),
        (
            "shifted_ll_subarea.grib",
            (11, 19),
            [73.0, 73.0, 73.0, 73.0],
            [-27.0, -23.0, -19.0, -15.0],
            [73, -27, 33, 45],
        ),
        (
            "shifted_ll_3x3_subarea.grib",
            (19, 29),
            [79.0, 79.0, 79.0, 79.0],
            [-25.0, -22.0, -19.0, -16.0],
            [79, -25, 25, 59],
        ),
    ],
)
def test_grib_latlon_various_grids_1(fl_type, filename, expected_shape, expected_lat, expected_lon, expected_area):
    ds, _ = load_grib_data(filename, fl_type, folder="data")

    lat, lon = ds[0].geography.latlons()
    assert lat.shape == expected_shape
    assert lon.shape == expected_shape
    assert np.allclose(lat.flatten()[:4], expected_lat)
    assert np.allclose(lon.flatten()[:4], expected_lon)
    assert np.allclose(np.asarray(ds[0].geography.area()), np.asarray(expected_area))


@pytest.mark.skip(
    "This test is currently failing because the GRIB field geography is not correctly handled in ecCodes."
)
@pytest.mark.parametrize(
    "filename,expected_shape, expected_lat, expected_lon, expected_area",
    [
        (
            "icon_ch1.grib2",
            (1147980,),
            [50.24130630493164, 50.23910903930664, 50.23666763305664, 50.22787857055664],
            [17.710683465003967, 17.689199090003967, 17.702382683753967, 17.704824090003967],
            [50.6, -0.9, 41.9, 17.8],
        ),
        (
            "eORCA025_T.grib",
            (
                1442,
                1207,
            ),
            [-89.5, -89.5, -89.5, -89.5],
            [72.75, 73.0, 73.25, 73.5],
            [90.0, 0.0, -90.0, 360.0],
        ),
    ],
)
def test_grib_latlon_various_grids_2(filename, expected_shape, expected_lat, expected_lon, expected_area):
    fl = earthkit.data.from_source("url", earthkit_remote_test_data_file("xr_engine/grid", filename)).to_fieldlist()

    lat, lon = fl[0].geography.latlons()
    assert lat.shape == expected_shape
    assert lon.shape == expected_shape
    assert np.allclose(lat.flatten()[:4], expected_lat)
    assert np.allclose(lon.flatten()[:4], expected_lon)
    assert np.allclose(np.asarray(fl[0].geography.area()), np.asarray(expected_area))


@pytest.mark.skip(
    "This test is currently failing because the GRIB field geography is handled by ecCodes and not earthkit-geo. "
)
@pytest.mark.skipif(NO_ECCODES_GRID, reason="No eckit-geo support in eccodes")
@pytest.mark.parametrize("fl_type", FL_TYPES)
@pytest.mark.parametrize(
    "filename,shape,grid_spec,area,grid_type",
    [
        (
            "ll_10_20.grib",
            (
                9,
                36,
            ),
            {"grid": "regular_ll"},
            (90.0, 0.0, -90.0, 360.0),
            "regular-ll",
        ),
    ],
)
def test_grib_eckit_grid_object(fl_type, filename, shape, grid_spec, area, grid_type):
    ds, _ = load_grib_data(filename, fl_type, folder="data")
    grid = ds[0].geography.grid()
    assert grid
    assert grid.shape == shape
    assert grid.bounding_box() == area

    # TODO: this does not work in eckit-geo Grid
    # grid.type == grid_type
    assert ds[0].geography.shape() == shape
    assert ds[0].geography.area() == area
    lat, lon = ds[0].geography.latlons()
    assert lat.shape == shape
    assert lon.shape == shape


@pytest.mark.skipif(NO_GEO, reason="No earthkit-geo support")
def test_grib_grid_points_rotated_ll():
    ds = earthkit.data.from_source("file", earthkit_test_data_file("rotated_wind_20x20.grib")).to_fieldlist()

    # grid points
    res = ds[0].geography.grid_points()
    ref1 = np.array([30.0, 29.351052, 27.504876, 24.734374]), np.array([140.0, 136.09296, 132.770576, 130.469424])

    ref2 = (
        np.array([-17.968188, -14.787578, -12.22927, -10.573044]),
        np.array([-50.356844, -48.94784, -46.558096, -43.46374]),
    )

    assert np.allclose(res[0][:4], ref1[0])
    assert np.allclose(res[1][:4], ref1[1])
    assert np.allclose(res[0][-4:], ref2[0])
    assert np.allclose(res[1][-4:], ref2[1])

    # unrotated grid points
    ds1 = earthkit.data.from_source("file", earthkit_test_data_file("wind_20x20.grib")).to_fieldlist()

    res = ds[0].geography.grid_points_unrotated()
    ref = ds1[0].geography.grid_points_unrotated()
    assert np.allclose(res[0], ref[0])
    assert np.allclose(res[1], ref[1])


@pytest.mark.skipif(NO_GEO, reason="No earthkit-geo support")
def test_grib_grid_points_rotated_rgg():
    ds = earthkit.data.from_source("file", earthkit_test_data_file("rotated_N32_subarea.grib")).to_fieldlist()

    # grid points
    res = ds[0].grid_points()

    # front
    ref1 = np.array([85.489232, 84.81188, 83.171928, 81.086144]), np.array([140.0, 110.950144, 92.460416, 82.07156])

    # back
    ref2 = np.array([44.011184, 42.14694, 40.199948, 38.1796]), np.array([4.244462, 7.003924, 9.575494, 11.973933])

    assert np.allclose(res[0][:4], ref1[0])
    assert np.allclose(res[1][:4], ref1[1])
    assert np.allclose(res[0][-4:], ref2[0])
    assert np.allclose(res[1][-4:], ref2[1])

    # unrotated grid points
    res = ds[0].geography.grid_points_unrotated()

    # front
    ref1 = (
        np.array([26.510768, 26.51076943, 26.5107701, 26.51076846]),
        np.array([1.28492181e-15, 2.81250046e00, 5.62500163e00, 8.43749805e00]),
    )

    # back
    ref2 = (
        np.array([-12.55775535, -12.55775697, -12.55775699, -12.5577565]),
        np.array([30.93749931, 33.75000128, 36.56250084, 39.37500023]),
    )

    assert np.allclose(res[0][:4], ref1[0])
    assert np.allclose(res[1][:4], ref1[1])
    assert np.allclose(res[0][-4:], ref2[0])
    assert np.allclose(res[1][-4:], ref2[1])


@pytest.mark.parametrize("fl_type", FL_TYPES)
def test_grib_healpix_grid(fl_type):
    ds, _ = load_grib_data("healpix_H8.grib2", fl_type, folder="data")

    f = ds[0]
    assert f.geography.shape() == (768,)
    r = f.geography.to_dict()
    assert r["shape"] == (768,)
    assert r["grid_type"] == "healpix"


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main()
