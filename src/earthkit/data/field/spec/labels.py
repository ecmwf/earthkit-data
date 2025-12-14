# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import abstractmethod

from .spec import Spec


class Labels(Spec):
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

    # @abstractmethod
    # def get(self, key, default=None, *, astype=None, raise_on_missing=False):
    #     r"""Return the value for ``key``.

    #     Parameters
    #     ----------
    #     key: str
    #         Metadata key
    #     default: value
    #         Specify the default value for ``key``. Returned when ``key``
    #         is not found or its value is a missing value and raise_on_missing is ``False``.
    #     astype: type as str, int or float
    #         Return/access type for ``key``. When it is supported ``astype`` is passed to the
    #         underlying metadata accessor as an option. Otherwise the value is
    #         cast to ``astype`` after it is taken from the accessor.
    #     raise_on_missing: bool
    #         When it is True raises an exception if ``key`` is not found or
    #         it has a missing value.

    #     Returns
    #     -------
    #     value
    #         Returns the ``key`` value. Returns ``default`` if ``key`` is not found
    #         or it has a missing value and ``raise_on_missing`` is False.

    #     Raises
    #     ------
    #     KeyError
    #         If ``raise_on_missing`` is True and ``key`` is not found or it has
    #         a missing value.

    #     """
    #     pass

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

    # @abstractmethod
    # def set(self, *args, **kwargs):
    #     r"""Set the value for ``key``."""
    #     pass


class SimpleLabels(dict, Labels):
    NAME = "labels"
    ALL_KEYS = []  # All keys are allowed

    @classmethod
    def from_dict(cls, d: dict, allow_unused=False) -> "SimpleLabels":
        return cls(d)

    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        def _cast(v):
            if callable(astype):
                try:
                    return astype(v)
                except Exception:
                    return None
            return v

        if not raise_on_missing:
            v = super().get(key, default)
        else:
            try:
                v = self[key]
            except KeyError:
                raise KeyError(f"Key {key} not found in Labels")

        if v is not None and astype:
            v = _cast(v)
        return v

    def set(self, *args, **kwargs):
        d = dict(self)
        d.update(*args, **kwargs)
        return SimpleLabels(d)

    # def __setitem__(self, key, value):
    #     raise TypeError("SimpleLabels object does not support item assignment")

    def check(self, owner):
        pass

    def namespace(self, *args):
        pass

    def get_grib_context(self, context):
        pass
