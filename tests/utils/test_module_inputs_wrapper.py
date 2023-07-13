# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np
import xarray as xr
import pandas as pd

from earthkit.data.utils import module_inputs_wrapper
from earthkit.data import from_source, from_object
from earthkit.data.readers import Reader
from earthkit.data.wrappers import Wrapper

TEST_NP = np.arange(10)
TEST_NP2 = np.arange(10)

TEST_DF = pd.DataFrame({'index': TEST_NP, 'data': TEST_NP2}).set_index('index')

TEST_DA = xr.DataArray(TEST_NP, name='test')
TEST_DA2 = xr.DataArray(TEST_NP2, name='test2')
TEST_DS = TEST_DA.to_dataset()
TEST_DS['test2'] = TEST_DA2

EK_GRIB_READER = from_source("file", "tests/data/test_single.grib")
EK_XARRAY_WRAPPER = from_object(TEST_DS)
EK_NUMPY_WRAPPER = from_object(TEST_NP)


def test_transform_xarray_function_inputs():
    xr_types = (xr.Dataset, xr.DataArray, xr.Variable)
    this_xr_ones_like = module_inputs_wrapper.transform_function_inputs(
        xr.ones_like, kwarg_types = {'other': xr_types}
    )

    # Check EK GribReader object
    ek_reader_result = this_xr_ones_like(EK_GRIB_READER)
    assert isinstance(ek_reader_result, xr_types)
    assert ek_reader_result == xr.ones_like(EK_GRIB_READER.to_xarray())

    # Check EK XarrayWrapper object
    ek_wrapper_result = this_xr_ones_like(EK_XARRAY_WRAPPER)
    assert isinstance(ek_wrapper_result, xr_types)
    assert ek_wrapper_result == xr.ones_like(EK_XARRAY_WRAPPER.data)


def test_transform_numpy_function_inputs():
    this_np_mean = module_inputs_wrapper.transform_function_inputs(
        np.mean, kwarg_types={"a": np.ndarray},
        convert_types=(Reader),
        tranformers={Wrapper: lambda x: x.data}  # Only conver Earthkit.data.Reader and Wrapper types
    )
    # Test with Earthkit.data GribReader object
    assert this_np_mean(EK_GRIB_READER) == np.mean(EK_GRIB_READER.to_numpy())
    assert isinstance(this_np_mean(EK_GRIB_READER), type(np.mean(TEST_NP)))

    # Test with Earthkit.data XarrayWrapper object
    ek_object_result = this_np_mean(EK_XARRAY_WRAPPER)
    assert ek_object_result == np.mean(TEST_DS)
    assert isinstance(ek_object_result, type(EK_XARRAY_WRAPPER.data))

    # Test with xarray.DataArray object
    assert this_np_mean(TEST_DA) == np.mean(TEST_NP)
    assert this_np_mean(TEST_DA) == np.mean(TEST_DA)
    assert isinstance(this_np_mean(TEST_DA), xr.DataArray)
    
    # Test with pandas.DataFrame object
    assert this_np_mean(TEST_DF) == np.mean(TEST_NP)
    assert this_np_mean(TEST_DF) == np.mean(TEST_DF)
    # assert isinstance(this_np_mean(TEST_DF), )


