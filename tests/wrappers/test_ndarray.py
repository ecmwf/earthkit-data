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

from earthkit.data import from_object
from earthkit.data import wrappers
from earthkit.data.wrappers import ndarray as ndwrapper

LOG = logging.getLogger(__name__)


def test_ndarray_wrapper():
    import numpy as np

    _wrapper = ndwrapper.wrapper(np.array([]))
    assert isinstance(_wrapper, ndwrapper.NumpyNDArrayWrapper)
    _wrapper = wrappers.get_wrapper(np.array([]))
    assert isinstance(_wrapper, ndwrapper.NumpyNDArrayWrapper)
    _wrapper = from_object(np.array([]))
    assert isinstance(_wrapper, ndwrapper.NumpyNDArrayWrapper)
