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

from earthkit.data import from_object
from earthkit.data import from_source
from earthkit.data import transform
from earthkit.data.utils.testing import earthkit_test_data_file

LOG = logging.getLogger(__name__)


def test_xr_dataarray_translator():
    val = xr.DataArray()
    ds = from_object(val)

    assert transform(val, xr.DataArray).equals(val)
    assert transform(ds, xr.DataArray).equals(val)

    assert isinstance(transform(val, xr.DataArray), xr.DataArray)
    assert isinstance(transform(ds, xr.DataArray), xr.DataArray)


def test_xr_dataset_translator():
    val = xr.Dataset()
    ds = from_object(val)

    assert transform(val, xr.Dataset).equals(val)
    assert transform(ds, xr.Dataset).equals(val)

    assert isinstance(transform(val, xr.Dataset), xr.Dataset)
    assert isinstance(transform(ds, xr.Dataset), xr.Dataset)


def test_transform_from_grib_file():
    # transform grib-based data object
    ds = from_source("file", earthkit_test_data_file("test_single.grib")).to_fieldlist()

    # np.ndarray
    transformed = transform(ds, np.ndarray)
    assert isinstance(transformed, np.ndarray)

    # xr.DataArray
    transformed = transform(ds, xr.DataArray)
    assert isinstance(transformed, xr.DataArray)

    # xr.Dataset
    transformed = transform(ds, xr.Dataset)
    assert isinstance(transformed, xr.Dataset)


def test_transform_from_xarray_object():
    # transform grib-based data object
    da = xr.DataArray([])
    ds = xr.Dataset({"a": da})

    # da to np.ndarray
    transformed = transform(da, np.ndarray)
    assert isinstance(transformed, np.ndarray)

    # ds to xr.DataArray
    transformed = transform(ds, xr.DataArray)
    assert isinstance(transformed, xr.DataArray)

    # ds to np.ndarray
    transformed = transform(ds, np.ndarray)
    assert isinstance(transformed, np.ndarray)
