# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import ABCMeta

# from .spec import Aliases
# from .spec import normalise_create_kwargs_2
# from .spec import spec_aliases


class ProcItem(metaclass=ABCMeta):
    def __init__(self, value, name) -> None:
        self.value = value
        self.name = name


# class TimeSpanProcItem(ProcItem):
#     def __init__(self, value, name) -> None:
#         super().__init__(value, name)


# class TimeSpanMethod:
#     def __init__(
#         self,
#         name: str,
#         standard_name: str,
#         long_name: str,
#     ) -> None:
#         self.name = name
#         self.standard_name = standard_name
#         self.long_name = long_name

#     def __eq__(self, other):
#         return self.name == other.name


# _defs = {
#     "accum": {"name": "accum", "standard_name": "air_pressure", "long_name": "pressure"},
#     "avg": {
#         "name": "avg",
#         "standard_name": "air_pressure",
#         "long_name": "pressure",
#     },
#     "instant": {
#         "name": "instant",
#         "standard_name": "air_pressure",
#         "long_name": "pressure",
#     },
#     "max": {
#         "name": "max",
#         "standard_name": "air_pressure",
#         "long_name": "pressure",
#     },
# }


# LevelTypes = Enum("LevelTypes", [(k, LevelType(**v)) for k, v in _defs.items()])

# _LEVEL_TYPES = {t.value.name: t.value for t in LevelTypes}


# class TimeSpanMethod(Enum):
#     ACCUMULATED = TimeSpanMethodItem(**_defs["accum"])
#     AVERAGE = TimeSpanMethodItem(**_defs["avg"])
#     INSTANT = TimeSpanMethodItem(**_defs["instant"])
#     MAX = TimeSpanMethodItem(**_defs["max"])


# class TimeSpan:
#     def __init__(self, value=datetime.timedelta(), method=TimeSpanMethod.INSTANT):
#         try:
#             self._value = to_timedelta(value)
#         except Exception as e:
#             raise ValueError(f"Invalid time span value: {value}") from e

#         self._method = method
#         if not isinstance(self._method, TimeSpanMethod):
#             raise ValueError(f"Invalid time span method: {method}")
#         self._check()

#     @property
#     def value(self):
#         return self._value

#     @property
#     def method(self):
#         return self._method

#     def __repr__(self):
#         return f"TimeSpan({self._value}, {self._method.value.name})"

#     @staticmethod
#     def build(data):
#         if isinstance(data, TimeSpan):
#             return data
#         else:
#             return TimeSpan(value=data)

#     def _check(self):
#         if self._value != ZERO_TIMEDELTA and self._method == TimeSpanMethod.INSTANT:
#             raise ValueError("A non-zero time_span cannot be of type instant")

#         if self._value == ZERO_TIMEDELTA and self._method != TimeSpanMethod.INSTANT:
#             raise ValueError("A zero time_span must be of type instant")

#     def __eq__(self, data):
#         value = TimeSpan.build(data)
#         return self._value == value._value and self._method == value._method

#     def __hash__(self):
#         return hash((self._value, self._method))


# @spec_aliases
# class PostProcess:
#     """A specification of a parameter."""

#     _SET_KEYS = (
#         "variable",
#         "units",
#     )

#     _ALIASES = Aliases({"variable": ("param",)})

#     def __init__(self, variable: str = None, units: str = None) -> None:
#         self._variable = variable
#         self._units = units

#     @property
#     def variable(self) -> str:
#         r"""str: Return the parameter variable."""
#         return self._variable

#     @property
#     def units(self) -> str:
#         r"""str: Return the parameter units."""
#         return self._units

#     @classmethod
#     def from_dict(cls, d: dict, allow_unused=False) -> "Parameter":
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

#         d1 = normalise_create_kwargs_2(cls, d, allowed_keys=cls._SET_KEYS, allow_unused=allow_unused)
#         # print(" ->", d)
#         return cls(**d1)
