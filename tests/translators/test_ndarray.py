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

import pytest

from earthkit.data.translators import ndarray as ndtranslator
from earthkit.data import translators, wrappers

LOG = logging.getLogger(__name__)


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

