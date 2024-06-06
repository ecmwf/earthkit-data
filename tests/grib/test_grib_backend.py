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

from earthkit.data import FieldList
from earthkit.data import from_source
from earthkit.data.testing import NO_CUPY
from earthkit.data.testing import NO_PYTORCH
from earthkit.data.testing import earthkit_examples_file


@pytest.mark.parametrize("_kwargs", [{}, {"array_backend": "numpy"}])
def test_grib_file_numpy_backend(_kwargs):
    ds = from_source("file", earthkit_examples_file("test6.grib"), **_kwargs)

    assert len(ds) == 6

    assert isinstance(ds[0].values, np.ndarray)
    assert ds[0].values.shape == (84,)

    assert isinstance(ds.values, np.ndarray)
    assert ds.values.shape == (
        6,
        84,
    )

    assert isinstance(ds[0].to_array(), np.ndarray)
    assert ds[0].to_array().shape == (7, 12)

    assert isinstance(ds.to_array(), np.ndarray)
    assert ds.to_array().shape == (6, 7, 12)

    assert isinstance(ds[0].to_numpy(), np.ndarray)
    assert ds[0].to_numpy().shape == (7, 12)

    assert isinstance(ds.to_numpy(), np.ndarray)
    assert ds.to_numpy().shape == (6, 7, 12)

    ds1 = ds.to_fieldlist()
    assert len(ds1) == len(ds)
    assert ds1.array_backend.name == "numpy"
    assert getattr(ds1, "path", None) is None


@pytest.mark.skipif(NO_PYTORCH, reason="No pytorch installed")
def test_grib_file_pytorch_backend():
    ds = from_source("file", earthkit_examples_file("test6.grib"), array_backend="pytorch")

    assert len(ds) == 6

    import torch

    assert torch.is_tensor(ds[0].values)
    assert ds[0].values.shape == (84,)

    assert torch.is_tensor(ds.values)
    assert ds.values.shape == (
        6,
        84,
    )

    x = ds[0].to_array()
    assert torch.is_tensor(x)
    assert x.shape == (7, 12)

    x = ds.to_array()
    assert torch.is_tensor(x)
    assert x.shape == (6, 7, 12)

    x = ds[0].to_numpy()
    assert isinstance(x, np.ndarray)
    assert x.shape == (7, 12)

    x = ds.to_numpy()
    assert isinstance(x, np.ndarray)
    assert x.shape == (6, 7, 12)

    ds1 = ds.to_fieldlist()
    assert len(ds1) == len(ds)
    assert ds1.array_backend.name == "pytorch"
    assert getattr(ds1, "path", None) is None


@pytest.mark.skipif(NO_CUPY, reason="No cupy installed")
def test_grib_file_cupy_backend():
    ds = from_source("file", earthkit_examples_file("test6.grib"), array_backend="cupy")

    import cupy as cp

    assert len(ds) == 6

    assert isinstance(ds[0].values, cp.ndarray)
    assert ds[0].values.shape == (84,)

    assert isinstance(ds.values, cp.ndarray)
    assert ds.values.shape == (
        6,
        84,
    )

    x = ds[0].to_array()
    assert isinstance(x, cp.ndarray)
    assert x.shape == (7, 12)

    x = ds.to_array()
    assert isinstance(x, cp.ndarray)
    assert x.shape == (6, 7, 12)

    x = ds[0].to_numpy()
    assert isinstance(x, np.ndarray)
    assert x.shape == (7, 12)

    x = ds.to_numpy()
    assert isinstance(x, np.ndarray)
    assert x.shape == (6, 7, 12)

    ds1 = ds.to_fieldlist()
    assert len(ds1) == len(ds)
    assert ds1.array_backend.name == "cupy"
    assert getattr(ds1, "path", None) is None


def test_grib_array_numpy_backend():
    s = from_source("file", earthkit_examples_file("test6.grib"))

    ds = FieldList.from_array(
        s.values,
        [m for m in s.metadata()],
    )
    assert len(ds) == 6
    with pytest.raises(AttributeError):
        ds.path

    assert isinstance(ds[0].values, np.ndarray)
    assert ds[0].values.shape == (84,)

    assert isinstance(ds.values, np.ndarray)
    assert ds.values.shape == (
        6,
        84,
    )

    assert isinstance(ds[0].to_array(), np.ndarray)
    assert ds[0].to_array().shape == (7, 12)

    assert isinstance(ds.to_array(), np.ndarray)
    assert ds.to_array().shape == (6, 7, 12)

    assert isinstance(ds[0].to_numpy(), np.ndarray)
    assert ds[0].to_numpy().shape == (7, 12)

    assert isinstance(ds.to_numpy(), np.ndarray)
    assert ds.to_numpy().shape == (6, 7, 12)


@pytest.mark.skipif(NO_PYTORCH, reason="No pytorch installed")
def test_grib_array_pytorch_backend():
    s = from_source("file", earthkit_examples_file("test6.grib"), array_backend="pytorch")

    ds = FieldList.from_array(
        s.values,
        [m for m in s.metadata()],
    )
    assert len(ds) == 6
    with pytest.raises(AttributeError):
        ds.path

    import torch

    assert torch.is_tensor(ds[0].values)
    assert ds[0].values.shape == (84,)

    assert torch.is_tensor(ds.values)
    assert ds.values.shape == (
        6,
        84,
    )

    assert torch.is_tensor(ds[0].to_array())
    assert ds[0].to_array().shape == (7, 12)

    assert torch.is_tensor(ds.to_array())
    assert ds.to_array().shape == (6, 7, 12)

    assert isinstance(ds[0].to_numpy(), np.ndarray)
    assert ds[0].to_numpy().shape == (7, 12)

    assert isinstance(ds.to_numpy(), np.ndarray)
    assert ds.to_numpy().shape == (6, 7, 12)


@pytest.mark.skipif(NO_CUPY, reason="No cupy installed")
def test_grib_array_cupy_backend():
    s = from_source("file", earthkit_examples_file("test6.grib"), array_backend="cupy")

    ds = FieldList.from_array(
        s.values,
        [m for m in s.metadata()],
    )
    assert len(ds) == 6
    with pytest.raises(AttributeError):
        ds.path

    import cupy as cp

    assert isinstance(ds[0].values, cp.ndarray)
    assert ds[0].values.shape == (84,)

    assert isinstance(ds.values, cp.ndarray)
    assert ds.values.shape == (
        6,
        84,
    )

    x = ds[0].to_array()
    assert isinstance(x, cp.ndarray)
    assert x.shape == (7, 12)

    x = ds.to_array()
    assert isinstance(x, cp.ndarray)
    assert x.shape == (6, 7, 12)

    x = ds[0].to_numpy()
    assert isinstance(x, np.ndarray)
    assert x.shape == (7, 12)

    x = ds.to_numpy()
    assert isinstance(x, np.ndarray)
    assert x.shape == (6, 7, 12)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main()
