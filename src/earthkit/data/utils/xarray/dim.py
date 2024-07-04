# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

LOG = logging.getLogger(__name__)


class Dim:
    name = None
    alias = None
    drop = None
    active = True

    def __init__(self, profile):
        self.profile = profile
        if self.alias is None:  # pragma: no cover
            self.alias = []
        if self.drop is None:  # pragma: no cover
            self.drop = []

        self.all_dims = self.drop + [self.name]
        if self.name not in self.profile.index_keys:
            self.profile.add_keys([self.name])

    def _replace_dim(self, key_src, key_dst):
        if key_dst not in self.profile.dim_keys:
            try:
                idx = self.profile.dim_keys.index(key_src)
                self.profile.dim_keys[idx] = key_dst
            except ValueError:
                self.profile.dim_keys.append(key_dst)

    def convert(self, value):
        return value

    def same(self, other):
        return self.name == other.name or any(k in self.alias for k in other.alias)

    def __contains__(self, key):
        return key == self.name or key in self.alias

    def allows(self, key):
        return key not in self.all_dims

    def remove(self):
        self.profile._remove_dim_keys(self.drop)

    def update(self, ds, attributes, squeeze=True):
        # if self.name in ds.indices():
        #     print(f"-> {self.name} active={self.active} ds={ds.index(self.name)}")

        if not self.active:
            return

        if self.profile.var_key in self:
            raise ValueError(
                (
                    f"Variable key {self.profile.var_key} cannot be in "
                    f"dimension={self.name} group={self.group}"
                )
            )

        # assert self.name in self.profile.dim_keys, f"self.name={self.name}"
        if squeeze:
            if self.name in ds.indices() and len(ds.index(self.name)) > 1:
                # print(f"-> {self.name} found in ds")
                self.deactivate_related()
            else:
                self.active = False
                self.deactivate_related()
        else:
            if self.name in ds.indices() and len(ds.index(self.name)) >= 1:
                # print(f"-> {self.name} found in ds")
                self.deactivate_related()
            else:
                self.active = False
                self.deactivate_related()

    def deactivate_related(self):
        for d in self.profile.dims:
            if d.active and d != self:
                if any(g in d for g in self.all_dims):
                    # print(f"deactivate name={self.name} d={d.name} self.group={self.all_dims}")
                    d.active = False
                if d.active and self.same(d):
                    d.active = False


class DateDim(Dim):
    name = "date"
    drop = ["valid_datetime", "base_datetime"]


class TimeDim(Dim):
    name = "time"
    drop = ["valid_datetime", "base_datetime"]


class StepDim(Dim):
    name = "step"
    drop = ["valid_datetime"]


class ValidDatetimeDim(Dim):
    name = "valid_datetime"
    drop = ["time", "date", "step", "base_datetime"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._replace_dim("date", self)

    # def adjust_dims(self):
    #     self._insert_at("date")
    #     super().adjust_dims()


class BaseDatetimeDim(Dim):
    name = "base_datetime"
    drop = ["time", "date", "valid_datetime"]
    alias = ["forecast_reference_time"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._replace_dim("date", self.name)

        # def adjust_dims(self):
        # self._insert_at("date")
        # super().adjust_dims()


class LevelDim(Dim):
    name = "levelist"
    drop = ["level"]
    alias = "level"


class LevelPerTypeDim(Dim):
    name = "level"
    drop = ["levelist", "levtype", "typeOfLevel"]

    # def __init__(self, profile, name):
    #     self.name = name
    #     super().__init__(profile)

    def rename(self, name):
        self.name = name


class LevelAndTypeDim(Dim):
    name = "level_and_type"
    drop = ["level", "levelist", "typeOfLevel", "levtype"]

    def adjust_dims(self):
        self._insert_at("level", self.name)
        super().adjust_dims()


class LevelTypeDim(Dim):
    name = "levtype"
    drop = ["typeOfLevel"]

    def update(self, ds, attributes, squeeze=True):
        # print("UPDATE levtype", ds.index("levtype"))
        super().update(ds, attributes, squeeze)
        if self.active and not squeeze and len(ds.index(self.name)) < 2:
            self.active = False


class NumberDim(Dim):
    name = "number"
    drop = []


class RemappingDim(Dim):
    def __init__(self, profile, name, keys):
        self.name = name
        self.drop = keys
        super().__init__(profile)


class CompoundKeyDim(Dim):
    def __init__(self, profile, ck):
        self.name = ck.name
        self.ck = ck
        self.drop = ck.keys
        super().__init__(profile)


class OtherDim(Dim):
    drop = []

    def __init__(self, profile, name):
        self.name = name
        super().__init__(profile)


TIME_DIM = 0
DATE_DIM = 1
STEP_DIM = 2
Z_DIM = 1
Y_DIM = 2
X_DIM = 3
N_DIM = 4

DIM_ORDER = [N_DIM, TIME_DIM, DATE_DIM, STEP_DIM, Z_DIM, Y_DIM, X_DIM]
