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
            method = getattr(cls.SPEC_CLS, method_name)

            print(f"Adding method {method} from {cls.SPEC_CLS}.{method_name}")

            def _make(method):
                def _f(self):
                    return getattr(self._spec, method)

                return _f

            setattr(cls, method_name, property(fget=_make(method_name)))

        setattr(cls, "ALL_KEYS", all_keys)

        print(f"ALL_KEYS for {cls}: {cls.ALL_KEYS}")
        return cls

    return decorator


class FieldMember(metaclass=ABCMeta):
    KEYS = tuple()
    ALIASES = Aliases()
    ALL_KEYS = tuple()
    NAME = None

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict) -> "FieldMember":
        """
        Create a FieldMember instance from a dictionary.

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
    def spec(self):
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
    def set(self, *args, **kwargs) -> "FieldMember":
        """
        Create a new FieldMember instance with updated data.

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
        """
        pass

    @abstractmethod
    def namespace(self, *args):
        pass

    @abstractmethod
    def check(self, owner):
        pass

    @abstractmethod
    def get_grib_context(self, context):
        pass

    @abstractmethod
    def __getstate__(self):
        pass

    @abstractmethod
    def __setstate__(self, state):
        pass


class SimpleFieldMember(FieldMember):
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


class SpecFieldMember(SimpleFieldMember):
    SPEC_CLS = None

    def __init__(self, spec) -> None:
        assert isinstance(spec, self.SPEC_CLS)
        self._spec = spec

    @classmethod
    def from_dict(cls, d):
        """Create a Time object from a dictionary."""
        data = cls.SPEC_CLS.from_dict(d)
        return cls(data)

    @property
    def spec(self):
        """Return the level layer."""
        return self._spec

    # def get_grib_context(self, context) -> dict:
    #     from earthkit.data.specs.grib.parameter import COLLECTOR

    #     COLLECTOR.collect(self, context)

    # def get(self, key, default=None, *, astype=None, raise_on_missing=False):
    #     def _cast(v):
    #         if callable(astype):
    #             try:
    #                 return astype(v)
    #             except Exception:
    #                 return None
    #         return v

    #     if key in self.ALL_KEYS:
    #         try:
    #             v = getattr(self, key)
    #             if astype and v is not None:
    #                 v = _cast(v)
    #             return v
    #         except Exception:
    #             pass

    #     if raise_on_missing:
    #         raise KeyError(f"Key {key} not found in specification")

    #     return default

    def set(self, *args, **kwargs):
        data = self._spec.set(*args, **kwargs)
        return type(self)(data)

    def namespace(self, owner, name, result):
        if name is None or name == self.NAME or (isinstance(name, (list, tuple)) and self.NAME in name):
            result[self.NAME] = self.to_dict()

    def check(self, owner):
        pass

    def __getstate__(self):
        state = {}
        state["spec"] = self._spec
        return state

    def __setstate__(self, state):
        self.__init__(spec=state["spec"])
