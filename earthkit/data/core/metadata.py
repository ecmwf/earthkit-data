# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import ABCMeta, abstractmethod


class Metadata(metaclass=ABCMeta):
    r"""Base class to represent metadata.

    Metadata is a dict-like immutable object. Modification is possible
    with :obj:`override`, which always creates new object.

    Implemented in subclasses: :obj:`RawMetadata`, :obj:`GribMetadata`.

    Examples
    --------
    - :ref:`/examples/metadata.ipynb`

    """

    def __iter__(self):
        """Return an iterator over the metadata keys."""
        return iter(self.keys())

    @abstractmethod
    def __len__(self):
        r"""Return the number of metadata entries."""

    @abstractmethod
    def __getitem__(self, key):
        r"""Return the value for ``key``.

        Raises
        ------
        KeyError
            When ``key`` is not available.
        """
        pass

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

    @abstractmethod
    def get(self, key, default=None):
        r"""Return the value for ``key``.

        Parameters
        ----------
        key: str
            Metadata key
        default:
            When ``key`` is not found ``default`` is returned.
        """
        pass

    def _get(self, key, astype=None, **kwargs):
        # when key is not available and no default is specified this
        # should raise KeyError
        if "default" in kwargs:
            default = kwargs.pop("default")
            v = self.get(key, default)
        else:
            v = self.__getitem__(key)

        if astype is None:
            try:
                return astype(v)
            except Exception:
                return None
        return v

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
        return []

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
        return {}

    def dump(self, **kwargs):
        r"""Generate a dump from the metadata content."""
        return None


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
    :ref:`/examples/metadata.ipynb`

    """

    def __init__(self, *args, **kwargs):
        self._d = dict(*args, **kwargs)

    def __len__(self):
        return len(self._d)

    def keys(self):
        return self._d.keys()

    def items(self):
        return self._d.items()

    def __getitem__(self, key):
        return self._d.__getitem__(key)

    def __contains__(self, key):
        return key in self._d

    def get(self, key, default=None):
        return self._d.get(key, default)

    def override(self, *args, **kwargs):
        d = dict(**self._d)
        d.update(*args, **kwargs)
        return RawMetadata(d)

    def __repr__(self):
        return f"{self.__class__.__name__}({self._d.__repr__()})"


class FieldMetadata(Metadata):
    r"""Metadata implementation for fields."""

    @abstractmethod
    def latitudes(self):
        r"""Return the latitudes of the field.

        Returns
        -------
        ndarray
        """
        pass

    @abstractmethod
    def longitudes(self):
        r"""Return the longitudes of the field.

        Returns
        -------
        ndarray
        """
        pass

    @abstractmethod
    def x(self):
        r"""Return the x coordinates in the field's original CRS.

        Returns
        -------
        ndarray
        """
        pass

    @abstractmethod
    def y(self):
        r"""Return the y coordinates in the field's original CRS.

        Returns
        -------
        ndarray
        """
        pass

    @abstractmethod
    def shape(self):
        r"""Return the shape of the field.

        Returns
        -------
        tuple
        """
        pass

    @abstractmethod
    def _unique_grid_id(self):
        pass

    @abstractmethod
    def projection(self):
        r"""Return information about the field's projection.

        Returns
        -------
        :obj:`Projection`
        """
        pass

    @abstractmethod
    def bounding_box(self):
        r"""Return the bounding box of the field.

        Returns
        -------
        :obj:`BoundingBox <data.utils.bbox.BoundingBox>`
        """
        pass

    @abstractmethod
    def datetime(self):
        r"""Return the date and time of the field.

        Returns
        -------
        dict of datatime.datetime
            Dict with items "base_time" and "valid_time".
        """
        pass

    @abstractmethod
    def ls_keys(self):
        r"""Return the keys to be used with the :meth:`ls` method."""
        pass

    @abstractmethod
    def describe_keys(self):
        r"""Return the keys to be used with the :meth:`describe` method."""
        pass

    @abstractmethod
    def index_keys(self):
        r"""Return the keys to be used with the :meth:`indices` method."""
        pass
