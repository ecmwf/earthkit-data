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


class ArrayBackendManager:
    def __init__(self):
        self.backends = {}
        self.lock = threading.Lock()

    def find(self, name):
        with self.lock:
            b = self.backends.get(name, None)
            if b is None:
                b = array_backend_types[name]()
                self.backends[name] = b
            return b


MANAGER = ArrayBackendManager()


class ArrayBackend(metaclass=ABCMeta):
    _array_ns = None

    @property
    def array_ns(self):
        return self._array_ns

    @staticmethod
    def find(name):
        return MANAGER.find(name)

    def to_array(self, v, backend=None):
        if backend is not None:
            if backend is self:
                return v

            return backend.to_backend(self, v)

    @abstractmethod
    def to_backend(self, backend, v):
        pass

    @abstractmethod
    def from_numpy(self, v):
        pass

    @abstractmethod
    def from_pytorch(self, v):
        pass


class NumpyBackend(ArrayBackend):
    def __init__(self):
        import numpy as np

        try:
            import array_api_compat

            self._array_ns = array_api_compat.array_namespace(np.ones(2))
        except Exception:
            self._array_ns = np

    def to_backend(self, backend, v):
        return backend.from_numpy(v)

    def from_numpy(self, v):
        return v

    def from_pytorch(self, v):
        import torch

        return torch.to_numpy(v)


class PytorchBackend(ArrayBackend):
    def __init__(self):
        try:
            import array_api_compat

        except Exception:
            raise ImportError("array_api_compat is required to use pytorch backend")

        import torch

        self._array_ns = array_api_compat.array_namespace(torch.ones(2))

    def to_backend(self, backend, v):
        return backend.from_pytorch(v)

    def from_numpy(self, v):
        import torch

        return torch.from_numpy(v)

    def from_pytorch(self, v):
        return v


array_backend_types = {"numpy": NumpyBackend, "pytorch": PytorchBackend}
