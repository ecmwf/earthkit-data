try:
    import array_api_compat
except Exception:
    array_api_compat = None


class ArrayBackend:
    _array_ns = None

    def to_numpy(self):
        pass

    def _get_backend(self, v):
        for k, b in array_backends:
            if b.match(v):
                return b

    def mutate(self):
        if self._array_ns is None:
            return EmptyBackend()
        return self


class EmptyBackend(ArrayBackend):
    def match(self, v):
        return False


class NumpyBackend(ArrayBackend):
    def __init__(self):
        import numpy as np

        self._array_ns = array_api_compat.array_namespace(np.ones(2))

    def match(self, v):
        import numpy as np

        return isinstance(v, np.ndarray)

    @property
    def array_ns(self):
        return self._array_ns

    def to_array(self, v, backend=None):
        if backend is not None:
            if backend == self:
                return v
            return backend.to_numpy(v)
        # else:
        #     try:
        #         import array_api_compat

        #     __array_ns = array_api_compat.array_namespace(v)
        # return v

    def from_numpy(self, v):
        return v

    def from_pytorch(self, v):
        import torch

        return torch.to_numpy(v)


class PytorchBackend(ArrayBackend):
    def __init__(self):
        try:
            import torch

            self._array_ns = array_api_compat.array_namespace(torch.ones(2))
        except Exception:
            pass

    def match(self, v):
        import numpy as np

        return isinstance(v, np.ndarray)


array_backends = {"numpy": NumpyBackend, "pytorch": PytorchBackend().mutate()}
