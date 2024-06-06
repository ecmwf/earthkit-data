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
from earthkit.data.testing import NO_PYTORCH
from earthkit.data.utils.array import ensure_backend
from earthkit.data.utils.array import get_backend


def test_utils_array_backend_numpy():
    b = ensure_backend("numpy")
    assert b.name == "numpy"

    import numpy as np

    v = np.ones(10)
    v_lst = [1.0] * 10

    assert b.is_native_array(v)
    assert id(b.to_numpy(v)) == id(v)
    assert id(b.from_backend(v, b)) == id(v)
    assert id(b.from_backend(v, None)) == id(v)
    assert np.allclose(b.from_other(v_lst, dtype=np.float64), v)
    assert get_backend(v) is b
    assert get_backend(v, guess=b) is b

    assert np.isclose(b.array_ns.mean(v), 1.0)

    if not NO_PYTORCH:
        import torch

        v_pt = torch.ones(10, dtype=torch.float64)
        pt_b = ensure_backend("pytorch")
        r = b.to_backend(v, pt_b)
        assert torch.is_tensor(r)
        assert torch.allclose(r, v_pt)


@pytest.mark.skipif(NO_PYTORCH, reason="No pytorch installed")
def test_utils_array_backend_pytorch():
    b = ensure_backend("pytorch")
    assert b.name == "pytorch"

    import numpy as np
    import torch

    v = torch.ones(10, dtype=torch.float64)
    v_np = np.ones(10, dtype=np.float64)
    v_lst = [1.0] * 10

    assert b.is_native_array(v)
    assert id(b.from_backend(v, b)) == id(v)
    assert id(b.from_backend(v, None)) == id(v)
    assert torch.allclose(b.from_backend(v_np, None), v)
    assert torch.allclose(b.from_numpy(v_np), v)
    assert torch.allclose(b.from_other(v_lst, dtype=torch.float64), v)
    assert get_backend(v) is b
    assert get_backend(v, guess=b) is b

    np_b = ensure_backend("numpy")
    r = b.to_backend(v, np_b)
    assert isinstance(r, np.ndarray)
    assert np.allclose(r, v_np)

    assert np.isclose(b.array_ns.mean(v), 1.0)


@pytest.mark.skipif(NO_CUPY, reason="No pytorch installed")
def test_utils_array_backend_cupy():
    b = ensure_backend("cupy")
    assert b.name == "cupy"

    import cupy as cp
    import numpy as np

    v = cp.ones(10, dtype=cp.float64)
    v_np = np.ones(10, dtype=np.float64)
    v_lst = [1.0] * 10

    assert b.is_native_array(v)
    assert id(b.from_backend(v, b)) == id(v)
    assert id(b.from_backend(v, None)) == id(v)
    assert cp.allclose(b.from_backend(v_np, None), v)
    assert cp.allclose(b.from_other(v_lst, dtype=cp.float64), v)
    assert get_backend(v) is b
    assert get_backend(v, guess=b) is b

    np_b = ensure_backend("numpy")
    r = b.to_backend(v, np_b)
    assert isinstance(r, np.ndarray)
    assert np.allclose(r, v_np)

    assert np.isclose(b.array_ns.mean(v), 1.0)


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
