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


def spec_aliases(cls) -> type:
    """
    Add alias properties to the class.

    Parameters
    ----------
    cls : type
        The class to which aliases will be added.

    Returns
    -------
    type
        The class with alias properties added.
    """
    aliases = getattr(cls, "ALIASES", None)
    if aliases:
        for alias, method in aliases.items():

            def _make(method):
                def _f(self):
                    return getattr(self, method)

                return _f

            setattr(
                cls,
                alias,
                property(fget=_make(method), doc=f"Return the {alias}. Alias for :obj:`{method}`."),
            )

    all_keys = list(cls.KEYS)
    if aliases:
        all_keys.extend(list(aliases.keys()))

    cls.ALL_KEYS = tuple(set(all_keys))
    return cls


def normalise_set_kwargs(
    spec: "Spec",
    *args: dict,
    add_spec_keys: bool = True,
    extra_keys=None,
    remove_nones: bool = False,
    **kwargs,
) -> dict:
    """
    Normalise and merge keyword arguments for the set method.

    Parameters
    ----------
    spec : Spec
        The specification object.
    *args : dict
        Additional dictionaries to merge.
    add_spec_keys : bool, optional
        Whether to add missing spec keys, by default True.
    **kwargs
        Additional keyword arguments.

    Returns
    -------
    dict
        The normalised keyword arguments.
    """
    kwargs = kwargs.copy()

    for a in args:
        if a is None:
            continue
        if isinstance(a, dict):
            kwargs.update(a)
            continue
        raise ValueError(f"Cannot use arg={a} in set() method. Only dict allowed.")

    _kwargs = {}
    for k, v in kwargs.items():
        k = spec.ALIASES.get(k, k)
        if k in spec.KEYS or (extra_keys and k in extra_keys):
            _kwargs[k] = v

    if add_spec_keys:
        for k in spec.KEYS:
            if k not in _kwargs:
                _kwargs[k] = getattr(spec, k)

    if remove_nones:
        _kwargs = {k: v for k, v in _kwargs.items() if v is not None}

    return _kwargs


class Aliases(dict):
    def __init__(self, d: dict = None) -> None:
        """
        Initialise the Aliases dictionary.

        Parameters
        ----------
        d : dict
            Dictionary of aliases.
        """
        r = {}
        d = d or {}
        for k, v in d.items():
            if isinstance(v, str):
                r[v] = k
            else:
                for x in v:
                    r[x] = k
        super().__init__(r)


class Spec(metaclass=ABCMeta):
    KEYS = tuple()
    ALIASES = Aliases()
    ALL_KEYS = tuple()

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict) -> "Spec":
        """
        Create a Spec instance from a dictionary.

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

    # @classmethod
    # @abstractmethod
    # def from_grib(cls, handle) -> "Spec":
    #     """
    #     Create a Spec instance from a GRIB handle.

    #     Parameters
    #     ----------
    #     handle
    #         GRIB handle object.

    #     Returns
    #     -------
    #     Spec
    #         The created Spec instance.
    #     """
    #     pass

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
    def set(self, *args, **kwargs) -> "Spec":
        """
        Create a new Spec instance with updated data.

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


class SimpleSpec(Spec):
    _private = None

    def _set_private_data(self, name, data):
        if self._private is None:
            self._private = {}
        self._private[name] = data

    def get_private_data(self, name, default=None):
        if self._private is not None:
            return self._private.get(name, default)
        return default

    def _copy_private_data(self, other):
        if other._private is not None:
            self._private = other._private.copy()

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
