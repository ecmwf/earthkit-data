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

            def _f(self):
                return getattr(self, method)

            setattr(cls, alias, property(fget=_f, doc=f"Return the {alias}. Alias for :obj:`{method}`."))

    all_keys = list(cls.KEYS)
    if aliases:
        all_keys.extend(list(aliases.keys()))

    cls.ALL_KEYS = tuple(set(all_keys))
    return cls


def normalise_set_kwargs(spec: "Spec", *args: dict, add_spec_keys: bool = True, **kwargs) -> dict:
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
    _kwargs = kwargs.copy()

    for a in args:
        if a is None:
            continue
        if isinstance(a, dict):
            _kwargs.update(a)
            continue
        raise ValueError(f"Cannot use arg={a} in set() method. Only dict allowed.")

    for k, v in kwargs.items():
        k = spec.ALIASES.get(k, k)
        if k in spec.KEYS:
            _kwargs[k] = v

    if add_spec_keys:
        for k in spec.KEYS:
            if k not in _kwargs:
                _kwargs[k] = getattr(spec, k)

    return _kwargs


def remove_spec_keys(spec: "Spec", d: dict) -> None:
    """
    Remove all spec keys from the given dictionary.

    Parameters
    ----------
    spec : Spec
        The specification object.
    d : dict
        The dictionary from which to remove keys.
    """
    if spec.ALL_KEYS:
        for k in d.keys():
            if k in spec.ALL_KEYS:
                del d[k]


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

    @classmethod
    @abstractmethod
    def from_grib(cls, handle) -> "Spec":
        """
        Create a Spec instance from a GRIB handle.

        Parameters
        ----------
        handle
            GRIB handle object.

        Returns
        -------
        Spec
            The created Spec instance.
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
