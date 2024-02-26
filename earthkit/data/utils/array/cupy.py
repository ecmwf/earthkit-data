# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import sys

from . import ArrayBackend


class CupyBackend(ArrayBackend):
    _name = "cupy"
    _array_name = "tensor"

    def _load(self):
        try:
            import array_api_compat

        except Exception as e:
            raise ImportError(
                f"array_api_compat is required to use cupy backend, {e}"
            )

        try:
            import cupy as cp
        except Exception as e:
            raise ImportError(f"cupy is required to use cupy backend, {e}")

        dt = {"float64": cp.float64, "float32": cp.float32}
        ns = array_api_compat.array_namespace(cp.ones(2))

        return ns, dt

    def is_native_array(self, v, dtype=None):
        if (not self._loaded() and "cupy" not in sys.modules) or not self.available:
            return False

        import cupy as cp

        if not isinstance(v, cp.ndarray):
            return False
        return self.match_dtype(v, dtype)

    def to_backend(self, v, backend):
        return backend.from_cupy(v)

    def from_numpy(self, v):
        import cupy as cp

        return cp.array(v)

    def from_pytorch(self, v):
        return None

    def from_cupy(self, v):
        return v

    def from_other(self, v, **kwargs):
        import cupy as cp

        return cp.array(v, **kwargs)


Backend = CupyBackend