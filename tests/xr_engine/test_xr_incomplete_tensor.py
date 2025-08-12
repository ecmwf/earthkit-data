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
                "full_tensor_only": False,
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
    kwargs_with_full_tensor["full_tensor_only"] = True

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
                "full_tensor_only": False,
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
    kwargs_with_full_tensor["full_tensor_only"] = True

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
                "full_tensor_only": False,
            },
            ["date", "time", "step", "level"],
            [
                {"param": ["t", "r", "u", "v", "z"], "level": [500, 700]},  # masks 80 fields
                {"param": ["r"], "time": [0], "step": [0]},  # masks 8 fields (+4 already masked above)
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
            240 - 102,
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
    kwargs_with_full_tensor["full_tensor_only"] = True

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
