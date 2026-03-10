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
import pandas as pd

from earthkit.data import from_object

LOG = logging.getLogger(__name__)

TEST_NP = np.arange(10)
TEST_INDEX = np.array([pd.to_datetime(f"2000-01-{i:02d}") for i in range(1, 11)])

TEST_PDS = pd.Series(TEST_NP, name="data", index=TEST_INDEX)
TEST_PDS_LAT = pd.Series(TEST_NP + 50, name="lat", index=TEST_INDEX)
TEST_PDS_LON = pd.Series(TEST_NP - 10, name="lon", index=TEST_INDEX)

TEST_PDDF = pd.concat([TEST_PDS, TEST_PDS_LAT, TEST_PDS_LON], axis=1)


def test_pandas_series_wrapper_detection():
    ds = from_object(TEST_PDS)
    assert ds._TYPE_NAME == "pandas.Series"
    assert "pandas" in ds.available_types
    assert ds.to_pandas().equals(TEST_PDS)


def test_series_wrapper_methods():
    ds = from_object(TEST_PDS)

    assert isinstance(ds.to_numpy(), np.ndarray)

    import xarray as xr

    assert isinstance(ds.to_xarray(), xr.DataArray)


def test_pandas_dataframe_wrapper_detection():

    ds = from_object(TEST_PDDF)
    assert ds._TYPE_NAME == "pandas.DataFrame"
    assert "pandas" in ds.available_types
    assert ds.to_pandas().equals(TEST_PDDF)


def test_pandas_dataframe_wrapper_methods():
    ds = from_object(TEST_PDDF)

    assert isinstance(ds.to_numpy(), np.ndarray)

    import xarray as xr

    assert isinstance(ds.to_xarray(), xr.Dataset)
