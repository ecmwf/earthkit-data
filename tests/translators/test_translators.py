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

from earthkit.data import translators, wrappers
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

    # Check that Transltor transforms to correct type
    transformed = translators.transform("Eartha", str)
    assert isinstance(transformed, str)


def test_ndarray_translator():
    import numpy as np

    # Check that an ndarray translator can be created
    _ndwrapper = wrappers.get_wrapper(np.array([1]))
    _trans = ndtranslator.translator(_ndwrapper, np.ndarray)
    assert isinstance(_trans, ndtranslator.NumpyNDArrayTranslator)

    # Check that get_translator method find the right translator
    _trans = translators.get_translator(np.array([1]), np.ndarray)
    assert isinstance(_trans, ndtranslator.NumpyNDArrayTranslator)

    # Check that Transltor transforms to correct type
    transformed = translators.transform(np.array([1]), np.ndarray)
    assert isinstance(transformed, np.ndarray)


def test_xr_dataarray_translator():
    import xarray as xr
    
    # Check that an ndarray translator can be created
    _xrwrapper = wrappers.get_wrapper(xr.DataArray())
    _trans = xrtranslator.translator(_xrwrapper, xr.DataArray)
    assert isinstance(_trans, xrtranslator.XArrayDataArrayTranslator)

    # Check that get_translator method find the right translator
    _trans = translators.get_translator(xr.DataArray(), xr.DataArray)
    assert isinstance(_trans, xrtranslator.XArrayDataArrayTranslator)

    # Check that Transltor transforms to correct type
    transformed = translators.transform(xr.DataArray(), xr.DataArray)
    assert isinstance(transformed, xr.DataArray)


def test_xr_dataset_translator():
    import xarray as xr

    # Check that an ndarray translator can be created
    _xrwrapper = wrappers.get_wrapper(xr.Dataset())
    _trans = xrtranslator.translator(_xrwrapper, xr.Dataset)
    assert isinstance(_trans, xrtranslator.XArrayDataArrayTranslator)

    # Check that get_translator method find the right translator
    _trans = translators.get_translator(xr.Dataset(), xr.Dataset)
    assert isinstance(_trans, xrtranslator.XArrayDataArrayTranslator)

    # Check that Transltor transforms to correct type
    transformed = translators.transform(xr.Dataset(), xr.Dataset)
    assert isinstance(transformed, xr.Dataset)
