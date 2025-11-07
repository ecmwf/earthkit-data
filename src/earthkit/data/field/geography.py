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
from .spec.geography import Geography

# from abc import abstractmethod

# from .spec import SimpleSpec
# from .spec import normalise_set_kwargs
# from .spec import spec_aliases

# from .spec.geography import Geography
# from .core import wrap_methods


# class FieldSpecAdapter(SimpleSpec):
#     CLS = None
#     NAME = None

#     """A specification of a vertical level or layer."""

#     def __init__(self, data) -> None:
#         assert isinstance(data, self.CLS)
#         self._data = data

#     @classmethod
#     def from_dict(cls, d):
#         """Create a Time object from a dictionary."""
#         data = cls.CLS.from_dict(d)
#         return cls(data)

#     # def get_grib_context(self, context) -> dict:
#     #     from earthkit.data.specs.grib.parameter import COLLECTOR

#     #     COLLECTOR.collect(self, context)

#     def set(self, *args, **kwargs):
#         data = self._data.set(*args, **kwargs)
#         return type(self)(data)

#     def namespace(self, owner, name, result):
#         if name is None or name == self.NAME or (isinstance(name, (list, tuple)) and self.NAME in name):
#             result[self.NAME] = self.to_dict()

#     def check(self, owner):
#         pass

#     def __getstate__(self):
#         state = {}
#         state["data"] = self._data
#         return state

#     def __setstate__(self, state):
#         self.__init__(data=state["data"])


@wrap_spec_methods(
    keys=[
        "latitudes",
        "longitudes",
        "shape",
        "grid_spec",
        "grid_type",
        "bounding_box",
        "distinct_latitudes",
        "distinct_longitudes",
        "x",
        "y",
        "projection",
        "unique_grid_id",
    ]
)
class GeographyFieldMember(SpecFieldMember):

    SPEC_CLS = Geography
    NAME = "geography"

    def get_grib_context(self, context) -> dict:
        pass

    def set(self, *args, **kwargs):
        raise NotImplementedError("GeographyFieldMember.set is not implemented yet.")
