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
import os
import tempfile

import numpy as np
import pandas as pd

from earthkit.data import from_object
from earthkit.data import wrappers
from earthkit.data.wrappers import pandas as pd_wrapper

LOG = logging.getLogger(__name__)

TEST_NP = np.arange(10)
TEST_INDEX = np.array([pd.to_datetime(f"2000-01-{i:02d}") for i in range(1, 11)])

TEST_PDS = pd.Series(TEST_NP, name="data", index=TEST_INDEX)
TEST_PDS_LAT = pd.Series(TEST_NP + 50, name="lat", index=TEST_INDEX)
TEST_PDS_LON = pd.Series(TEST_NP - 10, name="lon", index=TEST_INDEX)

TEST_PDDF = pd.concat([TEST_PDS, TEST_PDS_LAT, TEST_PDS_LON], axis=1)


def test_series_wrapper_detection():
    _wrapper = pd_wrapper.wrapper(TEST_PDS)
    assert isinstance(_wrapper, pd_wrapper.PandasSeriesWrapper)
    _wrapper = wrappers.get_wrapper(TEST_PDS)
    assert isinstance(_wrapper, pd_wrapper.PandasSeriesWrapper)
    _wrapper = from_object(TEST_PDS)
    assert isinstance(_wrapper, pd_wrapper.PandasSeriesWrapper)


def test_series_wrapper_methods():
    _wrapper = from_object(TEST_PDS)

    # Check iterable
    for thing in _wrapper:
        assert thing is not None

    _wrapper.describe()

    pd.testing.assert_series_equal(_wrapper.data, _wrapper.to_pandas())

    assert isinstance(_wrapper.to_numpy(), np.ndarray)

    import xarray as xr

    assert isinstance(_wrapper.to_xarray(), xr.DataArray)

    with tempfile.TemporaryDirectory() as tmp_dir:
        fpath = os.path.join(tmp_dir, "tmp.nc")
        _wrapper.to_netcdf(fpath)


def test_dataframe_wrapper_detection():
    _wrapper = pd_wrapper.wrapper(TEST_PDDF)
    assert isinstance(_wrapper, pd_wrapper.PandasDataFrameWrapper)
    _wrapper = wrappers.get_wrapper(TEST_PDDF)
    assert isinstance(_wrapper, pd_wrapper.PandasDataFrameWrapper)
    _wrapper = from_object(TEST_PDDF)
    assert isinstance(_wrapper, pd_wrapper.PandasDataFrameWrapper)


def test_dataframe_wrapper_methods():
    _wrapper = from_object(TEST_PDDF)

    # Check iterable
    for thing in _wrapper:
        assert thing is not None

    _wrapper.describe()

    pd.testing.assert_frame_equal(_wrapper.data, _wrapper.to_pandas())

    assert isinstance(_wrapper.to_numpy(), np.ndarray)

    import xarray as xr

    assert isinstance(_wrapper.to_xarray(), xr.Dataset)

    with tempfile.TemporaryDirectory() as tmp_dir:
        fpath = os.path.join(tmp_dir, "tmp.nc")
        _wrapper.to_netcdf(fpath)
