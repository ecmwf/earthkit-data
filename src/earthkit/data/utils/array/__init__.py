# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
import sys
import threading
from abc import ABCMeta
from abc import abstractmethod
from importlib import import_module

LOG = logging.getLogger(__name__)


class ArrayBackendManager:
    def __init__(self):
        self.backends = None
        self._np_backend = None
        self.loaded = None
        self.lock = threading.Lock()

    def find_for_name(self, name):
        self._load()
        b = self.backends.get(name, None)
        if b is None:
            raise TypeError(f"No array backend found for name={name}")

        # throw an exception when the backend is not available
        if not b.available:
            raise Exception(f"Could not load array backend for name={name}")

        return b

    def find_for_array(self, v, guess=None):
        self._load()
        if guess is not None and guess.is_native_array(v):
            return guess

        # try all the backends. This will only try to load/import an unloaded/unimported
        # backend when necessary
        for _, b in self.backends.items():
            if b.is_native_array(v):
                return b

        raise TypeError(f"No array backend found for array type={type(v)}")

    @property
    def numpy_backend(self):
        if self._np_backend is None:
            self._np_backend = self.find_for_name("numpy")
        return self._np_backend

    def _load(self):
        """Load the available backend objects"""
        if self.loaded is None:
            with self.lock:
                self.backends = {}
                here = os.path.dirname(__file__)
                for path in sorted(os.listdir(here)):
                    if path[0] in ("_", "."):
                        continue

                    if path.endswith(".py") or os.path.isdir(os.path.join(here, path)):
                        name, _ = os.path.splitext(path)
                        try:
                            module = import_module(f".{name}", package=__name__)
                            if hasattr(module, "Backend"):
                                w = getattr(module, "Backend")
                                self.backends[name] = w()
                        except Exception as e:
                            LOG.exception(f"Failed to import array backend code {name} from {path}. {e}")
                self.loaded = True


class ArrayBackendCore:
    def __init__(self, backend):
        self.ns = None
        self.dtypes = None

        try:
            self.ns, self.dtypes = backend._load()
            self.avail = True
        except Exception as e:
            LOG.exception(f"Failed to load array backend {backend.name}. {e}")
            self.avail = False


class ArrayBackend(metaclass=ABCMeta):
    """The backend objects are created upfront but only loaded on
    demand to avoid unnecessary imports
    """

    _name = None
    _array_name = "array"
    _core = None
    _converters = {}

    def __init__(self):
        self.lock = threading.Lock()

    def _load_core(self):
        if self._core is None:
            with self.lock:
                if self._core is None:
                    self._core = ArrayBackendCore(self)

    @property
    def available(self):
        self._load_core()
        return self._core.avail

    @abstractmethod
    def _load(self):
        """Load the backend object. Called from arrayBackendCore."""
        pass

    @property
    def array_ns(self):
        """Delayed construction of array namespace"""
        self._load_core()
        return self._core.ns

    @property
    def name(self):
        return self._name

    @property
    def array_name(self):
        return f"{self._name} {self._array_name}"

    def to_array(self, v, source_backend=None):
        r"""Convert an array into the current backend.

        Parameters
        ----------
        v: array-like
            Array.
        source_backend: :obj:`ArrayBackend`, str
            The array backend of ``v``. When None ``source_backend``
            is automatically detected.

        Returns
        -------
        array-like
            ``v`` converted into the array backend defined by ``self``.
        """
        return self.from_backend(v, source_backend)

    @property
    def _dtypes(self):
        self._load_core()
        return self._core.dtypes

    def to_dtype(self, dtype):
        if isinstance(dtype, str):
            return self._dtypes.get(dtype, None)
        return dtype

    def match_dtype(self, v, dtype):
        if dtype is not None:
            dtype = self.to_dtype(dtype)
            f = v.dtype == dtype if dtype is not None else False
            return f
        return True

    def is_native_array(self, v, dtype=None):
        if (self._core is None and self._module_name not in sys.modules) or not self.available:
            return False
        return self._is_native_array(v, dtype=dtype)

    @abstractmethod
    def _is_native_array(self, v, **kwargs):
        pass

    def _quick_check_available(self):
        return (self._core is None and self._module_name not in sys.modules) or not self.available

    @abstractmethod
    def to_numpy(self, v):
        pass

    def to_backend(self, v, backend, **kwargs):
        assert backend is not None
        backend = ensure_backend(backend)
        return backend.from_backend(v, self, **kwargs)

    def from_backend(self, v, backend, **kwargs):
        if backend is None:
            backend = get_backend(v, strict=False)

        if self is backend:
            return v

        if backend is not None:
            b = self._converters.get(backend.name, None)
            if b is not None:
                return b(v)

        return self.from_other(v, **kwargs)

    @abstractmethod
    def from_other(self, v, **kwargs):
        pass


_MANAGER = ArrayBackendManager()

# The public API


def ensure_backend(backend):
    if backend is None:
        return numpy_backend()
    if isinstance(backend, str):
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
        raise ValueError(f"array type={b.array_name} and specified backend={guess} do not match")
    return b


def numpy_backend():
    return _MANAGER.numpy_backend
