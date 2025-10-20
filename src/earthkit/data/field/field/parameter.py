# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from ..spec.parameter import Parameter
from ..spec.spec import SimpleSpec
from .wrap import wrap_methods


@wrap_methods(Parameter, keys=["variable", "units"])
class ParameterFieldSpec(SimpleSpec):
    """A specification of a vertical level or layer."""

    def __init__(self, data) -> None:
        assert isinstance(data, Parameter)
        self._data = data

    @classmethod
    def from_dict(cls, d):
        """Create a Time object from a dictionary."""
        data = Parameter.from_dict(d)
        return cls(data)

    def get_grib_context(self, context) -> dict:
        from earthkit.data.specs.grib.parameter import COLLECTOR

        COLLECTOR.collect(self, context)

    def set(self, *args, **kwargs):
        data = self._data.set(*args, **kwargs)
        return ParameterFieldSpec(data)

    def namespace(self, owner, name, result):
        if name is None or name == "parameter" or (isinstance(name, (list, tuple)) and "parameter" in name):
            result["parameter"] = self.to_dict()

    def check(self, owner):
        pass

    def __getstate__(self):
        state = {}
        state["data"] = self._data
        return state

    def __setstate__(self, state):
        self.__init__(data=state["data"])
