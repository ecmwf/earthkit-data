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
from earthkit.data.testing import earthkit_examples_file
from earthkit.data.testing import earthkit_remote_test_data_file
from earthkit.data.testing import earthkit_test_data_file
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


def test_netcdf_to_points_2():
    ds = from_source("file", earthkit_examples_file("test.nc"))

    assert len(ds) == 2

    import xarray as xr

    xr_ds = xr.open_dataset(earthkit_examples_file("test.nc"))

    for f in ds:
        v = f.to_points()
        assert isinstance(v, dict)

        # x
        assert isinstance(v["x"], np.ndarray)
        assert v["x"].shape == (11, 19)
        for x in v["x"]:
            assert np.allclose(x, np.arange(-27, 45 + 4, 4))

        # y
        assert isinstance(v["y"], np.ndarray)
        assert v["y"].shape == (11, 19)
        for i, y in enumerate(v["y"]):
            assert np.allclose(y, np.ones(19) * (73 - i * 4))

        ref = xr_ds[f.name].sel(latitude=57, longitude=-7).values

        x = 5
        y = 4
        assert np.isclose(f.to_numpy()[y, x], ref)
        assert np.isclose(v["x"][y, x], -7)
        assert np.isclose(v["y"][y, x], 57)


def test_netcdf_to_latlon():
    ds = from_source("file", earthkit_examples_file("test.nc"))

    assert len(ds) == 2

    import xarray as xr

    xr_ds = xr.open_dataset(earthkit_examples_file("test.nc"))

    for f in ds:
        v = f.to_latlon()
        assert isinstance(v, dict)

        # lon
        assert isinstance(v["lon"], np.ndarray)
        assert v["lon"].shape == (11, 19)
        for x in v["lon"]:
            assert np.allclose(x, np.arange(-27, 45 + 4, 4))

        # lat
        assert isinstance(v["lat"], np.ndarray)
        assert v["lat"].shape == (11, 19)
        for i, y in enumerate(v["lat"]):
            assert np.allclose(y, np.ones(19) * (73 - i * 4))

        ref = xr_ds[f.name].sel(latitude=57, longitude=-7).values

        x = 5
        y = 4
        assert np.isclose(f.to_numpy()[y, x], ref)
        assert np.isclose(v["lon"][y, x], -7)
        assert np.isclose(v["lat"][y, x], 57)


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


def test_netcdf_to_points_laea():
    ds = from_source("url", earthkit_remote_test_data_file("examples", "efas.nc"))

    assert len(ds) == 3

    pos = [(0, 0), (0, -1), (-1, 0), (-1, -1)]

    # we must check multiple fields
    for idx in range(2):
        v = ds[idx].to_points()
        assert isinstance(v, dict)

        # lon
        assert isinstance(v["x"], np.ndarray)
        assert v["x"].shape == (950, 1000)

        ref = np.array([2502500.0, 7497500.0, 2502500.0, 7497500.0])
        for i, x in enumerate(pos):
            assert np.isclose(v["x"][x], ref[i]), f"{i=}, {x=}"

        # lat
        assert isinstance(v["y"], np.ndarray)
        assert v["y"].shape == (950, 1000)

        ref = np.array([5497500.0, 5497500.0, 752500.0, 752500.0])
        for i, x in enumerate(pos):
            assert np.isclose(v["y"][x], ref[i]), f"{i=}, {x=}"


def test_netcdf_to_latlon_laea():
    ds = from_source("url", earthkit_remote_test_data_file("examples", "efas.nc"))

    assert len(ds) == 3

    pos = [(0, 0), (0, -1), (-1, 0), (-1, -1)]

    # we must check multiple fields
    for idx in range(2):
        v = ds[idx].to_latlon()
        assert isinstance(v, dict)

        # lon
        assert isinstance(v["lon"], np.ndarray)
        assert v["lon"].shape == (950, 1000)

        ref = np.array(
            [
                -35.034023999999995,
                73.93767587613708,
                -8.229274420493763,
                41.13970495087975,
            ]
        )
        for i, x in enumerate(pos):
            assert np.isclose(v["lon"][x], ref[i]), f"{i=}, {x=}"

        # lat
        assert isinstance(v["lat"], np.ndarray)
        assert v["lat"].shape == (950, 1000)

        ref = np.array(
            [
                66.9821429989222,
                58.24673887576243,
                27.802844211251625,
                23.942342882929605,
            ]
        )
        for i, x in enumerate(pos):
            assert np.isclose(v["lat"][x], ref[i]), f"{i=}, {x=}"


def test_netcdf_forecast_reference_time():
    ds = from_source("url", earthkit_remote_test_data_file("test-data", "fa_ta850.nc"))

    assert len(ds) == 37
    assert ds[0].metadata("valid_datetime") == "2020-01-23T00:00:00"
    assert ds[5].metadata("valid_datetime") == "2020-01-23T05:00:00"


if __name__ == "__main__":
    from earthkit.data.testing import main

    # test_datetime()
    main(__file__)
