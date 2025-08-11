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
import pathlib
import sys

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file

here = os.path.dirname(__file__)
sys.path.insert(0, here)
from xr_engine_fixtures import compare_coords  # noqa: E402
from xr_engine_fixtures import load_grib_data  # noqa: E402


@pytest.mark.cache
@pytest.mark.parametrize("engine", ["earthkit", "cfgrib"])
def test_xr_engine_kwargs_unchanged(engine):
    ds = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl_small.grib"))

    _kwargs = {"squeeze": True}
    res = ds.to_xarray(engine=engine, xarray_open_dataset_kwargs=_kwargs)
    assert res is not None
    assert _kwargs == {"squeeze": True}


@pytest.mark.cache
def test_xr_engine_basic():
    ds = from_source("url", earthkit_remote_test_data_file("test-data", "xr_engine", "level", "pl.grib"))
    res = ds.to_xarray()
    assert res is not None


@pytest.mark.cache
@pytest.mark.parametrize("path_maker", [lambda x: x, lambda x: pathlib.Path(x)])
def test_xr_engine_open_dataset_path(path_maker):

    ds = from_source("sample", "pl.grib")
    path = path_maker(ds.path)

    import xarray as xr

    res = xr.open_dataset(
        path,
        engine="earthkit",
    )
    assert res is not None


@pytest.mark.cache
@pytest.mark.parametrize("api", ["earthkit", "xr"])
def test_xr_engine_detailed_check_1(api):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data", "xr_engine", "level", "pl.grib"))

    if api == "earthkit":
        ds = ds_ek.to_xarray(
            time_dim_mode="raw",
            decode_times=False,
            decode_timedelta=False,
            add_valid_time_coord=False,
            dim_name_from_role_name=False,
        )
    else:
        import xarray as xr

        ds = xr.open_dataset(
            ds_ek.path,
            engine="earthkit",
            time_dim_mode="raw",
            decode_times=False,
            decode_timedelta=False,
            add_valid_time_coord=False,
            dim_name_from_role_name=False,
        )

    assert ds is not None

    # dataset
    lats = np.linspace(90, -90, 19)
    lons = np.linspace(0, 350, 36)
    data_vars = ["r", "t", "u", "v", "z"]

    coords_ref_full = {
        "date": np.array([20240603, 20240604]),
        "time": np.array([0, 1200]),
        "step_timedelta": [0, 6],
        "levelist": np.array([300, 400, 500, 700, 850, 1000]),
        "latitude": lats,
        "longitude": lons,
    }

    dims_ref_full = {
        "date": 2,
        "time": 2,
        "step_timedelta": 2,
        "levelist": 6,
        "latitude": 19,
        "longitude": 36,
    }

    assert len(ds.dims) == len(dims_ref_full)
    compare_coords(ds, coords_ref_full)
    assert [v for v in ds.data_vars] == data_vars

    # data variable
    assert ds["u"].shape == (2, 2, 2, 6, 19, 36)
    assert ds["u"].values.shape == (2, 2, 2, 6, 19, 36)
    assert ds["u"].as_numpy().shape == (2, 2, 2, 6, 19, 36)
    assert ds["u"].to_numpy().shape == (2, 2, 2, 6, 19, 36)
    r = ds["u"]
    compare_coords(r, coords_ref_full)

    # sel() on dataset
    r = ds.sel(date=20240603, time=[0, 1200])
    coords_ref = dict(coords_ref_full)
    coords_ref["date"] = np.array([20240603])
    compare_coords(r, coords_ref)
    assert [v for v in r.data_vars] == data_vars

    # sel() on data variable of filtered dataset
    assert r["u"].shape == (2, 2, 6, 19, 36)
    r1 = r["u"].sel(step_timedelta=6, levelist=[1000, 300])
    assert r1.shape == (2, 2, 19, 36)
    coords_ref["step_timedelta"] = [6]
    coords_ref["levelist"] = np.array([1000, 300])
    compare_coords(r1, coords_ref)

    # isel() on dataset
    r = ds.isel(date=0, time=[0, 1])
    coords_ref = dict(coords_ref_full)
    coords_ref["date"] = np.array([20240603])
    compare_coords(r, coords_ref)
    assert [v for v in r.data_vars] == data_vars

    # isel() on data variable of filtered dataset
    assert r["u"].shape == (2, 2, 6, 19, 36)
    r1 = r["u"].isel(step_timedelta=1, levelist=[0, -1])
    assert r1.shape == (2, 2, 19, 36)
    coords_ref["step_timedelta"] = [6]
    coords_ref["levelist"] = np.array([300, 1000])
    compare_coords(r1, coords_ref)

    # slicing of data variable
    da = ds["u"]

    r = da[:, 0]
    assert r.shape == (2, 2, 6, 19, 36)
    assert r.values.shape == (2, 2, 6, 19, 36)
    assert r.to_numpy().shape == (2, 2, 6, 19, 36)
    dims_ref = dict(dims_ref_full)
    dims_ref.pop("time")
    assert len(r.dims) == len(dims_ref)
    coords_ref = dict(coords_ref_full)
    coords_ref["time"] = np.array([0])
    compare_coords(r, coords_ref)

    r = da[:, 0, :, 3:5]
    assert r.shape == (2, 2, 2, 19, 36)
    assert r.values.shape == (2, 2, 2, 19, 36)
    assert r.to_numpy().shape == (2, 2, 2, 19, 36)
    dims_ref = dict(dims_ref_full)
    dims_ref.pop("time")
    assert len(r.dims) == len(dims_ref)
    coords_ref = dict(coords_ref_full)
    coords_ref["time"] = np.array([0])
    coords_ref["levelist"] = np.array([700, 850])
    compare_coords(r, coords_ref)

    r = da.loc[:, 0, :, [700, 850]]
    assert r.shape == (2, 2, 2, 19, 36)
    assert r.values.shape == (2, 2, 2, 19, 36)
    assert r.to_numpy().shape == (2, 2, 2, 19, 36)
    dims_ref = dict(dims_ref_full)
    dims_ref.pop("time")
    assert len(r.dims) == len(dims_ref)
    coords_ref = dict(coords_ref_full)
    coords_ref["time"] = np.array([0])
    coords_ref["levelist"] = np.array([700, 850])
    compare_coords(r, coords_ref)

    # lat-lon
    da = ds["t"]

    r = da[:, 0, :, 2, 9, 0]
    assert r.shape == (2, 2)
    vals_ref = np.array([[269.00918579, 268.78610229], [268.57771301, 268.08932495]])
    assert np.allclose(r.values, vals_ref)

    r = da[:, 0, :, 2, 9:12, :2]
    assert r.shape == (2, 2, 3, 2)
    vals_ref = np.array(
        [
            [
                [
                    [269.00918579, 269.31680298],
                    [269.70254517, 269.81387329],
                    [267.50527954, 266.83828735],
                ],
                [
                    [268.78610229, 268.80758667],
                    [269.52731323, 269.75680542],
                    [266.61813354, 267.12106323],
                ],
            ],
            [
                [
                    [268.57771301, 269.03767395],
                    [269.33357239, 269.56111145],
                    [264.75154114, 266.55036926],
                ],
                [
                    [268.08932495, 268.35983276],
                    [269.01803589, 269.02389526],
                    [264.29733276, 266.08248901],
                ],
            ],
        ]
    )
    assert np.allclose(r.values, vals_ref)

    r = da.loc[:, 0, :, 500, 0, 0]
    assert r.shape == (2, 2)
    vals_ref = np.array([[269.00918579, 268.78610229], [268.57771301, 268.08932495]])
    assert np.allclose(r.values, vals_ref)


@pytest.mark.cache
@pytest.mark.parametrize("api", ["earthkit", "xr"])
def test_xr_engine_detailed_check_2(api):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data", "xr_engine", "level", "pl.grib"))

    if api == "earthkit":
        ds = ds_ek.to_xarray(
            time_dim_mode="raw",
            decode_times=False,
            decode_timedelta=False,
            add_valid_time_coord=False,
            dim_name_from_role_name=True,
        )
    else:
        import xarray as xr

        ds = xr.open_dataset(
            ds_ek.path,
            engine="earthkit",
            time_dim_mode="raw",
            decode_times=False,
            decode_timedelta=False,
            add_valid_time_coord=False,
            dim_name_from_role_name=True,
        )

    assert ds is not None

    # dataset
    lats = np.linspace(90, -90, 19)
    lons = np.linspace(0, 350, 36)
    data_vars = ["r", "t", "u", "v", "z"]

    coords_ref_full = {
        "date": np.array([20240603, 20240604]),
        "time": np.array([0, 1200]),
        "step": [0, 6],
        "level": np.array([300, 400, 500, 700, 850, 1000]),
        "latitude": lats,
        "longitude": lons,
    }

    dims_ref_full = {
        "date": 2,
        "time": 2,
        "step": 2,
        "level": 6,
        "latitude": 19,
        "longitude": 36,
    }

    assert len(ds.dims) == len(dims_ref_full)
    compare_coords(ds, coords_ref_full)
    assert [v for v in ds.data_vars] == data_vars

    # data variable
    assert ds["u"].shape == (2, 2, 2, 6, 19, 36)
    assert ds["u"].values.shape == (2, 2, 2, 6, 19, 36)
    assert ds["u"].as_numpy().shape == (2, 2, 2, 6, 19, 36)
    assert ds["u"].to_numpy().shape == (2, 2, 2, 6, 19, 36)
    r = ds["u"]
    compare_coords(r, coords_ref_full)

    # sel() on dataset
    r = ds.sel(date=20240603, time=[0, 1200])
    coords_ref = dict(coords_ref_full)
    coords_ref["date"] = np.array([20240603])
    compare_coords(r, coords_ref)
    assert [v for v in r.data_vars] == data_vars

    # sel() on data variable of filtered dataset
    assert r["u"].shape == (2, 2, 6, 19, 36)
    r1 = r["u"].sel(step=6, level=[1000, 300])
    assert r1.shape == (2, 2, 19, 36)
    coords_ref["step"] = [6]
    coords_ref["level"] = np.array([1000, 300])
    compare_coords(r1, coords_ref)

    # isel() on dataset
    r = ds.isel(date=0, time=[0, 1])
    coords_ref = dict(coords_ref_full)
    coords_ref["date"] = np.array([20240603])
    compare_coords(r, coords_ref)
    assert [v for v in r.data_vars] == data_vars

    # isel() on data variable of filtered dataset
    assert r["u"].shape == (2, 2, 6, 19, 36)
    r1 = r["u"].isel(step=1, level=[0, -1])
    assert r1.shape == (2, 2, 19, 36)
    coords_ref["step"] = [6]
    coords_ref["level"] = np.array([300, 1000])
    compare_coords(r1, coords_ref)

    # slicing of data variable
    da = ds["u"]

    r = da[:, 0]
    assert r.shape == (2, 2, 6, 19, 36)
    assert r.values.shape == (2, 2, 6, 19, 36)
    assert r.to_numpy().shape == (2, 2, 6, 19, 36)
    dims_ref = dict(dims_ref_full)
    dims_ref.pop("time")
    assert len(r.dims) == len(dims_ref)
    coords_ref = dict(coords_ref_full)
    coords_ref["time"] = np.array([0])
    compare_coords(r, coords_ref)

    r = da[:, 0, :, 3:5]
    assert r.shape == (2, 2, 2, 19, 36)
    assert r.values.shape == (2, 2, 2, 19, 36)
    assert r.to_numpy().shape == (2, 2, 2, 19, 36)
    dims_ref = dict(dims_ref_full)
    dims_ref.pop("time")
    assert len(r.dims) == len(dims_ref)
    coords_ref = dict(coords_ref_full)
    coords_ref["time"] = np.array([0])
    coords_ref["level"] = np.array([700, 850])
    compare_coords(r, coords_ref)

    r = da.loc[:, 0, :, [700, 850]]
    assert r.shape == (2, 2, 2, 19, 36)
    assert r.values.shape == (2, 2, 2, 19, 36)
    assert r.to_numpy().shape == (2, 2, 2, 19, 36)
    dims_ref = dict(dims_ref_full)
    dims_ref.pop("time")
    assert len(r.dims) == len(dims_ref)
    coords_ref = dict(coords_ref_full)
    coords_ref["time"] = np.array([0])
    coords_ref["level"] = np.array([700, 850])
    compare_coords(r, coords_ref)

    # lat-lon
    da = ds["t"]

    r = da[:, 0, :, 2, 9, 0]
    assert r.shape == (2, 2)
    vals_ref = np.array([[269.00918579, 268.78610229], [268.57771301, 268.08932495]])
    assert np.allclose(r.values, vals_ref)

    r = da[:, 0, :, 2, 9:12, :2]
    assert r.shape == (2, 2, 3, 2)
    vals_ref = np.array(
        [
            [
                [
                    [269.00918579, 269.31680298],
                    [269.70254517, 269.81387329],
                    [267.50527954, 266.83828735],
                ],
                [
                    [268.78610229, 268.80758667],
                    [269.52731323, 269.75680542],
                    [266.61813354, 267.12106323],
                ],
            ],
            [
                [
                    [268.57771301, 269.03767395],
                    [269.33357239, 269.56111145],
                    [264.75154114, 266.55036926],
                ],
                [
                    [268.08932495, 268.35983276],
                    [269.01803589, 269.02389526],
                    [264.29733276, 266.08248901],
                ],
            ],
        ]
    )
    assert np.allclose(r.values, vals_ref)

    r = da.loc[:, 0, :, 500, 0, 0]
    assert r.shape == (2, 2)
    vals_ref = np.array([[269.00918579, 268.78610229], [268.57771301, 268.08932495]])
    assert np.allclose(r.values, vals_ref)


@pytest.mark.cache
@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("lazy_load", [False, True])
@pytest.mark.parametrize("release_source", [False, True])
@pytest.mark.parametrize("direct_backend", [False, True])
def test_xr_engine_detailed_flatten_check_1(stream, lazy_load, release_source, direct_backend):
    filename = "test-data/xr_engine/level/pl.grib"
    ds_ek, ds_ek_ref = load_grib_data(filename, "url", stream=stream)

    kwargs = {
        "xarray_open_dataset_kwargs": {
            "backend_kwargs": {
                "time_dim_mode": "raw",
                "decode_times": False,
                "decode_timedelta": False,
                "flatten_values": True,
                "add_valid_time_coord": False,
                "lazy_load": lazy_load,
                "release_source": release_source,
                "direct_backend": direct_backend,
                "dim_name_from_role_name": False,
            }
        }
    }

    ds = ds_ek.to_xarray(**kwargs)
    assert ds is not None

    # dataset
    ll = ds_ek_ref[0].to_latlon(flatten=True)
    lats = ll["lat"]
    lons = ll["lon"]
    data_vars = ["r", "t", "u", "v", "z"]

    coords_ref_full = {
        "date": np.array([20240603, 20240604]),
        "time": np.array([0, 1200]),
        "step_timedelta": np.array([0, 6]),
        "levelist": np.array([300, 400, 500, 700, 850, 1000]),
        "latitude": lats,
        "longitude": lons,
    }

    dims_ref_full = {
        "date": 2,
        "time": 2,
        "step_timedelta": 2,
        "levelist": 6,
        "values": 684,
    }

    assert len(ds.dims) == len(dims_ref_full)
    assert len(ds.coords) == len(coords_ref_full)
    for k, v in coords_ref_full.items():
        assert np.allclose(ds.coords[k].values, v)
    assert [v for v in ds.data_vars] == data_vars

    # data variable
    assert ds["u"].shape == (2, 2, 2, 6, 684)
    assert ds["u"].values.shape == (2, 2, 2, 6, 684)
    assert ds["u"].as_numpy().shape == (2, 2, 2, 6, 684)
    assert ds["u"].to_numpy().shape == (2, 2, 2, 6, 684)
    r = ds["u"]
    assert len(r.coords) == len(coords_ref_full)
    for k, v in coords_ref_full.items():
        assert np.allclose(r.coords[k].values, v)

    # sel() on dataset
    r = ds.sel(date=20240603, time=[0, 1200])
    coords_ref = dict(coords_ref_full)
    coords_ref["date"] = np.array([20240603])
    assert len(r.coords) == len(coords_ref)
    for k, v in coords_ref.items():
        assert np.allclose(r.coords[k].values, v)
    assert [v for v in r.data_vars] == data_vars

    # sel() on data variable of filtered dataset
    assert r["u"].shape == (2, 2, 6, 684)
    r1 = r["u"].sel(step_timedelta=6, levelist=[1000, 300])
    assert r1.shape == (2, 2, 684)
    coords_ref["step_timedelta"] = np.array([6])
    coords_ref["levelist"] = np.array([1000, 300])
    assert len(r1.coords) == len(coords_ref)
    for k, v in coords_ref.items():
        assert np.allclose(r1.coords[k].values, v)

    # isel() on dataset
    r = ds.isel(date=0, time=[0, 1])
    coords_ref = dict(coords_ref_full)
    coords_ref["date"] = np.array([20240603])
    assert len(r.coords) == len(coords_ref)
    for k, v in coords_ref.items():
        assert np.allclose(r.coords[k].values, v)
    assert [v for v in r.data_vars] == data_vars

    # isel() on data variable of filtered dataset
    assert r["u"].shape == (2, 2, 6, 684)
    r1 = r["u"].isel(step_timedelta=1, levelist=[0, -1])
    assert r1.shape == (2, 2, 684)
    coords_ref["step_timedelta"] = np.array([6])
    coords_ref["levelist"] = np.array([300, 1000])
    assert len(r1.coords) == len(coords_ref)
    for k, v in coords_ref.items():
        assert np.allclose(r1.coords[k].values, v)

    # slicing of data variable
    da = ds["u"]

    r = da[:, 0]
    assert r.shape == (2, 2, 6, 684)
    assert r.values.shape == (2, 2, 6, 684)
    assert r.to_numpy().shape == (2, 2, 6, 684)
    dims_ref = dict(dims_ref_full)
    dims_ref.pop("time")
    assert len(r.dims) == len(dims_ref)
    coords_ref = dict(coords_ref_full)
    coords_ref["time"] = np.array([0])
    for k, v in coords_ref.items():
        assert np.allclose(r.coords[k].values, v)

    r = da[:, 0, :, 3:5]
    assert r.shape == (2, 2, 2, 684)
    assert r.values.shape == (2, 2, 2, 684)
    assert r.to_numpy().shape == (2, 2, 2, 684)
    dims_ref = dict(dims_ref_full)
    dims_ref.pop("time")
    assert len(r.dims) == len(dims_ref)
    coords_ref = dict(coords_ref_full)
    coords_ref["time"] = np.array([0])
    coords_ref["levelist"] = np.array([700, 850])
    for k, v in coords_ref.items():
        assert np.allclose(r.coords[k].values, v)

    r = da.loc[:, 0, :, [700, 850]]
    assert r.shape == (2, 2, 2, 684)
    assert r.values.shape == (2, 2, 2, 684)
    assert r.to_numpy().shape == (2, 2, 2, 684)
    dims_ref = dict(dims_ref_full)
    dims_ref.pop("time")
    assert len(r.dims) == len(dims_ref)
    coords_ref = dict(coords_ref_full)
    coords_ref["time"] = np.array([0])
    coords_ref["levelist"] = np.array([700, 850])
    for k, v in coords_ref.items():
        assert np.allclose(r.coords[k].values, v)

    # level=500, lat=0, lon=0
    da = ds["t"]

    r = da[:, 0, :, 2, 9 * 36 + 0]
    assert r.shape == (2, 2)
    vals_ref = np.array([[269.00918579, 268.78610229], [268.57771301, 268.08932495]])
    assert np.allclose(r.values, vals_ref)

    r = da[:, 0, :, 2, [9 * 36, 10 * 36, 11 * 36]]
    assert r.shape == (2, 2, 3)
    vals_ref = np.array(
        [
            [
                [269.00918579, 269.70254517, 267.50527954],
                [268.78610229, 269.52731323, 266.61813354],
            ],
            [
                [268.57771301, 269.33357239, 264.75154114],
                [268.08932495, 269.01803589, 264.29733276],
            ],
        ]
    )

    v_ek = ds_ek_ref.sel(param="t", time=0, levelist=500).to_numpy(flatten=True)
    assert np.allclose(r.values.flatten(), v_ek[:, [9 * 36, 10 * 36, 11 * 36]].flatten())
    assert np.allclose(r.values, vals_ref)

    r = da.loc[:, 0, :, 500, 9 * 36 + 0]
    assert r.shape == (2, 2)
    vals_ref = np.array([[269.00918579, 268.78610229], [268.57771301, 268.08932495]])
    assert np.allclose(r.values, vals_ref)


@pytest.mark.cache
@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("lazy_load", [False, True])
@pytest.mark.parametrize("release_source", [False, True])
@pytest.mark.parametrize("direct_backend", [False, True])
def test_xr_engine_detailed_flatten_check_2(stream, lazy_load, release_source, direct_backend):
    filename = "test-data/xr_engine/level/pl.grib"
    ds_ek, ds_ek_ref = load_grib_data(filename, "url", stream=stream)

    kwargs = {
        "xarray_open_dataset_kwargs": {
            "backend_kwargs": {
                "time_dim_mode": "raw",
                "decode_times": False,
                "decode_timedelta": False,
                "flatten_values": True,
                "add_valid_time_coord": False,
                "lazy_load": lazy_load,
                "release_source": release_source,
                "direct_backend": direct_backend,
                "dim_name_from_role_name": True,
            }
        }
    }

    ds = ds_ek.to_xarray(**kwargs)
    assert ds is not None

    # dataset
    ll = ds_ek_ref[0].to_latlon(flatten=True)
    lats = ll["lat"]
    lons = ll["lon"]
    data_vars = ["r", "t", "u", "v", "z"]

    coords_ref_full = {
        "date": np.array([20240603, 20240604]),
        "time": np.array([0, 1200]),
        "step": np.array([0, 6]),
        "level": np.array([300, 400, 500, 700, 850, 1000]),
        "latitude": lats,
        "longitude": lons,
    }

    dims_ref_full = {
        "date": 2,
        "time": 2,
        "step": 2,
        "level": 6,
        "values": 684,
    }

    assert len(ds.dims) == len(dims_ref_full)
    compare_coords(ds, coords_ref_full)
    assert [v for v in ds.data_vars] == data_vars

    # data variable
    assert ds["u"].shape == (2, 2, 2, 6, 684)
    assert ds["u"].values.shape == (2, 2, 2, 6, 684)
    assert ds["u"].as_numpy().shape == (2, 2, 2, 6, 684)
    assert ds["u"].to_numpy().shape == (2, 2, 2, 6, 684)
    r = ds["u"]
    compare_coords(r, coords_ref_full)

    # sel() on dataset
    r = ds.sel(date=20240603, time=[0, 1200])
    coords_ref = dict(coords_ref_full)
    coords_ref["date"] = np.array([20240603])
    compare_coords(r, coords_ref)
    assert [v for v in r.data_vars] == data_vars

    # sel() on data variable of filtered dataset
    assert r["u"].shape == (2, 2, 6, 684)
    r1 = r["u"].sel(step=6, level=[1000, 300])
    assert r1.shape == (2, 2, 684)
    coords_ref["step"] = np.array([6])
    coords_ref["level"] = np.array([1000, 300])
    compare_coords(r1, coords_ref)

    # isel() on dataset
    r = ds.isel(date=0, time=[0, 1])
    coords_ref = dict(coords_ref_full)
    coords_ref["date"] = np.array([20240603])
    compare_coords(r, coords_ref)
    assert [v for v in r.data_vars] == data_vars

    # isel() on data variable of filtered dataset
    assert r["u"].shape == (2, 2, 6, 684)
    r1 = r["u"].isel(step=1, level=[0, -1])
    assert r1.shape == (2, 2, 684)
    coords_ref["step"] = np.array([6])
    coords_ref["level"] = np.array([300, 1000])
    compare_coords(r1, coords_ref)

    # slicing of data variable
    da = ds["u"]

    r = da[:, 0]
    assert r.shape == (2, 2, 6, 684)
    assert r.values.shape == (2, 2, 6, 684)
    assert r.to_numpy().shape == (2, 2, 6, 684)
    dims_ref = dict(dims_ref_full)
    dims_ref.pop("time")
    assert len(r.dims) == len(dims_ref)
    coords_ref = dict(coords_ref_full)
    coords_ref["time"] = np.array([0])
    compare_coords(r, coords_ref)

    r = da[:, 0, :, 3:5]
    assert r.shape == (2, 2, 2, 684)
    assert r.values.shape == (2, 2, 2, 684)
    assert r.to_numpy().shape == (2, 2, 2, 684)
    dims_ref = dict(dims_ref_full)
    dims_ref.pop("time")
    assert len(r.dims) == len(dims_ref)
    coords_ref = dict(coords_ref_full)
    coords_ref["time"] = np.array([0])
    coords_ref["level"] = np.array([700, 850])
    compare_coords(r, coords_ref)

    r = da.loc[:, 0, :, [700, 850]]
    assert r.shape == (2, 2, 2, 684)
    assert r.values.shape == (2, 2, 2, 684)
    assert r.to_numpy().shape == (2, 2, 2, 684)
    dims_ref = dict(dims_ref_full)
    dims_ref.pop("time")
    assert len(r.dims) == len(dims_ref)
    coords_ref = dict(coords_ref_full)
    coords_ref["time"] = np.array([0])
    coords_ref["level"] = np.array([700, 850])
    compare_coords(r, coords_ref)

    # level=500, lat=0, lon=0
    da = ds["t"]

    r = da[:, 0, :, 2, 9 * 36 + 0]
    assert r.shape == (2, 2)
    vals_ref = np.array([[269.00918579, 268.78610229], [268.57771301, 268.08932495]])
    assert np.allclose(r.values, vals_ref)

    r = da[:, 0, :, 2, [9 * 36, 10 * 36, 11 * 36]]
    assert r.shape == (2, 2, 3)
    vals_ref = np.array(
        [
            [
                [269.00918579, 269.70254517, 267.50527954],
                [268.78610229, 269.52731323, 266.61813354],
            ],
            [
                [268.57771301, 269.33357239, 264.75154114],
                [268.08932495, 269.01803589, 264.29733276],
            ],
        ]
    )

    v_ek = ds_ek_ref.sel(param="t", time=0, levelist=500).to_numpy(flatten=True)
    assert np.allclose(r.values.flatten(), v_ek[:, [9 * 36, 10 * 36, 11 * 36]].flatten())
    assert np.allclose(r.values, vals_ref)

    r = da.loc[:, 0, :, 500, 9 * 36 + 0]
    assert r.shape == (2, 2)
    vals_ref = np.array([[269.00918579, 268.78610229], [268.57771301, 268.08932495]])
    assert np.allclose(r.values, vals_ref)


@pytest.mark.cache
@pytest.mark.parametrize(
    "kwargs",
    [
        {"split_dims": ["step"]},
        {"split_dims": None},
        {"direct_backend": None},
        {"direct_backend": True},
        {"direct_backend": False},
    ],
)
def test_xr_engine_invalid_kwargs(kwargs):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data", "xr_engine", "level", "pl.grib"))

    import xarray as xr

    with pytest.raises(TypeError):
        xr.open_dataset(
            ds_ek.path,
            engine="earthkit",
            time_dim_mode="raw",
            **kwargs,
        )


@pytest.mark.cache
@pytest.mark.parametrize(
    "dtype,expected_dtype",
    [
        (np.float32, np.float32),
        ("float32", np.float32),
        (np.float64, np.float64),
        ("float64", np.float64),
    ],
)
def test_xr_engine_dtype(dtype, expected_dtype):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl.grib"))

    ds = ds_ek.to_xarray(dtype=dtype)
    assert ds["t"].data.dtype == expected_dtype
    assert ds["t"].values.dtype == expected_dtype


@pytest.mark.cache
def test_xr_engine_single_field():
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl.grib"))
    ds_ek = ds_ek[0]

    ds = ds_ek.to_xarray(
        time_dim_mode="raw",
        decode_times=False,
        decode_timedelta=False,
        add_valid_time_coord=False,
        squeeze=True,
    )

    vals_ref = ds_ek.to_numpy()

    lats = np.linspace(90, -90, 19)
    lons = np.linspace(0, 350, 36)

    var_attrs_ref = {
        "standard_name": "air_temperature",
        "long_name": "Temperature",
        "units": "K",
    }

    global_attrs_ref = {
        "param": "t",
        "paramId": 130,
        "class": "od",
        "stream": "oper",
        "levtype": "pl",
        "type": "fc",
        "expver": "0001",
        "date": 20240603,
        "time": 0,
        "domain": "g",
        "number": 0,
        "levelist": 1000,
        "Conventions": "CF-1.8",
        "institution": "ECMWF",
    }

    assert ds.attrs == global_attrs_ref

    data_vars = ["t"]

    coords_ref_full = {
        "latitude": lats,
        "longitude": lons,
    }

    dims_ref_full = {
        "latitude": 19,
        "longitude": 36,
    }

    assert len(ds.dims) == len(dims_ref_full)
    assert len(ds.coords) == len(coords_ref_full)
    for k, v in coords_ref_full.items():
        assert np.allclose(ds.coords[k].values, v)
    assert [v for v in ds.data_vars] == data_vars

    da = ds["t"]

    for k, v in var_attrs_ref.items():
        assert da.attrs[k] == v

    r = da[:, :]
    r.shape == (19, 36)
    assert np.allclose(r.values, vals_ref)

    r = da[2:4, 6:8]
    assert r.shape == (2, 2)
    assert np.allclose(r.values, vals_ref[2:4, 6:8])

    v = da.sel(latitude=0, longitude=0, method="nearest")
    assert np.allclose(v, vals_ref[9, 0])


@pytest.mark.cache
@pytest.mark.parametrize("add", [False, True])
def test_xr_engine_add_earthkit_attrs_1(add):
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl.grib"))
    ds_ek = ds_ek[0]

    ds = ds_ek.to_xarray(
        time_dim_mode="raw",
        decode_times=False,
        decode_timedelta=False,
        add_valid_time_coord=False,
        add_earthkit_attrs=add,
    )

    if add:
        assert "_earthkit" in ds["t"].attrs
    else:
        assert "_earthkit" not in ds["t"].attrs


@pytest.mark.cache
def test_xr_engine_add_earthkit_attrs_2():
    ds_ek = from_source("url", earthkit_remote_test_data_file("test-data/xr_engine/level/pl.grib"))
    ds_ek = ds_ek[0]

    ds = ds_ek.to_xarray(
        add_earthkit_attrs=False,
    )

    assert ds
    assert "_earthkit" not in ds["t"].attrs
