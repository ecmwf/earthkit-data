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

FieldComponent: TypeAlias = Any


class FieldComponentHandler(metaclass=ABCMeta):
    """Abstract base class for Field component handlers.

    A FieldComponent represents a component of a Field, such as time, vertical level, or
    processing information. It stores a specification object, the "spec",
    and provides methods to access and manipulate the specification data.

    It is meant to be used internally by the Field class and its members.

    Attributes
    ----------
    KEYS : tuple
        A tuple of keys from the "spec" that can be accessed as properties on the FieldComponent.
    ALIASES : Aliases
        An Aliases object that maps alternative key names to their canonical names.
    ALL_KEYS : tuple
        A tuple of all keys, including aliases, that can be accessed from the FieldComponent.
    NAME : str
        The name of the FieldComponent to be used as an identifier in the Field. It is also the
        name of the corresponding namespace in the Field.
    DUMP_KEYS : tuple
        A tuple of keys that should be included in the namespace represented by the FieldComponent.

    """

    KEYS = tuple()
    NAME = None

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict) -> "FieldComponentHandler":
        """
        Create a FieldComponentHandler instance from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing specification data.

        Returns
        -------
        FieldComponentHandler
            The created FieldComponentHandler instance.
        """
        pass

    @classmethod
    @abstractmethod
    def from_any(cls, **kwargs) -> "FieldComponentHandler":
        """
        Create a FieldComponentHandler instance from any allowed input types.

        Parameters
        ----------
        kwargs : dict
            Keyword arguments containing specification data.

        Returns
        -------
        FieldComponentHandler
            The created FieldComponentHandler instance.
        """
        pass

    # @classmethod
    # @abstractmethod
    # def create_empty(cls) -> "FieldComponentHandler":
    #     pass

    @property
    @abstractmethod
    def component(self) -> "FieldComponent":
        """Return the FieldComponent."""
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
    def set(self, *args, **kwargs) -> "FieldComponentHandler":
        """
        Create a new FieldComponent instance with updated data.

        Parameters
        ----------
        *args
            Positional arguments.
        **kwargs
            Keyword arguments.

        Returns
        -------
        FieldComponent
            The created FieldComponent instance.
        """
        pass

    @abstractmethod
    def dump(self, *args, **kwargs) -> None:
        """Populate the namespace dictionary for this FieldComponent."""
        pass

    @abstractmethod
    def check(self, owner):
        """Check the FieldComponent for consistency with the owner Field."""
        pass

    @abstractmethod
    def get_grib_context(self, context):
        """Populate the GRIB context dictionary for this FieldComponent."""
        pass

    @abstractmethod
    def __contains__(self, key):
        """Check if the key is in the FieldComponent."""
        pass

    @abstractmethod
    def __getstate__(self):
        """Return the state for pickling."""
        pass

    @abstractmethod
    def __setstate__(self, state):
        """Set the state from pickling."""
        pass


class LazyFieldComponentHandler(metaclass=ABCMeta):
    _exception = None

    @property
    @abstractmethod
    def _handler(self):
        pass

    def __getattr__(self, name):
        if self._exception is not None:
            raise self._exception(name)
        return getattr(self._handler, name)


class SimpleFieldComponentHandler(FieldComponentHandler):
    """A FieldComponent that wraps a specification object.

    Parameters
    ----------
    component : Component

    Attributes
    ----------
    component : Component
        The type of the specification object wrapped by the FieldComponent. To be
        defined in subclasses.

    Notes
    -----
    This class is still abstract and cannot be instantiated directly. Subclasses
    must define the SPEC_CLS attribute to specify the type of the specification
    object they wrap. They also need to implement the :obj:`get_grib_context` method.

    """

    COMPONENT_CLS = None
    COMPONENT_MAKER = None

    def __init__(self, component: Any) -> None:
        assert isinstance(
            component, self.COMPONENT_CLS
        ), f"type(component)={type(component)}, expected {self.COMPONENT_CLS}"
        self._component = component

    @classmethod
    def from_dict(cls, d: dict, **kwargs) -> "SimpleFieldComponentHandler":
        """Create a SimpleFieldComponent object from a dictionary."""
        component = cls.COMPONENT_MAKER(d, **kwargs)
        return cls(component)

    @classmethod
    def from_component(cls, component: Any) -> "SimpleFieldComponentHandler":
        """Create a SimpleFieldComponent object from a component object."""
        return cls(component)

    @classmethod
    def from_any(cls, data: Any, dict_kwargs=None) -> "SimpleFieldComponentHandler":
        """Create a SimpleFieldComponent object from any input.

        Parameters
        ----------
        data: Any
            The input data from which to create the SimpleFieldComponent instance.
        dict_kwargs: dict, optional
            Additional keyword arguments to be passed when creating the instance from
            a dictionary.

        Returns
        -------
        SimpleFieldComponentHandler
            An instance of SimpleFieldComponentHandler. If the input is already an instance
            of SimpleFieldComponentHandler, it is returned as is. Otherwise, it is assumed to be a
            component object and a new SimpleFieldComponentHandler instance is created from it.
        """
        if isinstance(data, (cls, LazyFieldComponentHandler)):
            return data
        elif isinstance(data, dict):
            dict_kwargs = dict_kwargs or {}
            return cls.from_dict(data, **dict_kwargs)
        elif isinstance(data, cls.COMPONENT_CLS):
            return cls.from_component(data)

        raise TypeError(f"Cannot create {cls.__name__} from {type(data)}")

    @classmethod
    def create_empty(cls) -> "SimpleFieldComponentHandler":
        raise NotImplementedError(f"{cls.__name__}.create_empty is not implemented")

    @property
    def component(self) -> Any:
        """Return the component object."""
        return self._component

    def __contains__(self, name):
        """Check if the key is in the component."""
        return name in self._component

    def get(self, key, default=None, *, astype=None, raise_on_missing=False):
        return self._component.get(key, default=default, astype=astype, raise_on_missing=raise_on_missing)

    def set(self, *args, **kwargs) -> "SimpleFieldComponentHandler":
        """Create a new SimpleFieldComponentHandler instance with updated component data."""
        component = self._component.set(*args, **kwargs)
        return self.from_component(component)

    def dump(self, owner: Any, name: str, result: dict, prefix_keys=False) -> None:
        """Populate the namespace dictionary for this SpecFieldComponent."""

        def _prefix(key):
            return f"{self.NAME}.{key}" if prefix_keys else key

        if name is None or name == self.NAME or (isinstance(name, (list, tuple)) and self.NAME in name):
            r = {_prefix(k): v for k, v in self.component.to_dict().items()}
            result[self.NAME] = r

    def check(self, owner: Any) -> None:
        """Default check implementation."""
        pass

    def __getstate__(self) -> dict:
        state = {}
        state["component"] = self._component
        return state

    def __setstate__(self, state) -> None:
        self.__init__(component=state["component"])
