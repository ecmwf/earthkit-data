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

from earthkit.data.field.spec.spec import Aliases


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


class FieldPart(metaclass=ABCMeta):
    """Abstract base class for Field parts.

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
    NAMESPACE_KEYS : tuple
        A tuple of keys that should be included in the namespace represented by the FieldPart.

    """

    KEYS = tuple()
    ALIASES = Aliases()
    ALL_KEYS = tuple()
    NAME = None
    NAMESPACE_KEYS = None

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
        Spec
            The created Spec instance.
        """
        pass

    @property
    @abstractmethod
    def spec(self) -> "FieldPart":
        """Return the spec of the FieldPart."""
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
        FieldPart
            The created FieldPart instance.
        """
        pass

    @abstractmethod
    def namespace(self, *args):
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
    def __getstate__(self):
        """Return the state for pickling."""
        pass

    @abstractmethod
    def __setstate__(self, state):
        """Set the state from pickling."""
        pass


class SimpleFieldPart(FieldPart):
    """A FieldPart providing basic implementations for the :obj:`get` method."""

    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        def _cast(v):
            if callable(astype):
                try:
                    return astype(v)
                except Exception:
                    return None
            return v

        if key in self.ALL_KEYS:
            try:
                v = getattr(self, key)
                if astype and v is not None:
                    v = _cast(v)
                return v
            except Exception:
                pass

        if raise_on_missing:
            raise KeyError(f"Key {key} not found in specification")

        return default


class SpecFieldPart(SimpleFieldPart):
    """A FieldPart that wraps a specification object.

    Parameters
    ----------
    spec : SPEC_CLS

    Attributes
    ----------
    spec : SPEC_CLS
        The type of the specification object wrapped by the FieldPart. To be
        defined in subclasses.

    Notes
    -----
    This class is still abstract and cannot be instantiated directly. Subclasses
    must define the SPEC_CLS attribute to specify the type of the specification
    object they wrap. They also need to implement the :obj:`get_grib_context` method.

    """

    SPEC_CLS = None

    def __init__(self, spec: Any) -> None:
        assert isinstance(spec, self.SPEC_CLS), type(spec)
        self._spec = spec

    @classmethod
    def from_dict(cls, d: dict, **kwargs) -> "SpecFieldPart":
        """Create a SpecFieldPart object from a dictionary."""
        data = cls.SPEC_CLS.from_dict(d, **kwargs)
        return cls(data)

    @classmethod
    def from_spec(cls, spec: Any) -> "SpecFieldPart":
        """Create a SpecFieldPart object from a specification object."""
        return cls(spec)

    @property
    def spec(self) -> Any:
        """Return the specification object."""
        return self._spec

    def set(self, *args, **kwargs) -> "SpecFieldPart":
        """Create a new SpecFieldPart instance with updated specification data."""
        data = self._spec.set(*args, **kwargs)
        return self.from_spec(data)
        # return type(self)(data)

    def namespace(self, owner: Any, name: str, result: dict) -> None:
        """Populate the namespace dictionary for this SpecFieldPart."""
        if name is None or name == self.NAME or (isinstance(name, (list, tuple)) and self.NAME in name):
            if self.NAMESPACE_KEYS:
                r = {k: getattr(self.spec, k) for k in self.NAMESPACE_KEYS}
                result[self.NAME] = r
            else:
                result[self.NAME] = dict()

    def check(self, owner: Any) -> None:
        """Default check implementation."""
        pass

    def __getstate__(self) -> dict:
        state = {}
        state["spec"] = self._spec
        return state

    def __setstate__(self, state) -> None:
        self.__init__(spec=state["spec"])
