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

LOG = logging.getLogger(__name__)


def test_int_wrapper():
    v = 11
    ds = from_object(v)
    assert ds._TYPE_NAME == "int"
    assert "numpy" in ds.available_types

    v1 = ds.to_numpy()
    assert np.allclose(v1, v)

    v1 = ds.to_numpy(copy=True, flatten=True)
    assert np.allclose(v1, v)

    assert isinstance(ds.to_value(), int)
    assert ds.to_value() == v
