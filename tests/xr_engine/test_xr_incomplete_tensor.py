#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import pandas as pd
import pytest

from earthkit.data import from_source
from earthkit.data.testing import earthkit_remote_test_data_file


@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [False, True])
@pytest.mark.parametrize(
    "kwargs,dim_keys,or_mask_spec,nfields",
    [
        (
            {
                "profile": "mars",
                "time_dim_mode": "raw",
                "decode_times": False,
                "allow_holes": True,
            },
            ["date", "time", "step", "level"],
            [
                {"param": ["r"], "time": [0], "step": [0]},  # masks 12 fields
                {"param": ["u"], "time": [1200], "level": [1000, 300]},  # masks 8 fields
                {
                    "param": ["z"],
                    "time": [1200],
                    "level": [850, 700, 500, 400, 300],
                    "date": [20240604],
                    "step": [6],
                },
                # masks 5 fields
                {
                    "param": ["z"],
                    "time": [1200],
                    "level": [1000, 700, 500, 400, 300],
                    "date": [20240603],
                    "step": [0],
                },
                # masks 5 fields
            ],
            240 - 30,
        ),
    ],
)
def test_xr_incomplete_tensor_holes(lazy_load, kwargs, dim_keys, or_mask_spec, nfields):
    kwargs["lazy_load"] = lazy_load

    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib"))

    md = ds_ek.metadata("param", *dim_keys)
    md_df = pd.DataFrame.from_records(md, columns=["param"] + dim_keys)
    mask = pd.Series(False, index=md_df.index)
    for mask_spec in or_mask_spec:
        _mask = pd.Series(True, index=md_df.index)
        for dim_key, coords in mask_spec.items():
            _mask = _mask & md_df[dim_key].isin(coords)
        mask = mask | _mask

    fl_indices = mask.index[~mask].to_list()
    ds_ek_masked = ds_ek[fl_indices]
    assert len(ds_ek_masked) == nfields

    ds = ds_ek_masked.to_xarray(**kwargs)

    kwargs_with_full_tensor = kwargs.copy()
    kwargs_with_full_tensor["allow_holes"] = False

    for (param, *coords), field, is_masked in zip(md, ds_ek, mask):
        coords_dict = dict(zip(dim_keys, coords))
        da = ds[param].sel(coords_dict, drop=True)
        da2 = field.to_xarray(**kwargs_with_full_tensor)[param]
        if is_masked:
            da2 = da2.where(False)  # makes all values NaN

        # check for dimensions (including their order), coordinates and values
        assert da.equals(da2), f"{param=}, {coords_dict=}, NaN expected: {is_masked}"


@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [False, True])
@pytest.mark.parametrize(
    "kwargs,dim_keys,or_mask_spec,expected_dims_by_param,nfields",
    [
        (
            {
                "profile": "mars",
                "time_dim_mode": "raw",
                "dims_as_attrs": ["step"],
                "decode_times": False,
                "allow_holes": True,
            },
            ["date", "time", "step", "level"],
            [
                {"param": ["t"], "step": [6]},  # masks 24 fields
                {"param": ["r"], "time": [0], "step": [0]},  # masks 12 fields
                {"param": ["u"], "time": [1200], "level": [1000, 300]},  # masks 8 fields
                {
                    "param": ["z"],
                    "time": [1200],
                    "level": [850, 700, 500, 400, 300],
                    "date": [20240604],
                    "step": [6],
                },
                # masks 5 fields
                {
                    "param": ["z"],
                    "time": [1200],
                    "level": [1000, 700, 500, 400, 300],
                    "date": [20240603],
                    "step": [0],
                },
                # masks 5 fields
            ],
            {
                "t": ["date", "time", "level"],
                "r": ["date", "time", "step", "level"],
                "u": ["date", "time", "step", "level"],
                "v": ["date", "time", "step", "level"],
                "z": ["date", "time", "step", "level"],
            },
            240 - 54,
        ),
    ],
)
def test_xr_incomplete_tensor_holes2(
    lazy_load, kwargs, dim_keys, or_mask_spec, expected_dims_by_param, nfields
):
    kwargs["lazy_load"] = lazy_load

    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib"))

    md = ds_ek.metadata("param", *dim_keys)
    md_df = pd.DataFrame.from_records(md, columns=["param"] + dim_keys)
    mask = pd.Series(False, index=md_df.index)
    for mask_spec in or_mask_spec:
        _mask = pd.Series(True, index=md_df.index)
        for dim_key, coords in mask_spec.items():
            _mask = _mask & md_df[dim_key].isin(coords)
        mask = mask | _mask

    fl_indices = mask.index[~mask].to_list()
    ds_ek_masked = ds_ek[fl_indices]
    assert len(ds_ek_masked) == nfields

    ds = ds_ek_masked.to_xarray(**kwargs)
    assert ds["t"].attrs["step_timedelta"] == pd.Timedelta(0, "s")

    kwargs_with_full_tensor = kwargs.copy()
    kwargs_with_full_tensor["allow_holes"] = False

    for param, expected_dims in expected_dims_by_param.items():
        assert set([d for d in ds[param].dims if d not in ["longitude", "latitude"]]) == set(expected_dims)

    for (param, *coords), field, is_masked in zip(md, ds_ek, mask):
        coords_dict = dict(zip(dim_keys, coords))
        if param == "t" and coords_dict["step"] != 0:
            continue
        restricted_coords_dict = {k: c for k, c in coords_dict.items() if k in ds[param].dims}
        da = ds[param].sel(restricted_coords_dict, drop=True)
        da2 = field.to_xarray(**kwargs_with_full_tensor)[param]
        if is_masked:
            da2 = da2.where(False)  # makes all values NaN

        # check for dimensions (including their order), coordinates and values
        assert da.equals(da2), f"{param=}, {coords_dict=}, NaN expected: {is_masked}"


@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [False, True])
@pytest.mark.parametrize(
    "kwargs,dim_keys,or_mask_spec,dropped_coords,nfields",
    [
        (
            {
                "profile": "mars",
                "time_dim_mode": "raw",
                "decode_times": False,
                "allow_holes": True,
            },
            ["date", "time", "step", "level"],
            [
                {"param": ["t", "r", "u", "v", "z"], "level": [500, 700]},  # masks 80 fields
                {"param": ["r"], "level": [300]},  # masks 8 fields
                {"param": ["r"], "time": [0], "step": [0]},  # masks 6 fields (+6 already masked above)
                {"param": ["u"], "time": [1200], "level": [1000, 300]},  # masks 8 fields
                {
                    "param": ["z"],
                    "time": [1200],
                    "level": [850, 700, 500, 400, 300],
                    "date": [20240604],
                    "step": [6],
                },
                # masks 3 fields (+2 already masked above)
                {
                    "param": ["z"],
                    "time": [1200],
                    "level": [1000, 700, 500, 400, 300],
                    "date": [20240603],
                    "step": [0],
                },
                # masks 3 fields (+2 already masked above)
            ],
            {"level": [500, 700]},
            240 - 108,
        ),
    ],
)
def test_xr_incomplete_tensor_coordinates_trimmed_plus_holes(
    lazy_load, kwargs, dim_keys, or_mask_spec, dropped_coords, nfields
):
    kwargs["lazy_load"] = lazy_load

    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine/level/pl.grib"))

    md = ds_ek.metadata("param", *dim_keys)
    md_df = pd.DataFrame.from_records(md, columns=["param"] + dim_keys)
    mask = pd.Series(False, index=md_df.index)
    for mask_spec in or_mask_spec:
        _mask = pd.Series(True, index=md_df.index)
        for dim_key, coords in mask_spec.items():
            _mask = _mask & md_df[dim_key].isin(coords)
        mask = mask | _mask

    fl_indices = mask.index[~mask].to_list()
    ds_ek_masked = ds_ek[fl_indices]
    assert len(ds_ek_masked) == nfields

    ds = ds_ek_masked.to_xarray(**kwargs)

    # check if appropriate coordinates were dropped
    for d, vs in dropped_coords.items():
        for v in vs:
            assert v not in list(ds[d].values)

    kwargs_with_full_tensor = kwargs.copy()
    kwargs_with_full_tensor["allow_holes"] = False

    for (param, *coords), field, is_masked in zip(md, ds_ek, mask):
        coords_dict = dict(zip(dim_keys, coords))
        # if the coords were dropped, skip
        if all(coords_dict[d] in vs for d, vs in dropped_coords.items()):
            continue
        da = ds[param].sel(coords_dict, drop=True)
        da2 = field.to_xarray(**kwargs_with_full_tensor)[param]
        if is_masked:
            da2 = da2.where(False)  # makes all values NaN

        # check for dimensions (including their order), coordinates and values
        assert da.equals(da2), f"{param=}, {coords_dict=}, NaN expected: {is_masked}"


@pytest.mark.cache
@pytest.mark.parametrize("lazy_load", [True, False])
@pytest.mark.parametrize(
    "file,variables,sel_dicts,shapes,isnan_by_var_dicts",
    [
        (
            "regular_ll.grib2",
            ["t", "r"],
            [
                {"step": ["0h"]},
                {"step": "0h", "latitude": [30, 40]},
                {"step": "0h", "latitude": [30, 40], "longitude": slice(10, 100)},
                {"step": "0h", "latitude": 30, "longitude": 20},
                {"step": ["0h"], "latitude": 30, "longitude": 20},
                {"step": ["0h"], "latitude": 30, "longitude": [20, 40, 0]},
            ],
            [(1, 19, 36), (2, 36), (2, 10), (), (1,), (1, 3)],
            [{"t": True, "r": False}] * 6,
        ),
        (
            "reduced_gg_O32.grib2",
            ["t", "q"],
            [
                {"step": "0h"},
                {"step": ["0h"], "values": [0, 1000]},
                {"step": ["0h"], "values": slice(None, 5)},
            ],
            [(5248,), (1, 2), (1, 5)],
            [{"t": True, "q": False}] * 3,
        ),
        (
            "reduced_rotated_gg_subarea_O32.grib1",
            ["t", "r"],
            [
                {"step": ["0h"]},
                {"step": "0h", "values": 224},
                {"step": "0h"},
                {"step": ["0h"], "values": 224},
            ],
            [(1, 225), (), (225,), (1,)],
            [{"t": True, "r": False}] * 4,
        ),
        (
            "healpix_H8_nested.grib2",
            ["t", "r"],
            [{"step": "0h"}, {"step": ["0h"], "values": slice(500, 400, -2)}],
            [(768,), (1, 50)],
            [{"t": True, "r": False}] * 2,
        ),
        (
            "sh_t32.grib1",
            ["t", "r"],
            [{"step": ["0h"]}, {"step": "0h", "values": [1, 2, 10]}],
            [(1, 1122), (3,)],
            [{"t": True, "r": False}] * 2,
        ),
    ],
)
def test_xr_incomplete_tensor_select_hole(lazy_load, file, variables, sel_dicts, shapes, isnan_by_var_dicts):
    kwargs = dict(squeeze=False, allow_holes=True, lazy_load=lazy_load)

    ds_ek = from_source("url", earthkit_remote_test_data_file("xr_engine", "grid", file))

    ds = ds_ek[1:].to_xarray(**kwargs).squeeze()
    assert set(ds) == set(variables)

    for sel_dict, shape, isnan_by_var in zip(sel_dicts, shapes, isnan_by_var_dicts):
        _ds = ds.sel(**sel_dict)
        for v in _ds:
            assert _ds[v].shape == shape
            assert _ds[v].isnull().all() == isnan_by_var[v]
            assert _ds[v].isnull().any() == isnan_by_var[v]
