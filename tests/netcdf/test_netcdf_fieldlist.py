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

import earthkit.data
from earthkit.data.testing import earthkit_remote_test_data_file


def test_netcdf_fieldlist_string_coord():
    import xarray as xr

    a = xr.DataArray(
        [
            [[11, 12, 13], [21, 22, 23], [31, 32, 33]],
            [[14, 15, 16], [24, 25, 26], [34, 35, 36]],
        ],
        coords={"level": ["500", "700"], "x": [1, 2, 3], "y": [4, 5, 6]},
        name="dummyvar",
    )

    # sanity check
    assert np.allclose(a.sel(level="500", x=2).values, np.array([21, 22, 23]))

    ds = earthkit.data.from_object(a)

    assert ds
    assert len(ds) == 2
    assert ds.metadata("level") == ["500", "700"]

    x_ref = np.array([[1, 1, 1], [2, 2, 2], [3, 3, 3]])
    y_ref = np.array([[4, 5, 6], [4, 5, 6], [4, 5, 6]])
    assert np.allclose(ds[0].to_points()["x"], x_ref)
    assert np.allclose(ds[0].to_points()["y"], y_ref)


def test_netcdf_fieldlist_bounds():
    """Check if having non string values in bounds does not cause a crash"""
    import xarray as xr

    a = xr.DataArray(
        [
            [[11, 12, 13], [21, 22, 23], [31, 32, 33]],
            [[14, 15, 16], [24, 25, 26], [34, 35, 36]],
        ],
        coords={"level": [0, 0], "x": [1, 2, 3], "y": [4, 5, 6]},
        attrs={"bounds": [1, 2, 3]},
        name="dummyvar",
    )

    ds = earthkit.data.from_object(a)
    assert ds
    assert len(ds) == 2


def test_netcdf_fieldlist_ctime():
    ds = earthkit.data.from_source(
        "url",
        earthkit_remote_test_data_file("test-data", "zgrid_rhgmet_metop_200701_R_2305_0010.nc"),
    )

    assert len(ds) == 1506
    assert ds[0].metadata("valid_datetime") == "2007-01-16T00:00:00"
    assert ds[5].metadata("valid_datetime") == "2007-01-16T00:00:00"


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
