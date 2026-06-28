#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data import from_object


def test_hl_xarray_single_core():
    import xarray as xr

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
