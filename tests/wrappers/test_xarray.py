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

from earthkit.data import from_object, wrappers
from earthkit.data.wrappers import xarray as xr_wrapper

LOG = logging.getLogger(__name__)


def test_dataset_wrapper():
    import xarray as xr

    _wrapper = xr_wrapper.wrapper(xr.Dataset())
    assert isinstance(_wrapper, xr_wrapper.XArrayDatasetWrapper)
    _wrapper = wrappers.get_wrapper(xr.Dataset())
    assert isinstance(_wrapper, xr_wrapper.XArrayDatasetWrapper)
    _wrapper = from_object(xr.Dataset())
    assert isinstance(_wrapper, xr_wrapper.XArrayDatasetWrapper)


def test_dataarray_wrapper():
    import xarray as xr

    _wrapper = xr_wrapper.wrapper(xr.DataArray())
    assert isinstance(_wrapper, xr_wrapper.XArrayDataArrayWrapper)
    _wrapper = wrappers.get_wrapper(xr.DataArray())
    assert isinstance(_wrapper, xr_wrapper.XArrayDataArrayWrapper)
    _wrapper = from_object(xr.DataArray())
    assert isinstance(_wrapper, xr_wrapper.XArrayDataArrayWrapper)
