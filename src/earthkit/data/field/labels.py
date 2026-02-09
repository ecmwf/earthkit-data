# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from abc import abstractmethod
from typing import Any

from .core import FieldPart


class Labels(FieldPart):
    NAME = "labels"

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


class SimpleLabels(dict, Labels):
    ALL_KEYS = []  # All keys are allowed

    @classmethod
    def from_dict(cls, d: dict, allow_unused=False) -> "SimpleLabels":
        """Create a SimpleLabels object from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing parameter data.

        Returns
        -------
        SimpleLabels
            The created SimpleLabels instance.
        """
        if not isinstance(d, dict):
            raise TypeError("labels must be a dictionary")
        return cls(d)

    @classmethod
    def from_any(cls, data: Any, dict_kwargs=None) -> "Labels":
        """Create a SimpleLabels object from any input.

        Parameters
        ----------
        data: Any
            The input data from which to create the SimpleLabels instance.
        dict_kwargs: dict, optional
            Additional keyword arguments to be passed when creating the instance from
            a dictionary.

        Returns
        -------
        SimpleLabels
            An instance of SimpleLabels. If the input is already an instance
            of SimpleLabels, it is returned as is. Otherwise, it is assumed to be a
            specification object and a new SimpleLabels instance is created from it.
        """
        if isinstance(data, cls):
            return data
        elif isinstance(data, dict):
            dict_kwargs = dict_kwargs or {}
            return cls.from_dict(data, **dict_kwargs)

        raise TypeError(f"Cannot create {cls.__name__} from {type(data)}")

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

    def dump(self, owner: Any, name: str, result: dict, prefix_keys=False) -> None:
        """Populate the namespace dictionary for this SpecFieldPart."""

        def _prefix(key):
            return f"{self.NAME}.{key}" if prefix_keys else key

        if name is None or name == self.NAME or (isinstance(name, (list, tuple)) and self.NAME in name):
            r = {_prefix(k): v for k, v in self.items()}
            result[self.NAME] = r

    def get_grib_context(self, context):
        pass
