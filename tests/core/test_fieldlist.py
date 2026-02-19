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
from earthkit.utils.array.testing.testing import NO_TORCH

from earthkit.data import SimpleFieldList
from earthkit.data import create_fieldlist


def _create_empty_fieldlist(mode):

    if mode == "method":
        return create_fieldlist()
    elif mode == "object":
        return SimpleFieldList()
    else:
        raise ValueError(f"Unknown mode: {mode}")


@pytest.mark.parametrize("mode", ["method", "object"])
def test_empty_fieldlist_values_numpy(mode):
    ds = _create_empty_fieldlist(mode)

    v = ds.values
    assert isinstance(v, np.ndarray)
    assert v.shape == (0,)


@pytest.mark.parametrize("mode", ["method", "object"])
def test_empty_fieldlist_data_numpy(mode):
    ds = _create_empty_fieldlist(mode)

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


@pytest.mark.parametrize("mode", ["method", "object"])
def test_empty_fieldlist_to_latlon_numpy(mode):
    ds = _create_empty_fieldlist(mode)

    with pytest.raises(ValueError):
        ds.geography

    with pytest.raises(ValueError):
        ds.geography.latlons()


@pytest.mark.parametrize("mode", ["method", "object"])
def test_empty_fieldlist_to_array_numpy(mode):
    ds = _create_empty_fieldlist(mode)

    v = ds.to_array()
    assert isinstance(v, np.ndarray)
    assert v.shape == (0,)

    v = ds.to_array(array_namespace="numpy")
    assert isinstance(v, np.ndarray)
    assert v.shape == (0,)

    v = ds.to_array(array_namespace=None)
    assert isinstance(v, np.ndarray)
    assert v.shape == (0,)


@pytest.mark.skipif(NO_TORCH, reason="No pytorch installed")
@pytest.mark.parametrize("mode", ["method", "object"])
def test_empty_fieldlist_to_array_torch(mode):
    import torch

    ds = _create_empty_fieldlist(mode)

    v = ds.to_array(array_namespace="torch")
    assert isinstance(v, torch.Tensor)
    assert v.shape == (0,)
