# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.core.order import build_remapping
from earthkit.data.utils import ensure_iterable

LOG = logging.getLogger(__name__)


TIME_DIM = 0
DATE_DIM = 1
STEP_DIM = 2
Z_DIM = 1
Y_DIM = 2
X_DIM = 3
N_DIM = 4

DIM_ORDER = [N_DIM, TIME_DIM, DATE_DIM, STEP_DIM, Z_DIM, Y_DIM, X_DIM]


class CompoundKey:
    name = None
    keys = []

    def remapping(self):
        return {self.name: "".join([str(k) for k in self.keys])}

    @staticmethod
    def make(key):
        ck = COMPOUND_KEYS.get(key, None)
        return ck() if ck is not None else None


class ParamLevelKey(CompoundKey):
    name = "param_level"
    keys = ["param", "level"]


class LevelAndTypeKey(CompoundKey):
    name = "level_and_type"
    keys = ["level", "levtype"]


COMPOUND_KEYS = {v.name: v for v in [ParamLevelKey, LevelAndTypeKey]}


class DimId:
    def __init__(self, name):
        self.name = name
        self.id = name + name(self(id))


class Dims:
    def __init__(self, profile, remapping=None):
        self.profile = profile
        self.dims = {}

        # print("INIT index_keys", self.index_keys)

        # each remapping is represented as a dimension
        remapping = build_remapping(remapping)
        if remapping:
            for k in remapping.lists:
                self.dims[k] = RemappingDim(self, k, remapping.lists[k])

        # each compound key defines a dimension. If a remapping uses
        # the same key name, the compound key is not added.
        for k in self.profile.index_keys:
            if not remapping or k not in remapping.lists:
                ck = CompoundKey.make(k)
                if ck is not None:
                    self.dims[k] = CompoundKeyDim(self, ck)

        # predefined dimensions are read from the profile configuration
        for k in self.profile.predefined_dims:
            if k in PREDEFINED_DIMS:
                d = PREDEFINED_DIMS[k](self)
            else:
                d = OtherDim(self, k)
            if k not in self.dims:
                self.dims[k] = d
            else:
                print("Duplicate dim={d.name}")

        # extra dimensions are added to the profile
        for k in self.profile.extra_dims:
            if k not in self.dims:
                self.dims[k] = OtherDim(self, k)

        for v in self.dims.values():
            v.check()

        self.dims = {k: v for k, v in self.dims.items() if v.active}

        # ensure all the requires keys are in the profile
        keys = []
        for d in self.dims.values():
            keys.extend(d.keys)

        self.profile.add_keys(keys)

    def deactivate(self, keys, ignore_dim=None, others=False, collect=False):
        names = []
        for d in self.dims.values():
            if d.active and d != ignore_dim:
                if any(key in d for key in keys):
                    # print(f"deactivate name={self.name} d={d.name} self.group={self.all_dims}")
                    d.active = False
                    if others:
                        d.deactivate_drop_list()
                    if collect:
                        names.append(d.name)

        if collect:
            return names

            # if d.active and self.same(d):
            #     d.active = False

    def update(self, ds, attributes, variable_keys):
        for k, d in self.dims.items():
            d.update(ds, attributes, self.profile.squeeze)

        # squeeze=True applied for all the new dims
        new_dims = {}
        for k in self.profile.index_keys:
            if len(ds.index(k)) > 1:
                if k not in variable_keys and self.allowed(k):
                    new_dims[k] = OtherDim(self, k)

        for k, v in new_dims.items():
            self.dims[k] = v

    def allowed(self, key):
        return all(key not in d for d in self.dims.values())

    @property
    def active_dim_keys(self):
        return [d.name for d in self.dims.values() if d.active]


class Dim:
    role = None
    name = None
    keys = None
    alias = None
    drop = None

    def __init__(self, owner, active=True):
        self.owner = owner
        self.profile = owner.profile
        self.active = active
        self.alias = ensure_iterable(self.alias)
        self.drop = ensure_iterable(self.drop)

        if self.keys is None:
            self.keys = [self.name]
        else:
            self.keys = ensure_iterable(self.keys)

        # self.all_dims = self.drop + [self.name]
        # if self.name not in self.profile.index_keys:
        #     self.profile.add_keys([self.name])

    def _replace_dim(self, key_src, key_dst):
        if key_dst not in self.profile.dim_keys:
            try:
                idx = self.profile.dim_keys.index(key_src)
                self.profile.dim_keys[idx] = key_dst
            except ValueError:
                self.profile.dim_keys.append(key_dst)

    # def convert(self, value):
    #     return value

    # def same(self, other):
    #     return self.name == other.name or any(k in self.alias for k in other.alias)

    def __contains__(self, key):
        return key == self.name or key in self.alias

    # def allows(self, key):
    #     return key not in self.all_dims

    # def remove(self):
    #     self.profile._remove_dim_keys(self.drop)

    def check(self):
        if self.active:
            self.active = self.condition()
            if self.active:
                self.deactivate_drop_list()

    def condition(self):
        return True

    def update(self, ds, attributes, squeeze=True):
        # if self.name in ds.indices():
        #     print(f"-> {self.name} active={self.active} ds={ds.index(self.name)}")

        if not self.active:
            return

        # sanity check
        if self.profile.variable_key in self:
            raise ValueError(
                (
                    f"Variable key {self.profile.var_key} cannot be in "
                    f"dimension={self.name} group={self.group}"
                )
            )

        # assert self.name in self.profile.dim_keys, f"self.name={self.name}"
        if squeeze:
            if not (self.name in ds.indices() and len(ds.index(self.name)) > 1):
                self.active = False
        else:
            if not (self.name in ds.indices() and len(ds.index(self.name)) >= 1):
                self.active = False

        self.deactivate_drop_list()

    def deactivate_drop_list(self):
        self.owner.deactivate([self.name] + self.drop, ignore_dim=self)


class DateDim(Dim):
    name = "date"
    drop = ["valid_datetime", "base_datetime", "forecast_reference_time"]

    def condition(self):
        return not self.profile.add_forecast_ref_time_dim and not self.profile.add_valid_time_dim


class TimeDim(Dim):
    name = "time"
    drop = ["valid_datetime", "base_datetime"]

    def condition(self):
        return not self.profile.add_forecast_ref_time_dim and not self.profile.add_valid_time_dim


class StepDim(Dim):
    name = "step"
    drop = ["valid_datetime", "stepRange"]


class ValidTimeDim(Dim):
    name = "valid_time"
    key = "valid_datetime"
    drop = ["time", "date", "step", "base_datetime", "validityTime", "validityDate"]

    def condition(self):
        return self.profile.add_valid_time_dim


class ForecastRefTimeDim(Dim):
    name = "forecast_reference_time"
    key = "base_datetime"
    drop = ["time", "date", "valid_datetime", "dataTime", "dataDate"]
    alias = ["forecast_reference_time"]

    def condition(self):
        return self.profile.add_forecast_ref_time_dim


class LevelDim(Dim):
    name = "level"
    drop = ["levelist"]
    alias = "levellist"


class LevelListDim(Dim):
    name = "levelist"
    drop = ["level"]
    alias = "level"


class LevelPerTypeDim(Dim):
    name = "[level_per_type]"
    drop = ["levelist", "levtype", "typeOfLevel"]

    # def __init__(self, profile, name):
    #     self.name = name
    #     super().__init__(profile)
    # def __init__(self, profile, *args, **kwargs):
    #     active = profile.level_per_type_dim
    #     super().__init__(profile, *args, active=active, **kwargs)

    def condition(self):
        return self.profile.level_per_type_dim

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


class TypeOfLevelDim(Dim):
    name = "typeOfLevel"
    drop = ["levtype"]

    def update(self, ds, attributes, squeeze=True):
        # print("UPDATE typeOfLevel", ds.index("typeOfLevel"))
        super().update(ds, attributes, squeeze)
        if self.active and not squeeze and len(ds.index(self.name)) < 2:
            self.active = False


class NumberDim(Dim):
    name = "number"
    drop = []


class RemappingDim(Dim):
    def __init__(self, owner, name, keys):
        self.name = name
        self.drop = keys
        super().__init__(owner)


class CompoundKeyDim(Dim):
    def __init__(self, owner, ck):
        self.name = ck.name
        self.ck = ck
        self.drop = ck.keys
        super().__init__(owner)


class OtherDim(Dim):
    drop = []

    def __init__(self, owner, name):
        self.name = name
        super().__init__(owner)


PREDEFINED_DIMS = {}
for d in [
    DateDim,
    TimeDim,
    StepDim,
    ValidTimeDim,
    ForecastRefTimeDim,
    LevelDim,
    LevelListDim,
    LevelPerTypeDim,
    LevelAndTypeDim,
    LevelTypeDim,
    TypeOfLevelDim,
    NumberDim,
]:
    PREDEFINED_DIMS[d.name] = d


# TIME_DIM = 0
# DATE_DIM = 1
# STEP_DIM = 2
# Z_DIM = 1
# Y_DIM = 2
# X_DIM = 3
# N_DIM = 4

# DIM_ORDER = [N_DIM, TIME_DIM, DATE_DIM, STEP_DIM, Z_DIM, Y_DIM, X_DIM]
