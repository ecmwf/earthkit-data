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

import numpy as np
import pytest

from earthkit.data import from_source

SAMPLE_DATA_FOLDER = "~/git/cfgrib/tests/sample-data"
SAMPLE_DATA_FOLDER = "/Users/cgr/metview/python_test/earthkit_data/engine"


@pytest.mark.parametrize(
    "grib_name",
    [
        "pl_regular_ll",
        # "era5-levels-members",
        # "fields_with_missing_values",
        # "lambert_grid",
        # "reduced_gg",
        # "regular_gg_sfc",
        # "regular_gg_pl",
        # "regular_gg_ml",
        # "regular_gg_ml_g2",
        # "regular_ll_sfc",
        # "regular_ll_msl",
        # "scanning_mode_64",
        # "single_gridpoint",
        # "spherical_harmonics",
        # "t_analysis_and_fc_0",
    ],
)
def test_xr_engine(grib_name):
    pass
    grib_path = os.path.join(SAMPLE_DATA_FOLDER, grib_name + ".grib")
    print(f"Reading {grib_path}")
    ds = from_source("file", grib_path)
    res = ds.to_xarray(_legacy=False)
    assert res is not None


def test_xr_engine_detailed_check():
    grib_path = os.path.join(SAMPLE_DATA_FOLDER, "pl_regular_ll.grib")

    ds_ek = from_source("file", grib_path)
    ds = ds_ek.to_xarray()
    assert ds is not None

    # dataset
    lats = np.linspace(90, -90, 19)
    lons = np.linspace(0, 350, 36)
    data_vars = ["r", "t", "u", "v", "z"]

    coords_ref_full = {
        "date": np.array([20240603, 20240604]),
        "time": np.array([0, 1200]),
        "step": np.array([0, 6]),
        "levelist": np.array([300, 400, 500, 700, 850, 1000]),
        "latitude": lats,
        "longitude": lons,
    }

    dims_ref_full = {
        "date": 2,
        "time": 2,
        "step": 2,
        "levelist": 6,
        "latitude": 19,
        "longitude": 36,
    }

    assert len(ds.dims) == len(dims_ref_full)
    assert len(ds.coords) == len(coords_ref_full)
    for k, v in coords_ref_full.items():
        assert np.allclose(ds.coords[k].values, v)
    assert [v for v in ds.data_vars] == data_vars

    # data variable
    assert ds["u"].shape == (2, 2, 2, 6, 19, 36)
    assert ds["u"].values.shape == (2, 2, 2, 6, 19, 36)
    assert ds["u"].as_numpy().shape == (2, 2, 2, 6, 19, 36)
    assert ds["u"].to_numpy().shape == (2, 2, 2, 6, 19, 36)
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
    assert r["u"].shape == (2, 2, 6, 19, 36)
    r1 = r["u"].sel(step=6, levelist=[1000, 300])
    assert r1.shape == (2, 2, 19, 36)
    coords_ref["step"] = np.array([6])
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
    assert r["u"].shape == (2, 2, 6, 19, 36)
    r1 = r["u"].isel(step=1, levelist=[0, -1])
    assert r1.shape == (2, 2, 19, 36)
    coords_ref["step"] = np.array([6])
    coords_ref["levelist"] = np.array([300, 1000])
    assert len(r1.coords) == len(coords_ref)
    for k, v in coords_ref.items():
        assert np.allclose(r1.coords[k].values, v)

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
    for k, v in coords_ref.items():
        assert np.allclose(r.coords[k].values, v)

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
    for k, v in coords_ref.items():
        assert np.allclose(r.coords[k].values, v)

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
    for k, v in coords_ref.items():
        assert np.allclose(r.coords[k].values, v)

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


def test_xr_engine_detailed_flatten_check():
    grib_path = os.path.join(SAMPLE_DATA_FOLDER, "pl_regular_ll.grib")

    ds_ek = from_source("file", grib_path)

    kwargs = {
        "xarray_open_dataset_kwargs": {
            "backend_kwargs": {
                "flatten_values": True,
            }
        }
    }

    ds = ds_ek.to_xarray(**kwargs)
    assert ds is not None

    # dataset
    ll = ds_ek[0].to_latlon(flatten=True)
    lats = ll["lat"]
    lons = ll["lon"]
    data_vars = ["r", "t", "u", "v", "z"]

    coords_ref_full = {
        "date": np.array([20240603, 20240604]),
        "time": np.array([0, 1200]),
        "step": np.array([0, 6]),
        "levelist": np.array([300, 400, 500, 700, 850, 1000]),
        "latitude": lats,
        "longitude": lons,
    }

    dims_ref_full = {
        "date": 2,
        "time": 2,
        "step": 2,
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
    r1 = r["u"].sel(step=6, levelist=[1000, 300])
    assert r1.shape == (2, 2, 684)
    coords_ref["step"] = np.array([6])
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
    r1 = r["u"].isel(step=1, levelist=[0, -1])
    assert r1.shape == (2, 2, 684)
    coords_ref["step"] = np.array([6])
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

    # lat-lon
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

    v_ek = ds_ek.sel(param="t", time=0, levelist=500).to_numpy(flatten=True)
    assert np.allclose(r.values.flatten(), v_ek[:, [9 * 36, 10 * 36, 11 * 36]].flatten())
    assert np.allclose(r.values, vals_ref)

    r = da.loc[:, 0, :, 500, 9 * 36 + 0]
    assert r.shape == (2, 2)
    vals_ref = np.array([[269.00918579, 268.78610229], [268.57771301, 268.08932495]])
    assert np.allclose(r.values, vals_ref)
