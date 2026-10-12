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
import xarray as xr

from earthkit.data.field.xarray.geography import XArrayGeography


def test_xarray_geography_rejects_more_than_two_dims_with_actual_shape():
    selection = xr.DataArray(np.zeros((5, 3, 4)), dims=["member", "latitude", "longitude"])
    with pytest.raises(ValueError, match=r"got sizes \(5, 3, 4\)"):
        XArrayGeography(None, selection)


def test_xarray_geography_two_dims():
    selection = xr.DataArray(np.zeros((3, 4)), dims=["latitude", "longitude"])
    assert XArrayGeography(None, selection).shape() == (3, 4)
