#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import logging

import numpy as np
import xarray as xr

from earthkit.data import from_object, wrappers
from earthkit.data.wrappers import xarray as xr_wrapper

LOG = logging.getLogger(__name__)


TEST_DA = xr.DataArray(
    np.arange(9).reshape(3, 3), name="test", coords={"x": [1, 2, 3], "y": [1, 2, 3]}
)
TEST_DS = TEST_DA.to_dataset()


def test_dataset_wrapper():
    _wrapper = xr_wrapper.wrapper(TEST_DS)
    assert isinstance(_wrapper, xr_wrapper.XArrayDatasetWrapper)
    _wrapper = wrappers.get_wrapper(TEST_DS)
    assert isinstance(_wrapper, xr_wrapper.XArrayDatasetWrapper)
    _wrapper = from_object(TEST_DS)
    assert isinstance(_wrapper, xr_wrapper.XArrayDatasetWrapper)


def test_dataarray_wrapper():
    _wrapper = xr_wrapper.wrapper(TEST_DA)
    assert isinstance(_wrapper, xr_wrapper.XArrayDataArrayWrapper)
    _wrapper = wrappers.get_wrapper(TEST_DA)
    assert isinstance(_wrapper, xr_wrapper.XArrayDataArrayWrapper)
    _wrapper = from_object(TEST_DA)
    assert isinstance(_wrapper, xr_wrapper.XArrayDataArrayWrapper)


def test_inbuilt_xarray_methods():
    _wrapper = from_object(TEST_DA)
    assert _wrapper.mean().equals(TEST_DA.mean())

    _wrapper = from_object(TEST_DS)
    assert _wrapper.mean().equals(TEST_DS.mean())
