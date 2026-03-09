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

from earthkit.data import from_object
from earthkit.data import transform

LOG = logging.getLogger(__name__)


def test_ndarray_translator():
    val = np.array([1, 2, 3])
    ds = from_object(val)

    assert np.allclose(transform(val, np.ndarray), val)
    assert np.allclose(transform(ds, np.ndarray), val)

    assert isinstance(transform(val, np.ndarray), np.ndarray)
    assert isinstance(transform(ds, np.ndarray), np.ndarray)
