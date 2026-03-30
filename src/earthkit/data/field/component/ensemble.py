# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

from .component import SimpleFieldComponent, component_keys, mark_alias, mark_get_key


@component_keys
class EnsembleBase(SimpleFieldComponent):
    """Base class for the ensemble component of a field.

    This class defines the interface for ensemble components, which can represent
    different types of ensemble information.

    The ensemble information can be accessed by methods like :meth:`member`. Each of these
    methods has an associated key that can be used in the :meth:`get` method to retrieve the
    corresponding information. The list of supported keys are as follows:

    - "member"
    - "realization" (alias of "member")
    - "realisation" (alias of "member")

    Typically, this object is used as a component of a field, and can be accessed via the :attr:`ensemble`
    attribute of a field. The keys above can also be accessed via the :meth:`get` method of the field,
    using the "ensemble." prefix.

    The following example demonstrates how to access the ensemble information from a field using
    various methods and keys:

        >>> import earthkit.data as ekd
        >>> field = = ekd.from_source("sample", "ens_cf_pf.grib").to_fieldlist()[2]
        >>> field.ensemble.member()
        '1'
        >>> field.ensemble.get("member")
        '1'
        >>> field.get("ensemble.member")
        '1'

    The ensemble component is immutable. The :meth:`set` method to create a new
    instance with updated values. For example, the following code creates a new ensemble
    component with an updated member:

        >>> new_ensemble = field.ensemble.set(member="2")
        >>> new_ensemble.member()
        '2'

    We can also call the Field's :meth:`set` method to create a new field with an updated ensemble component:

        >>> new_field = field.set({"ensemble.member": "2"})
        >>> new_field.ensemble.member()
        '2'

    Parameters
    ----------
    member : str, int, optional
        The ensemble member, by default None.
    """

    @mark_get_key
    @abstractmethod
    def member(self) -> str:
        """Return the ensemble member."""
        pass

    @mark_alias("member")
    def realization(self) -> str:
        """Return the ensemble member (alias of `member`)."""
        pass

    @mark_alias("member")
    def realisation(self) -> str:
        """Return the ensemble member (alias of `member`)."""
        pass


def create_ensemble(d: dict) -> "EnsembleBase":
    """Create a EnsembleBase object from a dictionary.

    Parameters
    ----------
    d : dict
        Dictionary containing parameter data.

    Returns
    -------
    EnsembleBase
        The created EnsembleBase instance.
    """
    if not isinstance(d, dict):
        raise TypeError(f"Cannot create Ensemble from {type(d)}, expected dict")

    cls = Ensemble
    d1 = cls._normalise_create_kwargs(d, allowed_keys=("member",))
    return cls(**d1)


class EmptyEnsemble(EnsembleBase):
    """Empty ensemble component, representing the absence of ensemble information."""

    def member(self) -> None:
        """Return the ensemble member.

        An EmptyEnsemble does not contain any ensemble information, and this method returns None.
        """
        return None

    @classmethod
    def from_dict(cls, d: dict):
        """Create an EmptyEnsemble object from a dictionary."""
        if d:
            return cls()
        return cls()

    def to_dict(self):
        """Return a dictionary representation of the EmptyEnsemble."""
        return {"member": None}

    def set(self, *args, **kwargs):
        """Create a new instance with updated data.

        An EmptyEnsemble object cannot be updated, and this method raises a
        ValueError.
        """
        raise ValueError("Cannot set values on EmptyEnsemble")

    def __getstate__(self):
        return {}

    def __setstate__(self, state):
        self.__init__()


class Ensemble(EnsembleBase):
    """Ensemble component representing ensemble information.

    Parameters
    ----------
    member : str, int, optional
        The ensemble member, by default None. Internally stored as a string,
        so if an integer is provided, it will be converted to a string.
        None is treated as "0".
    """

    def __init__(self, member=None) -> None:
        if member is None:
            self._member = "0"
        elif isinstance(member, int):
            self._member = str(member)
        else:
            self._member = member

    def member(self) -> str:
        return self._member

    @classmethod
    def from_dict(cls, d: dict) -> "Ensemble":
        """Create a Ensemble object from a dictionary.

        Parameters
        ----------
        d : dict
            Dictionary containing parameter data.

            The dictionary can contain the following keys:

            - "member": The ensemble member.

        Returns
        -------
        Ensemble
            The created Ensemble instance.
        """
        return create_ensemble(d)

    def to_dict(self):
        """Return a dictionary representation of the Ensemble."""
        return {"member": self._member}

    def set(self, *args, **kwargs):
        """Create a new instance with updated data.

        Parameters
        ----------
        args : tuple
            Positional arguments containing time data. Only dictionaries are allowed.
        kwargs : dict
            Keyword arguments containing time data.


        The following keys can be provided to update the ensemble information:

            - "member": The ensemble member.

        """
        d = self._normalise_set_kwargs(*args, allowed_keys=("member",), **kwargs)

        if d:
            return self.from_dict(d)
        else:
            return Ensemble(member=self._member)

    def __getstate__(self):
        state = {}
        state["member"] = self._member
        return state

    def __setstate__(self, state):
        self.__init__(member=state["member"])


EMPTY_ENSEMBLE = Ensemble()
