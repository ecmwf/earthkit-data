# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from ..spec.ensemble import Ensemble
from ..spec.spec import SimpleSpec
from .wrap import wrap_methods


@wrap_methods(Ensemble, keys=["member"])
class EnsembleFieldSpec(SimpleSpec):
    """A specification of an ensemble field."""

    def __init__(self, data) -> None:
        assert isinstance(data, Ensemble)
        self._data = data

    @classmethod
    def from_dict(cls, d):
        """Create a Time object from a dictionary."""
        data = Ensemble.from_dict(d)
        return cls(data)

    def get_grib_context(self, context) -> dict:
        from earthkit.data.specs.grib.ensemble import COLLECTOR

        COLLECTOR.collect(self, context)

    def set(self, *args, **kwargs):
        data = self._data.set(*args, **kwargs)
        return EnsembleFieldSpec(data)

    def namespace(self, owner, name, result):
        if name is None or name == "ensemble" or (isinstance(name, (list, tuple)) and "ensemble" in name):
            result["ensemble"] = self.to_dict()

    def check(self, owner):
        pass

    def __getstate__(self):
        state = {}
        state["data"] = self._data
        return state

    def __setstate__(self, state):
        self.__init__(data=state["data"])


# class SimpleEnsembleSpec(EnsembleSpec):
#     """Ensemble specification."""

#     def __init__(self, data) -> None:
#         assert isinstance(data, Ensemble)
#         self._data = data

#     @property
#     def data(self):
#         """Return the level layer."""
#         return self._data

#     @property
#     def member(self) -> str:
#         return self._data.member

#     @classmethod
#     def from_dict(cls, d: dict) -> "SimpleEnsembleSpec":
#         """Create a Ensemble object from a dictionary.

#         Parameters
#         ----------
#         d : dict
#             Dictionary containing parameter data.

#         Returns
#         -------
#         Realisation
#             The created Realisation instance.
#         """
#         if not isinstance(d, dict):
#             raise TypeError("data must be a dictionary")
#         d = normalise_set_kwargs(cls, add_spec_keys=False, **d)
#         data = Ensemble(**d)
#         return cls(data)

#     def to_dict(self) -> dict:
#         """Convert the object to a dictionary.

#         Returns
#         -------
#         dict
#             Dictionary representation of the object.
#         """
#         return {"member": self.member}

#     def get_grib_context(self, context) -> dict:
#         from .grib.ensemble import COLLECTOR

#         COLLECTOR.collect(self, context)

#     def set(self, *args, **kwargs) -> "SimpleEnsembleSpec":
#         """
#         Create a new SimpleEnsemble instance with updated data.

#         Parameters
#         ----------
#         *args
#             Positional arguments.
#         **kwargs
#             Keyword arguments.

#         Returns
#         -------
#         SimpleRealisation
#             The created SimpleRealisation instance.
#         """
#         kwargs = normalise_set_kwargs(self, *args, **kwargs)
#         data = Ensemble(**kwargs)
#         spec = SimpleEnsembleSpec(data)
#         return spec

#     def namespace(self, owner, name, result):
#         if name is None or name == "ensemble" or (isinstance(name, (list, tuple)) and "ensemble" in name):
#             result["ensemble"] = self.to_dict()

#     def check(self, owner):
#         pass

#     def __getstate__(self):
#         state = {}
#         state["data"] = self._data
#         return state

#     def __setstate__(self, state):
#         self.__init__(data=state["data"])
