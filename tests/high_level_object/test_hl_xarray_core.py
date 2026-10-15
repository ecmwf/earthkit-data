#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import xarray as xr

from earthkit.data import concat, from_object


def test_hl_xarray_single_core():
    data_array = xr.DataArray(
        [[1, 2, 3], [4, 5, 6]],
        dims=["x", "y"],
        coords={"x": [1, 2], "y": [3, 4, 5]},
    )
    ds = from_object(data_array)
    assert ds._TYPE_NAME == "xarray.DataArray"
    assert "xarray" in ds.available_types

    da = ds.to_xarray()
    assert da.equals(data_array)

    dataset = xr.Dataset({"var": data_array})
    ds = from_object(dataset)
    assert ds._TYPE_NAME == "xarray.Dataset"
    assert "xarray" in ds.available_types
    assert ds.to_xarray().equals(dataset)

    fl = ds.to_fieldlist()
    assert len(fl) == 1
    assert fl[0].shape == (2, 3)


def test_hl_xarray_multi_core_1():
    data_array_1 = xr.DataArray(
        [[1, 2, 3], [4, 5, 6]],
        dims=["x", "y"],
        coords={"x": [1, 2], "y": [3, 4, 5]},
    )
    dataset_1 = xr.Dataset({"a": data_array_1})

    data_array_2 = xr.DataArray(
        [[2, 2, 3], [4, 5, 6]],
        dims=["x", "y"],
        coords={"x": [1, 2], "y": [3, 4, 5]},
    )
    dataset_2 = xr.Dataset({"b": data_array_2})

    d1 = from_object(dataset_1)
    d2 = from_object(dataset_2)

    assert d1._TYPE_NAME == "xarray.Dataset"
    assert "xarray" in d1.available_types
    assert d1.to_xarray().equals(dataset_1)

    assert d2._TYPE_NAME == "xarray.Dataset"
    assert "xarray" in d2.available_types
    assert d2.to_xarray().equals(dataset_2)

    d = concat(d1, d2)
    assert d._TYPE_NAME == "Multi"
    assert "xarray" in d.available_types
    ds = d.to_xarray()

    ds_ref = xr.merge([dataset_1, dataset_2])
    assert ds.equals(ds_ref)


def test_hl_xarray_multi_core_2():
    data_array_1 = xr.DataArray(
        [[1, 2, 3], [4, 5, 6]],
        dims=["x", "y"],
        coords={"x": [1, 2], "y": [3, 4, 5]},
    )
    dataset_1 = xr.Dataset({"a": data_array_1})

    data_array_2 = xr.DataArray(
        [[2, 2, 3], [4, 5, 6]],
        dims=["x", "y"],
        coords={"x": [1, 2], "y": [3, 4, 5]},
    )
    dataset_2 = xr.Dataset({"b": data_array_2})

    data_array_3 = xr.DataArray(
        [[1, 2, 3], [4, 5, 6]],
        dims=["x", "y"],
        coords={"x": [1, 2], "y": [3, 4, 5]},
    )
    dataset_3 = xr.Dataset({"c": data_array_3})

    data_array_4 = xr.DataArray(
        [[2, 2, 3], [4, 5, 6]],
        dims=["x", "y"],
        coords={"x": [1, 2], "y": [3, 4, 5]},
    )
    dataset_4 = xr.Dataset({"d": data_array_4})

    d1 = from_object(dataset_1)
    d2 = from_object(dataset_2)
    d3 = from_object(dataset_3)
    d4 = from_object(dataset_4)

    da = concat(d1, d2)
    db = concat(d3, d4)

    d = concat(da, db)

    assert d._TYPE_NAME == "Multi"
    assert "xarray" in d.available_types
    ds = d.to_xarray()

    ds_ref = xr.merge([dataset_1, dataset_2, dataset_3, dataset_4])
    assert ds.equals(ds_ref)
