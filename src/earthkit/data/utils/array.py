# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from abc import ABCMeta
from abc import abstractmethod
from functools import cached_property

LOG = logging.getLogger(__name__)


class ArrayNamespace:
    @cached_property
    def api(self):
        try:
            import array_api_compat

            return array_api_compat
        except Exception:
            raise ImportError("array_api_compat is required to use array namespace")

    @cached_property
    def numpy(self):
        import numpy as np

        return self.api.array_namespace(np.ones(2))

    def namespace(self, *arrays):
        # default namespace is numpy
        if not arrays:
            return self.numpy

        # if isinstance(arrays[0], self.numpy.ndarray):
        #     return self.numpy

        # if self.api is not None:
        return self.api.array_namespace(*arrays)

        # raise ValueError("Can't find namespace for array. Please install array_api_compat package")


_NAMESPACE = ArrayNamespace()


class ArrayBackend(metaclass=ABCMeta):
    @property
    def name(self):
        return self._name

    @abstractmethod
    def _make_sample(self):
        return None

    @property
    def namespace(self):
        return _NAMESPACE.namespace(self._make_sample())

    @property
    @abstractmethod
    def module(self):
        pass

    @abstractmethod
    def to_numpy(self, v):
        pass

    @abstractmethod
    def from_numpy(self, v):
        pass

    @abstractmethod
    def from_other(self, v, **kwargs):
        pass

    @property
    @abstractmethod
    def dtypes(self):
        pass

    def to_dtype(self, dtype):
        if isinstance(dtype, str):
            return self.dtypes.get(dtype, None)
        return dtype

    def match_dtype(self, v, dtype):
        if dtype is not None:
            dtype = self.to_dtype(dtype)
            f = v.dtype == dtype if dtype is not None else False
            return f
        return True


class NumpyBackend(ArrayBackend):
    _name = "numpy"
    _module_name = "numpy"

    def _make_sample(self):
        import numpy as np

        return np.ones(2)

    @cached_property
    def module(self):
        import numpy as np

        return np

    def to_numpy(self, v):
        return v

    def from_numpy(self, v):
        return v

    def from_other(self, v, **kwargs):
        import numpy as np

        if not kwargs and isinstance(v, np.ndarray):
            return v

        return np.array(v, **kwargs)

    @cached_property
    def dtypes(self):
        import numpy

        return {"float64": numpy.float64, "float32": numpy.float32}


class PytorchBackend(ArrayBackend):
    _name = "pytorch"
    _module_name = "torch"

    def _make_sample(self):
        import torch

        return torch.ones(2)

    @cached_property
    def module(self):
        import torch

        return torch

    def to_numpy(self, v):
        return v.cpu().numpy()

    def from_numpy(self, v):
        import torch

        return torch.from_numpy(v)

    def from_other(self, v, **kwargs):
        import torch

        return torch.tensor(v, **kwargs)

    @cached_property
    def dtypes(self):
        import torch

        return {"float64": torch.float64, "float32": torch.float32}


class JaxBackend(ArrayBackend):
    _name = "jax"
    _module_name = "jax"

    def _make_sample(self):
        import jax.numpy as jarray

        return jarray.ones(2)

    @cached_property
    def module(self):
        import jax.numpy as jarray

        return jarray

    def to_numpy(self, v):
        import numpy as np

        return np.array(v)

    def from_numpy(self, v):
        return self.from_other(v)

    def from_other(self, v, **kwargs):
        import jax.numpy as jarray

        return jarray.array(v, **kwargs)

    @cached_property
    def dtypes(self):
        import jax.numpy as jarray

        return {"float64": jarray.float64, "float32": jarray.float32}


class CupyBackend(ArrayBackend):
    _name = "cupy"
    _module_name = "cupy"

    def _make_sample(self):
        import cupy

        return cupy.ones(2)

    @cached_property
    def module(self):
        import cupy

        return cupy

    def from_numpy(self, v):
        return self.from_other(v)

    def to_numpy(self, v):
        return v.get()

    def from_other(self, v, **kwargs):
        import cupy as cp

        return cp.array(v, **kwargs)

    @cached_property
    def dtypes(self):
        import cupy as cp

        return {"float64": cp.float64, "float32": cp.float32}


_NUMPY = NumpyBackend()
_PYTORCH = PytorchBackend()
_CUPY = CupyBackend()
_JAX = JaxBackend()

_BACKENDS = [_NUMPY, _PYTORCH, _CUPY, _JAX]
_BACKENDS_BY_NAME = {v._name: v for v in _BACKENDS}
_BACKENDS_BY_MODULE = {v._module_name: v for v in _BACKENDS}


def array_namespace(*args):
    return _NAMESPACE.namespace(*args)


def array_to_numpy(array):
    return backend_from_array(array).to_numpy(array)


def backend_from_array(array, raise_exception=True):
    if isinstance(array, _NAMESPACE.numpy.ndarray):
        return _NUMPY

    if _NAMESPACE.api is not None:
        if _NAMESPACE.api.is_torch_array(array):
            return _PYTORCH
        elif _NAMESPACE.api.is_cupy_array(array):
            return _CUPY
        elif _NAMESPACE.api.is_jax_array(array):
            return _JAX

    if raise_exception:
        raise ValueError(f"Can't find namespace for array type={type(array)}")


def backend_from_name(name, raise_exception=True):
    r = _BACKENDS_BY_NAME.get(name, None)
    if raise_exception and r is None:
        raise ValueError(f"Unknown array backend name={name}")
    return r


def backend_from_module(module, raise_exception=True):
    import inspect

    r = None
    if inspect.ismodule(module):
        r = _BACKENDS_BY_MODULE.get(module.__name__, None)
        if raise_exception and r is None:
            raise ValueError(f"Unknown array backend module={module}")
    return r


def get_backend(data):
    if isinstance(data, ArrayBackend):
        return data
    if isinstance(data, str):
        return backend_from_name(data, raise_exception=True)

    r = backend_from_module(data, raise_exception=True)
    if r is None:
        r = backend_from_array(data)

    return r


class Converter:
    def __init__(self, source, target):
        self.source = source
        self.target = target

    def __call__(self, array, **kwargs):
        if self.source == _NUMPY:
            return self.target.from_numpy(array, **kwargs)
        return self.target.from_other(array, **kwargs)


def converter(array, target):
    if target is None:
        return None

    source_backend = backend_from_array(array)
    target_backend = get_backend(target)

    if source_backend == target_backend:
        return None
    return Converter(source_backend, target_backend)


def convert_array(array, target_backend=None, target_array_sample=None, **kwargs):
    if target_backend is not None and target_array_sample is not None:
        raise ValueError("Only one of target_backend or target_array_sample can be specified")
    if target_backend is not None:
        target = target_backend
    else:
        target = backend_from_array(target_array_sample)

    r = []
    target_is_list = True
    if not isinstance(array, (list, tuple)):
        array = [array]
        target_is_list = False

    for a in array:
        c = converter(a, target)
        if c is None:
            r.append(a)
        else:
            r.append(c(a, **kwargs))

    if not target_is_list:
        return r[0]
    return r


def match(v1, v2):
    get_backend(v1) == get_backend(v2)


# added for backward compatibility
def ensure_backend(backend):
    return None
