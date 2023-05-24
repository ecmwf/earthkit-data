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

from earthkit.data import from_source, transform, translators, wrappers
from earthkit.data.translators import ndarray as ndtranslator
from earthkit.data.translators import string as strtranslator
from earthkit.data.translators import xarray as xrtranslator

LOG = logging.getLogger(__name__)


def test_string_translator():
    # Check that an ndarray translator can be created
    _ndwrapper = wrappers.get_wrapper("Eartha")
    _trans = strtranslator.translator(_ndwrapper, str)
    assert isinstance(_trans, strtranslator.StrTranslator)

    # Check that get_translator method find the right translator
    _trans = translators.get_translator("Eartha", str)
    assert isinstance(_trans, strtranslator.StrTranslator)

    # Check that public API method transforms to correct type (back to original)
    transformed = transform("Eartha", str)
    assert isinstance(transformed, str)


def test_ndarray_translator():
    # Check that an ndarray translator can be created
    _ndwrapper = wrappers.get_wrapper(np.array([1]))
    _trans = ndtranslator.translator(_ndwrapper, np.ndarray)
    assert isinstance(_trans, ndtranslator.NumpyNDArrayTranslator)

    # Check that get_translator method find the right translator
    _trans = translators.get_translator(np.array([1]), np.ndarray)
    assert isinstance(_trans, ndtranslator.NumpyNDArrayTranslator)

    # Check that public API method  transforms to correct type (back to original)
    transformed = transform(np.array([1]), np.ndarray)
    assert isinstance(transformed, np.ndarray)


def test_xr_dataarray_translator():
    # Check that an xr.DataArray translator can be created
    _xrwrapper = wrappers.get_wrapper(xr.DataArray())
    _trans = xrtranslator.translator(_xrwrapper, xr.DataArray)
    assert isinstance(_trans, xrtranslator.XArrayDataArrayTranslator)

    # Check that get_translator method find the right translator
    _trans = translators.get_translator(xr.DataArray(), xr.DataArray)
    assert isinstance(_trans, xrtranslator.XArrayDataArrayTranslator)

    # Check that public API method transforms to correct type (back to original)
    transformed = transform(xr.DataArray(), xr.DataArray)
    assert isinstance(transformed, xr.DataArray)


def test_xr_dataset_translator():
    # Check that an xr.Dataset translator can be created
    _xrwrapper = wrappers.get_wrapper(xr.Dataset())
    _trans = xrtranslator.translator(_xrwrapper, xr.Dataset)
    assert isinstance(_trans, xrtranslator.XArrayDataArrayTranslator)

    # Check that get_translator method find the right translator
    _trans = translators.get_translator(xr.Dataset(), xr.Dataset)
    assert isinstance(_trans, xrtranslator.XArrayDataArrayTranslator)

    # Check that public API method transforms to correct type (back to original)
    transformed = transform(xr.Dataset(), xr.Dataset)
    assert isinstance(transformed, xr.Dataset)


def test_transform_from_grib_file():
    # transform grib-based data object
    f = from_source("file", "tests/data/test_single.grib")

    # np.ndarray
    transformed = transform(f, np.ndarray)
    assert isinstance(transformed, np.ndarray)

    # xr.DataArray
    transformed = transform(f, xr.DataArray)
    assert isinstance(transformed, xr.DataArray)

    # xr.Dataset
    transformed = transform(f, xr.Dataset)
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
