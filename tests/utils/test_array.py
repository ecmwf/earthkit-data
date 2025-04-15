#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest

from earthkit.data.testing import NO_CUPY
from earthkit.data.testing import NO_JAX
from earthkit.data.testing import NO_PYTORCH
from earthkit.data.utils.array import _CUPY
from earthkit.data.utils.array import _JAX
from earthkit.data.utils.array import _NUMPY
from earthkit.data.utils.array import _PYTORCH
from earthkit.data.utils.array import get_backend

"""These tests are for the array backend utilities mostly used in other tests."""


def test_utils_array_backend_numpy():
    b = get_backend("numpy")
    assert b.name == "numpy"
    assert b is _NUMPY

    import numpy as np

    v = np.ones(10)
    v_lst = [1.0] * 10

    assert id(b.to_numpy(v)) == id(v)
    assert id(b.from_numpy(v)) == id(v)
    assert id(b.from_other(v)) == id(v)

    assert np.allclose(b.from_other(v_lst, dtype=np.float64), v)
    assert get_backend(v) is b
    assert get_backend(np) is b

    assert np.isclose(b.namespace.mean(v), 1.0)

    if not NO_PYTORCH:
        import torch

        v_pt = torch.ones(10, dtype=torch.float64)
        pt_b = get_backend("pytorch")
        r = pt_b.from_other(v)
        assert torch.is_tensor(r)
        assert torch.allclose(r, v_pt)


@pytest.mark.skipif(NO_PYTORCH, reason="No pytorch installed")
def test_utils_array_backend_pytorch():
    b = get_backend("pytorch")
    assert b.name == "pytorch"
    assert b is _PYTORCH

    import numpy as np
    import torch

    v = torch.ones(10, dtype=torch.float64)
    v_np = np.ones(10, dtype=np.float64)
    v_lst = [1.0] * 10

    assert torch.allclose(b.from_numpy(v_np), v)
    assert torch.allclose(b.from_other(v_lst, dtype=torch.float64), v)
    assert get_backend(v) is b

    r = b.to_numpy(v)
    assert isinstance(r, np.ndarray)
    assert np.allclose(r, v_np)

    assert np.isclose(b.namespace.mean(v), 1.0)


@pytest.mark.skipif(NO_CUPY, reason="No cupy installed")
def test_utils_array_backend_cupy():
    b = get_backend("cupy")
    assert b.name == "cupy"
    assert b is _CUPY

    import cupy as cp
    import numpy as np

    v = cp.ones(10, dtype=cp.float64)
    v_np = np.ones(10, dtype=np.float64)
    v_lst = [1.0] * 10

    # assert b.is_native_array(v)
    # assert id(b.from_backend(v, b)) == id(v)
    # assert id(b.from_backend(v, None)) == id(v)
    assert cp.allclose(b.from_numpy(v_np), v)
    assert cp.allclose(b.from_other(v_lst, dtype=cp.float64), v)
    assert get_backend(v) is b

    r = b.to_numpy(v)
    assert isinstance(r, np.ndarray)
    assert np.allclose(r, v_np)

    assert np.isclose(b.namespace.mean(v), 1.0)


@pytest.mark.skipif(NO_JAX, reason="No jax installed")
def test_utils_array_backend_jax():
    b = get_backend("jax")
    assert b.name == "jax"
    assert b is _JAX

    import jax.numpy as ja
    import numpy as np

    v = ja.ones(10, dtype=ja.float64)
    v_np = np.ones(10, dtype=np.float64)
    v_lst = [1.0] * 10

    # assert b.is_native_array(v)
    # assert id(b.from_backend(v, b)) == id(v)
    # assert id(b.from_backend(v, None)) == id(v)
    assert ja.allclose(b.from_numpy(v_np), v)
    assert ja.allclose(b.from_other(v_lst, dtype=ja.float64), v)
    assert get_backend(v) is b

    r = b.to_numpy(v)
    assert isinstance(r, np.ndarray)
    assert np.allclose(r, v_np)

    assert np.isclose(b.namespace.mean(v), 1.0)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
