# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os

from . import ArrayBackend


class PytorchBackend(ArrayBackend):
    _name = "pytorch"
    _array_name = "tensor"

    def _load(self):
        try:
            import array_api_compat

        except Exception as e:
            raise ImportError(
                f"array_api_compat is required to use pytorch backend, {e}"
            )

        try:
            import torch
        except Exception as e:
            raise ImportError(f"torch is required to use pytorch backend, {e}")

        dt = {"float64": torch.float64, "float32": torch.float32}
        ns = array_api_compat.array_namespace(torch.ones(2))

        return ns, dt

    def is_native_array(self, v, dtype=None):
        if self.available is None and "torch" not in os.modules:
            return False

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


Backend = PytorchBackend
