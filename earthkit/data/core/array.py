# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import threading
from abc import ABCMeta, abstractmethod


class ArrayBackendItem:
    def __init__(self, backend_type):
        self.type = backend_type
        self._obj = None
        self._avail = None
        self.lock = threading.Lock()

    def obj(self):
        if self._obj is None:
            with self.lock:
                if self._obj is None:
                    self._obj = self.type()
        return self._obj

    def available(self):
        if self._avail is None:
            if self._obj is not None:
                self._avail = True
            else:
                try:
                    self.obj()
                    self._avail = True
                except Exception:
                    self._avail = False
        return self._avail


class ArrayBackendManager:
    def __init__(self):
        """The backend objects are created on demand to avoid unnecessary imports"""
        self.backends = {k: ArrayBackendItem(v) for k, v in array_backend_types.items()}
        self._np_backend = None

    def find_for_name(self, name):
        b = self.backends.get(name, None)
        if b is None:
            raise TypeError(f"No backend found for name={name}")

        # this will try to create the backend if it does not exist yet and
        # throw an exception when it is not possible
        return b.obj()

    def find_for_array(self, v, guess=None):
        if guess is not None:
            if guess.is_native_array(v):
                return guess

        # try all the backends
        for _, b in self.backends.items():
            # this will try create the backend if it does not exist yest.
            # If it fails available() will return False from this moment on.
            if b.available() and b.obj().is_native_array(v):
                return b.obj()

        raise TypeError(f"No backend found for array type={type(v)}")

    def numpy_backend(self):
        if self._np_backend is None:
            self._np_backend = self.find_for_name("numpy")
        return self._np_backend


class ArrayBackend(metaclass=ABCMeta):
    _array_ns = None
    _default = "numpy"
    _name = None
    _array_name = "array"
    _dtypes = {}

    def __init__(self):
        self.lock = threading.Lock()

    @property
    def array_ns(self):
        """Delayed construction of array namespace"""
        if self._array_ns is None:
            with self.lock:
                if self._array_ns is None:
                    self._array_ns = self._make_array_ns()
        return self._array_ns

    @abstractmethod
    def _make_array_ns(self):
        pass

    @property
    def name(self):
        return self._name

    @property
    def array_name(self):
        return f"{self._name} {self._array_name}"

    def to_array(self, v, backend=None):
        if backend is not None:
            if backend is self:
                return v

            return backend.to_backend(v, self)
        else:
            b = get_backend(v, strict=False)
            return b.to_backend(v, self)

    def to_dtype(self, dtype):
        if isinstance(dtype, str):
            return self._dtypes.get(dtype, None)
        return dtype

    def match_dtype(self, v, dtype):
        if dtype is not None:
            dtype = self.to_dtype(dtype)
            return v.dtype == dtype if dtype is not None else False
        return True

    @abstractmethod
    def is_native_array(self, v, **kwargs):
        pass

    @abstractmethod
    def to_backend(self, v, backend):
        pass

    @abstractmethod
    def from_numpy(self, v):
        pass

    @abstractmethod
    def from_pytorch(self, v):
        pass

    @abstractmethod
    def from_other(self, v, **kwargs):
        pass


class NumpyBackend(ArrayBackend):
    _name = "numpy"

    def __init__(self):
        super().__init__()

    def _make_array_ns(self):
        import numpy as np

        try:
            import array_api_compat

            ns = array_api_compat.array_namespace(np.ones(2))
        except Exception:
            ns = np

        return ns

    def to_dtype(self, dtype):
        return dtype

    def is_native_array(self, v, dtype=None):
        import numpy as np

        if not isinstance(v, np.ndarray):
            return False
        if dtype is not None:
            return v.dtype == dtype
        return True

    def to_backend(self, v, backend):
        return backend.from_numpy(v)

    def from_numpy(self, v):
        return v

    def from_pytorch(self, v):
        return v.numpy()

    def from_other(self, v, **kwargs):
        import numpy as np

        return np.array(v, **kwargs)


class PytorchBackend(ArrayBackend):
    _name = "pytorch"
    _array_name = "tensor"

    def __init__(self):
        super().__init__()
        # pytorch is an optional dependency, we need to see on init
        # if we can load it
        self.array_ns

    def _make_array_ns(self):
        try:
            import array_api_compat

        except Exception:
            raise ImportError("array_api_compat is required to use pytorch backend")

        try:
            import torch
        except Exception:
            raise ImportError("pytorch is required to use pytorch backend")

        self._dtypes = {"float64": torch.float64, "float32": torch.float32}

        return array_api_compat.array_namespace(torch.ones(2))

    def is_native_array(self, v, dtype=None):
        import torch

        if not torch.is_tensor(v):
            return False
        return self.match_dtype(v, dtype)

    def to_backend(self, v, backend):
        return backend.from_pytorch(v)

    def from_numpy(self, v):
        import torch

        return torch.from_numpy(v)

    def from_pytorch(self, v):
        return v

    def from_other(self, v, **kwargs):
        import torch

        return torch.tensor(v, **kwargs)


array_backend_types = {"numpy": NumpyBackend, "pytorch": PytorchBackend}

_MANAGER = ArrayBackendManager()

NUMPY_BACKEND = _MANAGER.numpy_backend()


def ensure_backend(backend):
    if backend is None:
        return _MANAGER.find_for_name(ArrayBackend._default)
    elif isinstance(backend, str):
        return _MANAGER.find_for_name(backend)
    else:
        return backend


def get_backend(array, guess=None, strict=True):
    if isinstance(array, list):
        array = array[0]

    if guess is not None:
        guess = ensure_backend(guess)

    b = _MANAGER.find_for_array(array, guess=guess)
    if strict and guess is not None and b is not guess:
        raise ValueError(
            f"array type={b.array_name} and specified backend={guess} do not match"
        )
    return b
