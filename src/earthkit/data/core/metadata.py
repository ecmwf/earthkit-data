# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import functools
from abc import ABCMeta
from abc import abstractmethod


class MetadataAccessor:
    r"""Helper class to access metadata using dedicated methods on a metadata object.

    Parameters
    ----------
    conf: dict
        Dictionary mapping method names to metadata keys that should be accessed with the given method.m
        The metadata keys can be a string or a list/tuple of strings.
    aliases: list of iterables, optional
        Groups of metadata keys that should be accessed with the same method.
    """

    def __init__(self, conf, aliases=None):
        self.keys = set()
        self.methods = dict()
        aliases = aliases or dict()
        for k, v in conf.items():
            if isinstance(v, str):
                self.keys.add(v)
            else:
                self.keys.update(v)

            if isinstance(v, str):
                v = [v]

            for kv in v:
                self.methods[kv] = k

            for gr in aliases:
                if any(gr_k in v for gr_k in gr):
                    for gr_k in gr:
                        if gr_k not in self.keys:
                            self.methods[gr_k] = k
                            self.keys.add(gr_k)

    def __contains__(self, key):
        return key in self.keys

    def get(self, md, key, default=None, *, astype=None, raise_on_missing=False):
        """Return the value for ``key``.

        Parameters
        ----------
        md: Metadata
            Metadata object featuring the method to access the value of ``key``.
        key: str
            Metadata key
        """
        try:
            v = getattr(md, self.methods[key])()
            # TODO: add automatic conversion support
            if self.methods[key].endswith("_datetime"):
                if v is not None:
                    return v.isoformat()
            return v
        except Exception as e:
            if not raise_on_missing:
                return default
            else:
                raise KeyError(f"{key}, reason={e}")


def cacheable_metadata(func):
    @functools.wraps(func)
    def wrapped(self, key, default=None, *, astype=None, raise_on_missing=False):
        if self._cache is not None:
            cache_id = (key, default, astype, raise_on_missing)
            if cache_id in self._cache:
                return self._cache[cache_id]

            v = func(self, key, default=default, astype=astype, raise_on_missing=raise_on_missing)
            self._cache[cache_id] = v
            return v
        else:
            return func(self, key, default=default, astype=astype, raise_on_missing=raise_on_missing)

    return wrapped


def custom_accessor(func):
    @functools.wraps(func)
    def wrapped(self, key, *args, **kwargs):
        if self.CUSTOM_ACCESSOR and key in self.CUSTOM_ACCESSOR:
            return self.CUSTOM_ACCESSOR.get(self, key, *args, **kwargs)
        return func(self, key, *args, **kwargs)

    return wrapped


class Metadata(metaclass=ABCMeta):
    r"""Base class to represent metadata.

    Metadata is a dict-like immutable object. Modification is possible
    with :obj:`override`, which always creates a new object.

    Implemented in subclasses: :obj:`RawMetadata`, :obj:`GribMetadata`.

    Parameters
    ----------
    cache: bool, dict-like, optional
        Enable caching of all the calls to :meth:`get`. Default is False. The cache
        is attached to the instance.

    Examples
    --------
    - :ref:`/examples/metadata.ipynb`

    """

    DATA_FORMAT = None
    NAMESPACES = []
    LS_KEYS = []
    DESCRIBE_KEYS = []
    INDEX_KEYS = []
    ALIASES = []
    CUSTOM_ACCESSOR = None

    _cache = None

    def __init__(self, cache=False):
        if cache is True:
            self._cache = dict()
        elif cache is not False and cache is not None:
            self._cache = cache

    @abstractmethod
    def __iter__(self):
        """Return an iterator over the metadata keys."""
        pass

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
        r"""Return the metadata keys.

        Returns
        -------
        Iterable of str

        """
        pass

    @abstractmethod
    def items(self):
        r"""Return the metadata items.

        Returns
        -------
        Iterable of :obj:`(key,value)` pairs

        """
        pass

    @cacheable_metadata
    @custom_accessor
    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        r"""Return the value for ``key``.

        When the instance is created with ``cache=True`` all the result is cached.

        Parameters
        ----------
        key: str
            Metadata key
        default: value
            Specify the default value for ``key``. Returned when ``key``
            is not found or its value is a missing value and raise_on_missing is ``False``.
        astype: type as str, int or float
            Return/access type for ``key``. When it is supported ``astype`` is passed to the
            underlying metadata accessor as an option. Otherwise the value is
            cast to ``astype`` after it is taken from the accessor.
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
        return self._get(key, default=default, astype=astype, raise_on_missing=raise_on_missing)

    @abstractmethod
    def _get(self, key, astype=None, default=None, raise_on_missing=False):
        pass

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
            "base_time": self.base_datetime(),
            "valid_time": self.valid_datetime(),
        }

    @abstractmethod
    def base_datetime(self):
        pass

    @abstractmethod
    def valid_datetime(self):
        pass

    @property
    def geography(self):
        r""":obj:`Geography`: Get geography description.

        If it is not available None is returned.
        """
        return None

    @property
    def gridspec(self):
        r""":class:`~data.core.gridspec.GridSpec`: Get grid description.

        If it is not available None is returned.
        """
        return None if self.geography is None else self.geography.gridspec()

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
        r"""Return the underlying data format.

        Returns
        -------
        str

        """
        return self.DATA_FORMAT

    def _hide_internal_keys(self):
        return self


class WrappedMetadata:
    def __init__(self, metadata, extra=None, hidden=None, merge=True):
        self.metadata = metadata
        self.extra = extra if extra is not None else dict()
        self.hidden = hidden if hidden is not None else []

        for k in self.hidden:
            if k in self.extra:
                raise ValueError(f"Hidden key {k} is also in extra")

        if merge and isinstance(metadata, WrappedMetadata):
            self.metadata = metadata.metadata
            v = dict(**metadata.extra)
            v.update(self.extra)
            self.extra = v
            for x in metadata.hidden:
                if x not in self.hidden:
                    self.hidden.append(x)

    def __len__(self):
        r"""Return the number of metadata entries."""
        return len(self.keys())

    def __contains__(self, key):
        r"""Check if ``key`` is available.

        Returns
        -------
        bool
        """
        if self._is_hidden(key):
            return False
        if key in self.extra:
            return True
        return key in self.metadata

    def _is_hidden(self, key):
        return key in self.hidden

    def keys(self):
        r"""Return the metadata keys.

        Returns
        -------
        Iterable of str

        """
        r = list(self.metadata.keys())
        if self.extra:
            r += [x for x in self.extra if x not in r]
        if self.hidden:
            r = [x for x in r if x not in self.hidden]
        return r

    def items(self):
        r"""Return the metadata items.

        Returns
        -------
        Iterable of :obj:`(key,value)` pairs

        """
        for k in self.keys():
            if self._is_hidden(k):
                continue
            if k in self.extra:
                yield k, self.extra[k]
            else:
                yield k, self.metadata.get(k)

    def get(self, key, default=None, *, astype=None, raise_on_missing=False, **kwargs):
        if self._is_hidden(key):
            if raise_on_missing:
                raise KeyError(key)
            return default

        if key in self.extra:
            v = self.extra[key]
            if astype is not None and v is not None:
                try:
                    return astype(v)
                except Exception:
                    return None
            return v

        return self.metadata.get(
            key, default=default, astype=astype, raise_on_missing=raise_on_missing, **kwargs
        )

    def override(self, *args, **kwargs):
        md = self.metadata.override(*args, **kwargs)
        return self.__class__(md, self.extra, hidden=self.hidden, merge=True)

    def __getitem__(self, key):
        return self.get(key, raise_on_missing=True)

    def __getattr__(self, name):
        return getattr(self.metadata, name)


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
        super().__init__()

    def override(self, *args, **kwargs):
        d = dict(**self._d)
        d.update(*args, **kwargs)
        return RawMetadata(d)

    def __len__(self):
        return len(self._d)

    def __contains__(self, key):
        return key in self._d

    def __iter__(self):
        return iter(self.keys())

    def _get(self, key, default=None, astype=None, raise_on_missing=False):
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

    def base_datetime(self):
        return None

    def valid_datetime(self):
        return None

    def as_namespace(self, namespace):
        return {}

    def __repr__(self):
        return f"{self.__class__.__name__}({self._d.__repr__()})"
