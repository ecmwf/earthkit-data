from abc import abstractmethod

from .component import SimpleFieldComponent, component_keys, mark_get_key


@component_keys
class ProvenanceBase(SimpleFieldComponent):
    """Base class for the provenance component of a field."""

    @mark_get_key
    @abstractmethod
    def history(self) -> str:
        """TODO."""


def create_provenance(d: dict) -> "ProvenanceBase":
    """TODO."""
    cls = Provenance
    d1 = cls._normalise_create_kwargs(d, allowed_keys=("history",))
    return cls(**d1)


class Provenance(ProvenanceBase):
    """Provenance component representing provenance information."""

    def __init__(self, history=None):
        self._history = history

    @classmethod
    def from_dict(cls, d: dict) -> "Provenance":
        """Create a Provenance object from a dictionary."""
        return create_provenance(d)

    def to_dict(self):
        """Return a dictionary representation of the Provenance."""
        return {"history": self._history}

    def set(self, *args, **kwargs):
        d = self._normalise_set_kwargs(*args, allowed_keys=("history",), **kwargs)

        if d:
            return self.from_dict(d)
        else:
            return Provenance(history=self._history)

    def history(self):
        return self._history

    def __getstate__(self):
        return {"history": self._history}

    def __setstate__(self, state):
        self.__init__(history=state["history"])


class EmptyProvenance(Provenance):
    """TODO?."""
