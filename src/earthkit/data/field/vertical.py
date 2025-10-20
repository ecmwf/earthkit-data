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
from .spec.vertical import Vertical


@wrap_spec_methods(keys=["level", "layer", "cf", "abbreviation", "units", "positive", "type"])
class VerticalFieldMember(SpecFieldMember):
    """A specification of a vertical level or layer."""

    SPEC_CLS = Vertical
    NAME = "vertical"

    # def __init__(self, data) -> None:
    #     assert isinstance(data, Vertical)
    #     self._data = data

    # @classmethod
    # def from_dict(cls, d):
    #     """Create a Time object from a dictionary."""
    #     data = Vertical.from_dict(d)
    #     return cls(data)

    def get_grib_context(self, context) -> dict:
        from earthkit.data.field.grib.vertical import COLLECTOR

        COLLECTOR.collect(self, context)

    # def set(self, *args, **kwargs):
    #     data = self._data.set(*args, **kwargs)
    #     return VerticalFieldSpec(data)

    # def namespace(self, owner, name, result):
    #     if name is None or name == "vertical" or (isinstance(name, (list, tuple)) and "vertical" in name):
    #         result["vertical"] = self.to_dict()

    # def check(self, owner):
    #     pass

    # def __getstate__(self):
    #     state = {}
    #     state["data"] = self._data
    #     return state

    # def __setstate__(self, state):
    #     self.__init__(data=state["data"])
