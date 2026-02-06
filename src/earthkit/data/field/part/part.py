# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import ABCMeta
from abc import abstractmethod
from functools import wraps


def mark_key(*args):
    get_key = "get" in args
    set_key = "set" in args

    def wrapper(func):
        if get_key:
            func._is_get_key = get_key
        if set_key:
            func._is_set_key = set_key
        return func

    return wrapper


def mark_alias(name):
    def wrapper(func):
        @wraps(func)
        def inner(self, *args, **kwargs):
            other = getattr(self, name)
            return other(*args, **kwargs)

        inner._alias = name
        return inner

    return wrapper


def part_keys(cls):
    _GET_KEYS = []
    _SET_KEYS = []
    _ALIASES = {}
    _KEYS = []
    for k in dir(cls):
        if not k.startswith("_"):
            f = getattr(cls, k)
            if callable(f):
                if hasattr(f, "_is_get_key"):
                    # print(f"{k} is function")
                    _GET_KEYS.append(k)
                if hasattr(f, "_is_set_key"):
                    # print(f"{k} is function")
                    _SET_KEYS.append(k)
                if hasattr(f, "_alias"):
                    # print(f"{k} is alias to {f._alias}")
                    _ALIASES[k] = f._alias
                    _GET_KEYS.append(k)

    # cls._GET_KEYS = _GET_KEYS
    # cls._SET_KEYS = _SET_KEYS
    cls._ALIASES = _ALIASES
    cls._KEYS = _GET_KEYS
    return cls


def normalise_create_kwargs(cls, data, allowed_keys=None, allow_unused=False, remove_nones=True):
    _kwargs = {}
    for k_in, v in data.items():
        k = cls._ALIASES.get(k_in, k_in)
        if k in allowed_keys:
            _kwargs[k] = v
        else:
            if allow_unused:
                continue
            raise ValueError(f"Cannot use key={k} to create object={cls.__class__.__name__}")

    if remove_nones:
        _kwargs = {k: v for k, v in _kwargs.items() if v is not None}

    return _kwargs


def normalise_set_kwargs(cls, *args, allowed_keys=None, remove_nones=True, **kwargs):
    kwargs = kwargs.copy()

    for a in args:
        if a is None:
            continue
        if isinstance(a, dict):
            kwargs.update(a)
            continue
        raise ValueError(f"Cannot use arg={a}. Only dict allowed.")

    _kwargs = {}
    for k, v in kwargs.items():
        k = cls._ALIASES.get(k, k)
        if allowed_keys:
            if k in allowed_keys:
                _kwargs[k] = v
            else:
                raise ValueError(f"Cannot use key={k} to modify {cls.__class__.__name__}")
        else:
            _kwargs[k] = v

    if remove_nones:
        _kwargs = {k: v for k, v in _kwargs.items() if v is not None}

    return _kwargs


class FieldPart(metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict) -> "FieldPart":
        """
        Create a FieldPart instance from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing specification data.

        Returns
        -------
        FieldPart
            The created FieldPart instance.
        """
        pass

    @abstractmethod
    def to_dict(self) -> dict:
        """
        Convert the object to a dictionary.

        Returns
        -------
        dict
            Dictionary representation of the object.
        """
        pass

    @abstractmethod
    def keys(self) -> tuple | set:
        """Return the available keys in the part."""
        pass

    @abstractmethod
    def aliases(self) -> dict:
        """Return the aliases in the part."""
        pass

    @abstractmethod
    def get(self, key, default=None, *, astype=None, raise_on_missing=False) -> "any":
        r"""Return the values for the specified keys.

        Parameters
        ----------
        keys: str, list or tuple
            Specify the metadata keys to extract. Can be a single key (str) or multiple
            keys as a list/tuple of str.
        default: Any, None
            Specify the default value(s) for ``keys``. Returned when the given key
            is not found and ``raise_on_missing`` is False. When ``default`` is a single
            value, it is used for all the keys. Otherwise it must be a list/tuple of the
            same length as ``keys``.
        astype: type as str, int or float
            Return type for ``keys``.  When ``astype`` is a single type, it is used for
            all the keys. Otherwise it must be a list/tuple of the same length as ``keys``.
        raise_on_missing: bool
            When True, raises KeyError if any of ``keys`` is not found.

        Returns
        -------
        single value, list, tuple
            The value(s) for the specified ``keys``:

            - when ``keys`` is a str returns a single value
            - when ``keys`` is a list/tuple returns a list/tuple of values

        Raises
        ------
        KeyError
            If ``raise_on_missing`` is True and any of ``keys`` is not found.
        """
        pass

    @abstractmethod
    def _get_single(self, key, default=None, *, astype=None, raise_on_missing=False) -> "any":
        r"""Return the value for ``key``."""
        pass

    @abstractmethod
    def set(self, *args, **kwargs) -> "FieldPart":
        """
        Create a new FieldPart instance with updated data.

        Parameters
        ----------
        *args
            Positional arguments.
        **kwargs
            Keyword arguments.

        Returns
        -------
        Spec
            The created Spec instance.

        Raises
        ------
        KeyError
            If any of the keys to be set are not supported.
        """
        pass

    @abstractmethod
    def __contains__(self, name):
        pass

    @abstractmethod
    def __getstate__(self):
        pass

    @abstractmethod
    def __setstate__(self, state):
        pass


class SimpleFieldPart(FieldPart):
    _KEYS = tuple()
    _ALIASES = dict()

    def __contains__(self, name):
        """Check if the key is in the part."""
        return name in self._KEYS

    def keys(self):
        """Return the available keys in the part."""
        return self._KEYS

    def aliases(self):
        """Return the aliases in the part."""
        return self._ALIASES

    def _get_single(self, key, default=None, astype=None, raise_on_missing=False):
        if key in self:
            v = getattr(self, key)()
            if astype and v is not None and callable(astype):
                try:
                    return astype(v)
                except Exception:
                    return default
            return v

        if raise_on_missing:
            raise KeyError(f"Key {key} not found in FieldPart")

        return default

    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        return self._get_single(key, default=default, astype=astype, raise_on_missing=raise_on_missing)

    @classmethod
    def normalise_create_kwargs(cls, data, allowed_keys=None, remove_nones=False):
        _kwargs = {}
        for k_in, v in data.items():
            k = cls._ALIASES.get(k_in, k_in)
            if k in allowed_keys:
                if remove_nones and v is None:
                    continue
                _kwargs[k] = v
            else:
                raise ValueError(f"Cannot use key={k} to create object={cls}")
        return _kwargs

    @classmethod
    def normalise_set_kwargs(cls, *args, allowed_keys=None, **kwargs):
        kwargs = kwargs.copy()

        for a in args:
            if a is None:
                continue
            if isinstance(a, dict):
                kwargs.update(a)
                continue
            raise ValueError(f"Cannot use arg={a}. Only dict allowed.")

        _kwargs = {}
        for k, v in kwargs.items():
            k = cls._ALIASES.get(k, k)
            if allowed_keys:
                if k in allowed_keys:
                    _kwargs[k] = v
                else:
                    raise ValueError(f"Cannot use key={k} to modify {cls}")
            else:
                _kwargs[k] = v

        return _kwargs
