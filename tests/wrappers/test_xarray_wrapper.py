#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from earthkit.data import from_object


@pytest.mark.no_eccodes
def test_xr_dataset_wrapper():
    import xarray as xr

    data = xr.Dataset()

    ds = from_object(data)
    assert ds._TYPE_NAME == "xarray.Dataset"
    assert "xarray" in ds.available_types
    assert ds.to_xarray().equals(data)


@pytest.mark.no_eccodes
def test_xr_dataarray_wrapper():
    import xarray as xr

    data = xr.DataArray()

    ds = from_object(data)
    assert ds._TYPE_NAME == "xarray.DataArray"
    assert "xarray" in ds.available_types
    assert ds.to_xarray().equals(data)


@pytest.mark.no_eccodes
def test_xarray_wrapper_to_numpy():
    import xarray as xr

    data_array = xr.DataArray(
        [[1, 2, 3], [4, 5, 6]],
        dims=["x", "y"],
        coords={"x": [1, 2], "y": [3, 4, 5]},
    )
    ds = from_object(data_array)

    arr_2d = ds.to_numpy()
    assert arr_2d.shape == (2, 3)

    arr_1d = ds.to_numpy(flatten=True)
    assert arr_1d.shape == (6,)

    dataset = xr.Dataset({"var": data_array})
    ds = from_object(dataset)
    arr_2d = ds.to_numpy()
    assert arr_2d.shape == (1, 2, 3)
