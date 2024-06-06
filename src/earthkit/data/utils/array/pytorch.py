# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from . import ArrayBackend


class PytorchBackend(ArrayBackend):
    _name = "pytorch"
    _array_name = "tensor"
    _module_name = "torch"

    def __init__(self):
        super().__init__()
        self._converters = {"numpy": self.from_numpy}

    def _load(self):
        try:
            import array_api_compat

        except Exception as e:
            raise ImportError(f"array_api_compat is required to use pytorch backend, {e}")

        try:
            import torch
        except Exception as e:
            raise ImportError(f"torch is required to use pytorch backend, {e}")

        dt = {"float64": torch.float64, "float32": torch.float32}
        ns = array_api_compat.array_namespace(torch.ones(2))

        return ns, dt

    def _is_native_array(self, v, dtype=None):
        import torch

        if not torch.is_tensor(v):
            return False
        return self.match_dtype(v, dtype)

    def to_numpy(self, v):
        return v.numpy()

    def from_numpy(self, v):
        import torch

        return torch.from_numpy(v)

    def from_other(self, v, **kwargs):
        import torch

        return torch.tensor(v, **kwargs)


Backend = PytorchBackend
