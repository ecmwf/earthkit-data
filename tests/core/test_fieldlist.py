#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import numpy as np
import pytest
from earthkit.utils.testing import NO_TORCH

from earthkit.data import SimpleFieldList


def test_empty_fieldlist_values_numpy():
    ds = SimpleFieldList()

    v = ds.values
    assert isinstance(v, np.ndarray)
    assert v.shape == (0,)


def test_empty_fieldlist_data_numpy():
    ds = SimpleFieldList()

    v = ds.data()
    assert isinstance(v, np.ndarray)
    assert v.shape == (0, 0, 0)

    v = ds.data(keys="value")
    assert isinstance(v, np.ndarray)
    assert v.shape == (0,)

    v = ds.data(keys="lat")
    assert isinstance(v, np.ndarray)
    assert v.shape == (0,)

    v = ds.data(keys="lon")
    assert isinstance(v, np.ndarray)
    assert v.shape == (0,)

    v = ds.data(keys=["lon", "lat"])
    assert isinstance(v, np.ndarray)
    assert v.shape == (0, 0)


def test_empty_fieldlist_to_latlon_numpy():
    ds = SimpleFieldList()

    v = ds.to_latlon()
    assert v == {"lat": None, "lon": None}


def test_empty_fieldlist_to_array_numpy():
    ds = SimpleFieldList()

    v = ds.to_array()
    assert isinstance(v, np.ndarray)
    assert v.shape == (0,)

    v = ds.to_array(array_backend="numpy")
    assert isinstance(v, np.ndarray)
    assert v.shape == (0,)

    v = ds.to_array(array_backend=None)
    assert isinstance(v, np.ndarray)
    assert v.shape == (0,)


@pytest.mark.skipif(NO_TORCH, reason="No pytorch installed")
def test_empty_fieldlist_to_array_torch():
    import torch

    ds = SimpleFieldList()

    v = ds.to_array(array_backend="torch")
    assert isinstance(v, torch.Tensor)
    assert v.shape == (0,)
