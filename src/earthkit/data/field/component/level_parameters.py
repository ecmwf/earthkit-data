# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
from abc import ABCMeta, abstractmethod

from .level_type import LevelTypes, get_level_type


class LevelParameters(metaclass=ABCMeta):
    _LEVEL_TYPE = None

    def level_type(self):
        return self._LEVEL_TYPE

    @abstractmethod
    def number_of_levels(self):
        pass

    @abstractmethod
    def coefficients(self):
        pass

    def coefficient_names(self):
        return self._LEVEL_TYPE.coefficient_names

    @abstractmethod
    def coefficient_size(self):
        pass


class HybridLevelParametersBase(LevelParameters):
    _LEVEL_TYPE = LevelTypes.HYBRID.value


class HybridLevelParameters(HybridLevelParametersBase):
    def __init__(self, A, B):
        self._A = A
        self._B = B
        if len(A) != len(B):
            raise ValueError("A and B coefficient arrays must have the same length")

    def number_of_levels(self):
        return len(self._A) - 1

    def coefficients(self):
        return self._A, self._B

    def coefficient_size(self):
        return 2 * (len(self._A))


def create_level_parameters(level_type, coefficients) -> LevelParameters:
    if coefficients is None:
        raise ValueError("Coefficients must be provided for level types that require them")

    if isinstance(coefficients, LevelParameters):
        if coefficients.level_type() != level_type:
            raise ValueError(
                f"Provided LevelParameters of type {coefficients.level_type()} do not match"
                f" expected level type {level_type}"
            )
        return coefficients

    level_type = get_level_type(level_type)

    if level_type == LevelTypes.HYBRID:
        if len(coefficients) != 2:
            raise ValueError("Hybrid level type requires two coefficient arrays (A and B)")
        A, B = coefficients
        return HybridLevelParameters(A, B)

    raise ValueError(f"Unsupported level type '{level_type}' or invalid coefficients")
