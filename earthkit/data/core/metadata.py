# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import ABCMeta, abstractmethod
import functools

from earthkit.data.core.constants import DATETIME
from earthkit.data.decorators import cached_method


def internal_key(func):
    """Controls if internal keys can be accessed"""
    @functools.wraps(func)
    def wrapped(self, key, *args, **kwargs):
        if not self._internal:
            ns, _, name = key.partition(".")
            if name == "":
                name = key
                ns = ""

            if args:
                kwargs["default"] = args[0]

            args = ()

            if ns == self.EKD_NAMESPACE:
                key = name
            else:
                if name in self.INTERNAL_KEYS:
                    if kwargs.get("raise_on_missing", True):
                        raise KeyError(key)
                    else:
                        return kwargs.get("default", None)

        return func(self, key, *args, **kwargs)

    return wrapped


def internal_namespace(func):
    """Controls if internal namespaces an be accessed"""
    @functools.wraps(func)
    def wrapped(self, namespace):
        if not self._internal:
            if namespace in self.INTERNAL_NAMESPACES:
                return {}

            r = func(self, namespace)
            for k in list(r.keys()):
                if k in self.INTERNAL_KEYS:
                    del r[k]
            return r
        else:
            return func(self, namespace)

    return wrapped


def internal_namespace_list(func):
    """Controls if internal namespaced an be accessed"""
    @functools.wraps(func)
    def wrapped(self):
        v = func(self)
        if not self._internal:
            r = []
            for x in v:
                if x not in self.INTERNAL_NAMESPACES:
                    r.append(x)
            return r
        else:
            return v

    return wrapped

class Metadata(metaclass=ABCMeta):
    r"""Base class to represent metadata.

    Metadata is a dict-like immutable object. Modification is possible
    with :obj:`override`, which always creates a new object.

    Implemented in subclasses: :obj:`RawMetadata`, :obj:`GribMetadata`.

    Examples
    --------
    - :ref:`/examples/metadata.ipynb`

    """

    DATA_FORMAT = None
    NAMESPACES = []
    LS_KEYS = []
    DESCRIBE_KEYS = [] 
    INDEX_KEYS = []
    CUSTOM_KEYS = [DATETIME]
    _internal = True

    # _key_accessor = None

    def __init_subclass__(cls, *args, **kwargs):
        super().__init_subclass__(*args, **kwargs)
    
        name = "as_namespace"
        if name in cls.__dict__:
            setattr(cls, name, namespace_filter(getattr(cls, name)))

    
    def __iter__(self):
        """Return an iterator over the metadata keys."""
        return iter(self.keys())

    @abstractmethod
    def __len__(self):
        r"""Return the number of metadata entries."""
        pass

    def __getitem__(self, key):
        r"""Return the value for ``key``.

        Raises
        ------
        KeyError
            When ``key`` is not available.
        """
        return self.get(key, raise_on_missing=True)

    @abstractmethod
    def __contains__(self, key):
        r"""Check if ``key`` is available.

        Returns
        -------
        bool
        """
        pass

    @abstractmethod    
    def keys(self):
        r"""Return a new view of the metadata keys.

        Returns
        -------
        Iterable of str

        """
        pass

    @abstractmethod   
    def items(self):
        r"""Return a new view of the metadata items.

        Returns
        -------
        Iterable of :obj:`(key,value)` pairs

        """
        pass

    @internal_key
    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        r"""Return the value for ``key``.
        
        Parameters
        ----------
        key: str
            Metadata key
        default: value
            Specify the default value for ``key``. Returned when ``key``
            is not found or its value is a missing value and raise_on_missing is ``False``.
        raise_on_missing: bool
            When it is True raises an exception if ``key`` is not found or
            it has a missing value.

        Returns
        -------
        value
            Returns the ``key`` value. Returns ``default`` if ``key`` is not found
            or it has a missing value and ``raise_on_missing`` is False.

        Raises
        ------
        KeyError
            If ``raise_on_missing`` is True and ``key`` is not found or it has
            a missing value.

        """
        if self.is_custom_key(key):
            return self._get_custom_key(
                key, default=default, astype=astype, raise_on_missing=raise_on_missing
            )
        else:
            return self._get(
                key, default=default, astype=astype, raise_on_missing=raise_on_missing
            )

    @abstractmethod
    def _get(self, key, astype=None, default=None, raise_on_missing=False):
        pass

    def is_custom_key(self, key):
        return key in self.CUSTOM_KEYS and key not in self

    def _get_custom_key(self, key, default=None, raise_on_missing=True, **kwargs):
        if self.is_custom_key(key):
            try:
                if key == DATETIME:
                    return self._valid_datetime()
            except Exception as e:
                if not raise_on_missing:
                    return default
                else:
                    raise KeyError(f"{key}, reason={e}")

    @abstractmethod
    def override(self, *args, **kwargs):
        r"""Change the metadata values and return a new object.

        :obj:`override` accepts another :obj:`Metadata` or a dict or
        an iterable of key/value pairs (as tuples or other iterables of length two).
        If keyword arguments are specified, the metadata is then updated with those
        key/value pairs.

        Examples
        --------
        >>> other = RawMetadata({"key1": 1, "key2": 2})
        >>> m1 = m.override(other)
        >>> m1 = m.override({"key1": 1, "key2": 2})
        >>> m1 = m.override([("key1", 1), ("key2", 2)])
        >>> m1 = m.override(key1=1, key2=2)
        """
        pass

    @internal_namespace
    def namespaces(self):
        r"""Return the available namespaces.

        Returns
        -------
        list of str
        """
        return self.NAMESPACES

    def as_namespace(self, namespace=None):
        r"""Return all the keys/values from a namespace.

        Parameters
        ----------
        namespace: str, None
            The namespace. When `namespace` is None or an empty :obj:`str` all the available
            keys/values are returned.

        Returns
        -------
        dict
            All the keys/values from the `namespace`.

        """
        if namespace is None or namespace == "":
            return {k: v for k, v in self.items()}
        return {}

    def dump(self, **kwargs):
        r"""Generate a dump from the metadata content."""
        return None

    def datetime(self):
        r"""Return the date and time of the field.

        Returns
        -------
        dict of datatime.datetime
            Dict with items "base_time" and "valid_time".


        >>> import earthkit.data
        >>> ds = earthkit.data.from_source("file", "tests/data/t_time_series.grib")
        >>> ds[4].datetime()
        {'base_time': datetime.datetime(2020, 12, 21, 12, 0),
        'valid_time': datetime.datetime(2020, 12, 21, 18, 0)}

        """
        return {
            "base_time": self._base_datetime(),
            "valid_time": self._valid_datetime(),
        }

    @abstractmethod
    def _base_datetime(self):
        pass

    @abstractmethod
    def _valid_datetime(self):
        pass

    @property
    def geography(self):
        r""":obj:`Geography`: Get geography description.

        If it is not available None is returned.
        """
        return None
   
    def ls_keys(self):
        r"""Return the keys to be used with the :meth:`ls` method."""
        return self.LS_KEYS

    def describe_keys(self):
        r"""Return the keys to be used with the :meth:`describe` method."""
        return self.DESCRIBE_KEYS

    def index_keys(self):
        r"""Return the keys to be used with the :meth:`indices` method."""
        return self.INDEX_KEYS
    
    def data_format(self):
        return self.DATA_FORMAT

    def _hide_internal(self):
        self._internal = False


class RawMetadata(Metadata):
    r"""Metadata implementation based on key/value pairs.

    >>> from earthkit.data.core.metadata import RawMetadata
    >>> md = RawMetadata({"shortName": "2t", "perturbationNumber": 5})
    >>> md = RawMetadata([("shortName", "2t"), ("perturbationNumber", 5)])
    >>> md = RawMetadata(shortName="2t", perturbationNumber=5)
    >>> md
    RawMetadata({'shortName': '2t', 'perturbationNumber': 5})
    >>> md2 = RawMetadata(md)
    >>> md2
    RawMetadata({'shortName': '2t', 'perturbationNumber': 5})

    Value access:

    >>> "shortName" in md
    True
    >>> md["shortName"]
    '2t'
    >>> md.get("shortName")
    '2t'
    >>> "step" in md
    False
    >>> md.get("step")
    >>> md.get("step", 0)
    0

    Examples
    --------
    - :ref:`/examples/metadata.ipynb`

    """

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)
        
    def override(self, *args, **kwargs):
        d = dict(**self._d)
        d.update(*args, **kwargs)
        return RawMetadata(d)

    def __len__(self):
        return len(self._d)

    def __contains__(self, key):
        return key in self._d

    def _get(self, key, astype=None, default=None, raise_on_missing=False):
        if not raise_on_missing:
            v = self._d.get(key, default)
        else:
            v = self._d[key]

        if astype is not None:
            try:
                return astype(v)
            except Exception:
                return None
        return v

    def keys(self):
        return self._d.keys()

    def items(self):
        return self._d.items()
    
    def _base_datetime(self):
        return None
    
    def _valid_datetime(self):
        return None
    
    def as_namespace(self, namespace):
        return {}

    def __repr__(self):
        return f"{self.__class__.__name__}({self._d.__repr__()})"
