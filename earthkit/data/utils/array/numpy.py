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


class NumpyBackend(ArrayBackend):
    _name = "numpy"

    def _load(self):
        import numpy as np

        try:
            import array_api_compat

            ns = array_api_compat.array_namespace(np.ones(2))
        except Exception:
            ns = np

        return ns, {}

    def to_dtype(self, dtype):
        return dtype

    def is_native_array(self, v, dtype=None):
        if self.available is None and "numpy" not in os.modules:
            return False

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


Backend = NumpyBackend
