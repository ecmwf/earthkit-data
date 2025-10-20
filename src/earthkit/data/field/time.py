# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .core import SpecFieldMember
from .core import wrap_spec_methods
from .spec.time import Time


@wrap_spec_methods(keys=["base_datetime", "valid_datetime", "step"])
class TimeFieldMember(SpecFieldMember):
    """A specification for a time object."""

    SPEC_CLS = Time
    NAME = "time"

    # def __init__(self, data) -> None:
    #     assert isinstance(data, Time)
    #     self._data = data

    # @classmethod
    # def from_dict(cls, d):
    #     """Create a Time object from a dictionary."""
    #     data = Time.from_dict(d)
    #     return cls(data)

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.time import COLLECTOR

        COLLECTOR.collect(self, context)

    # def set(self, *args, **kwargs):
    #     data = self._data.set(*args, **kwargs)
    #     return TimeFieldSpec(data)

    # def namespace(self, owner, name, result):
    #     if name is None or name == "time" or (isinstance(name, (list, tuple)) and "time" in name):
    #         result["time"] = self.to_dict()

    # def check(self, owner):
    #     pass

    # def __getstate__(self):
    #     state = {}
    #     state["data"] = self._data
    #     return state

    # def __setstate__(self, state):
    #     self.__init__(data=state["data"])
