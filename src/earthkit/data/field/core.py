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
from typing import Any
from typing import TypeAlias

# from earthkit.data.field.part.spec import Aliases

FieldPart: TypeAlias = Any


def wrap_spec_methods(keys=None):
    if keys is None:
        keys = []

    def decorator(cls):
        all_keys = list(keys)
        for k, v in cls.SPEC_CLS._ALIASES.items():
            if v in keys:
                all_keys.append(k)

        for method_name in all_keys:
            # method = getattr(cls.SPEC_CLS, method_name)

            # print(f"Adding method {method} from {cls.SPEC_CLS}.{method_name}")

            def _make(method):
                def _f(self):
                    return getattr(self._spec, method)

                return _f

            setattr(cls, method_name, property(fget=_make(method_name)))

        setattr(cls, "ALL_KEYS", all_keys)

        # print(f"ALL_KEYS for {cls}: {cls.ALL_KEYS}")
        return cls

    return decorator


class FieldPartHandler(metaclass=ABCMeta):
    """Abstract base class for Field part handlers.

    A FieldPart represents a component of a Field, such as time, vertical level, or
    processing information. It stores a specification object, the "spec",
    and provides methods to access and manipulate the specification data.

    It is meant to be used internally by the Field class and its members.

    Attributes
    ----------
    KEYS : tuple
        A tuple of keys from the "spec" that can be accessed as properties on the FieldPart.
    ALIASES : Aliases
        An Aliases object that maps alternative key names to their canonical names.
    ALL_KEYS : tuple
        A tuple of all keys, including aliases, that can be accessed from the FieldPart.
    NAME : str
        The name of the FieldPart to be used as an identifier in the Field. It is also the
        name of the corresponding namespace in the Field.
    DUMP_KEYS : tuple
        A tuple of keys that should be included in the namespace represented by the FieldPart.

    """

    KEYS = tuple()
    NAME = None
    DUMP_KEYS = None

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict) -> "FieldPartHandler":
        """
        Create a FieldPart instance from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing specification data.

        Returns
        -------
        FieldPartHandler
            The created FieldPartHandler instance.
        """
        pass

    @classmethod
    @abstractmethod
    def from_any(cls, **kwargs) -> "FieldPartHandler":
        """
        Create a FieldPartHandler instance from any allowed input types.

        Parameters
        ----------
        kwargs : dict
            Keyword arguments containing specification data.

        Returns
        -------
        FieldPartHandler
            The created FieldPartHandler instance.
        """
        pass

    @property
    @abstractmethod
    def part(self) -> "FieldPart":
        """Return the FieldPart."""
        pass

    @abstractmethod
    def get(self, key, default=None, *, astype=None, raise_on_missing=False) -> "any":
        r"""Return the value for ``key``.

        Parameters
        ----------
        key: str
            Key
        default: value
            Specify the default value for ``key``. Returned when ``key``
            is not found or its value is a missing value and raise_on_missing is ``False``.
        astype: type as str, int or float
            Return/access type for ``key``. When it is supported ``astype`` is passed to the
            underlying accessor as an option. Otherwise the value is
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
        pass

    @abstractmethod
    def set(self, *args, **kwargs) -> "FieldPartHandler":
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
        FieldPart
            The created FieldPart instance.
        """
        pass

    @abstractmethod
    def namespace(self, *args, **kwargs) -> None:
        """Populate the namespace dictionary for this FieldPart."""
        pass

    @abstractmethod
    def check(self, owner):
        """Check the FieldPart for consistency with the owner Field."""
        pass

    @abstractmethod
    def get_grib_context(self, context):
        """Populate the GRIB context dictionary for this FieldPart."""
        pass

    @abstractmethod
    def __contains__(self, key):
        """Check if the key is in the FieldPart."""
        pass

    @abstractmethod
    def __getstate__(self):
        """Return the state for pickling."""
        pass

    @abstractmethod
    def __setstate__(self, state):
        """Set the state from pickling."""
        pass


class LazyFieldPartHandler(metaclass=ABCMeta):
    _exception = None

    @property
    @abstractmethod
    def _handler(self):
        pass

    def __getattr__(self, name):
        if self._exception is not None:
            raise self._exception(name)
        return getattr(self._handler, name)


class SimpleFieldPartHandler(FieldPartHandler):
    """A FieldPart that wraps a specification object.

    Parameters
    ----------
    part : Part

    Attributes
    ----------
    part : Part
        The type of the specification object wrapped by the FieldPart. To be
        defined in subclasses.

    Notes
    -----
    This class is still abstract and cannot be instantiated directly. Subclasses
    must define the SPEC_CLS attribute to specify the type of the specification
    object they wrap. They also need to implement the :obj:`get_grib_context` method.

    """

    PART_CLS = None
    PART_MAKER = None

    def __init__(self, part: Any) -> None:
        assert isinstance(part, self.PART_CLS), f"type(part)={type(part)}, expected {self.PART_CLS}"
        self._part = part

    @classmethod
    def from_dict(cls, d: dict, **kwargs) -> "SimpleFieldPartHandler":
        """Create a SimpleFieldPart object from a dictionary."""
        part = cls.PART_MAKER(d, **kwargs)
        return cls(part)

    @classmethod
    def from_part(cls, part: Any) -> "SimpleFieldPartHandler":
        """Create a SimpleFieldPart object from a part object."""
        return cls(part)

    @classmethod
    def from_any(cls, data: Any, dict_kwargs=None) -> "SimpleFieldPartHandler":
        """Create a SimpleFieldPart object from any input.

        Parameters
        ----------
        data: Any
            The input data from which to create the SimpleFieldPart instance.
        dict_kwargs: dict, optional
            Additional keyword arguments to be passed when creating the instance from
            a dictionary.

        Returns
        -------
        SimpleFieldPartHandler
            An instance of SimpleFieldPartHandler. If the input is already an instance
            of SimpleFieldPartHandler, it is returned as is. Otherwise, it is assumed to be a
            part object and a new SimpleFieldPartHandler instance is created from it.
        """
        if isinstance(data, (cls, LazyFieldPartHandler)):
            return data
        elif isinstance(data, dict):
            dict_kwargs = dict_kwargs or {}
            return cls.from_dict(data, **dict_kwargs)
        elif isinstance(data, cls.PART_CLS):
            return cls.from_part(data)

        raise TypeError(f"Cannot create {cls.__name__} from {type(data)}")

    @property
    def part(self) -> Any:
        """Return the part object."""
        return self._part

    def __contains__(self, name):
        """Check if the key is in the part."""
        return name in self._part

    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        return self._part.get(key, default=default, astype=astype, raise_on_missing=raise_on_missing)
        # if key in self:
        #     v = getattr(self._part, key)()
        #     if astype and v is not None and callable(astype):
        #         try:
        #             return astype(v)
        #         except Exception:
        #             return None
        #     return v

        # if raise_on_missing:
        #     raise KeyError(f"Key {key} not found in specification")

        # return default

    def set(self, *args, **kwargs) -> "SimpleFieldPartHandler":
        """Create a new SimpleFieldPartHandler instance with updated part data."""
        part = self._part.set(*args, **kwargs)
        return self.from_part(part)
        # return type(self)(data)

    def namespace(self, owner: Any, name: str, result: dict, prefix_keys=False) -> None:
        """Populate the namespace dictionary for this SpecFieldPart."""

        def _prefix(key):
            return f"{self.NAME}.{key}" if prefix_keys else key

        if name is None or name == self.NAME or (isinstance(name, (list, tuple)) and self.NAME in name):
            if self.NAMESPACE_KEYS:
                r = {_prefix(k): getattr(self.part, k)() for k in self.NAMESPACE_KEYS}
                result[self.NAME] = r
            else:
                result[self.NAME] = dict()

    def check(self, owner: Any) -> None:
        """Default check implementation."""
        pass

    def __getstate__(self) -> dict:
        state = {}
        state["part"] = self._part
        return state

    def __setstate__(self, state) -> None:
        self.__init__(part=state["part"])
