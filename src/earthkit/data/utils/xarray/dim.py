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


class Vocabulary:
    @staticmethod
    def make(name):
        return VOCABULARIES[name]()


class MarsVocabulary(Vocabulary):
    def level(self):
        return "levelist"

    def level_type(self):
        return "levtype"


class CFVocabulary(Vocabulary):
    def level(self):
        return "level"

    def level_type(self):
        return "typeOfLevel"


VOCABULARIES = {"mars": MarsVocabulary, "cf": CFVocabulary}


class DimGroup:
    name = None
    names = None

    def __init__(self, dims, used):
        self.used = {d: dims[d] for d in used}
        self.ignored = {k: v for k, v in dims.items() if k not in self.used}
        assert all(n in self.used or n in self.ignored for n in self.names)

    def dims(self):
        return self.used, self.ignored

    def make_dim(self, name, *args, **kwargs):
        if name in PREDEFINED_DIMS:
            return PREDEFINED_DIMS[name](*args, **kwargs)
        return OtherDim(*args, **kwargs)


class NumberDimGroup(DimGroup):
    name = "number"
    names = ["number"]

    def __init__(self, profile, owner):
        dims = {name: self.make_dim(name, owner) for name in self.names}
        used = ["number"]
        super().__init__(dims, used)

    def collect(self, tensor):
        pass


class TimeDimGroup(DimGroup):
    name = "time"
    names = ["forecast_reference_time", "date", "time", "step", "valid_time"]

    def __init__(self, profile, owner):
        dims = {name: self.make_dim(name, owner) for name in self.names}

        used = []
        if profile.time_dim_mode == "forecast":
            used = ["forecast_reference_time", "step"]
        elif profile.time_dim_mode == "valid":
            used = ["valid_time"]
        else:
            used = ["date", "time", "step"]

        super().__init__(dims, used)


class LevelDimGroup(DimGroup):
    name = "level"
    names = ["level", "level_per_type", "level_and_type"]

    def __init__(self, profile, owner):
        level_key = profile.vocabulary.level()
        level_type_key = profile.vocabulary.level_type()

        dims = {
            "level": LevelDim(owner, level_key),
            "level_per_type": LevelPerTypeDim(owner, level_key, level_type_key),
            "level_and_type": LevelAndTypeDim(owner, level_key, level_type_key),
        }

        print(f"level_dim_mode={profile.level_dim_mode}")
        used = []
        if profile.level_dim_mode == "level":
            used = ["level"]
        elif profile.level_dim_mode == "per_type":
            used = ["level_per_type"]
        elif profile.level_dim_mode == "and_type":
            used = ["level_and_type"]

        super().__init__(dims, used)


DIM_GROUPS = {v.name: v for v in [NumberDimGroup, TimeDimGroup, LevelDimGroup]}


class DimId:
    def __init__(self, name):
        self.name = name
        self.id = name + name(self(id))


class Dims:
    def __init__(self, profile, dims=None, remapping=None):
        self.profile = profile

        if dims is not None:
            self.dims = dims
            return

        self.dims = {}
        ignored = {}

        # print("INIT index_keys", self.profile.index_keys)

        # each remapping is a dimension
        remapping = build_remapping(remapping)
        if remapping:
            for k in remapping.lists:
                self.dims[k] = RemappingDim(self, k, remapping.lists[k])

        self.core_dim_order = []
        groups = {}
        for k, v in DIM_GROUPS.items():
            gr = v(self.profile, self)
            groups[k] = gr
            used, ignored = gr.dims()
            for k, v in used.items():
                print(f"ADD DIM {k} {v}")
                if k not in self.dims:
                    self.dims[k] = v
                    self.core_dim_order.append(k)
                else:
                    ignored[k] = v
            ignored.update(ignored)

        keys = self.profile.index_keys + self.profile.extra_dims

        # each index key can define a dimension
        # compound keys: If a remapping uses the same key name, the compound
        # key is not added.s
        for k in keys:
            if k not in self.dims and k not in ignored:
                if not remapping or k not in remapping.lists:
                    ck = CompoundKey.make(k)
                    if ck is not None:
                        self.dims[k] = CompoundKeyDim(self, ck)
                    else:
                        self.dims[k] = OtherDim(self, name=k)

        # check dims consistency. The ones can be used
        # marked as active
        for k, d in self.dims.items():
            d.check()

        # only the active dims are used
        self.dims = {k: v for k, v in self.dims.items() if v.active}

        # # ignored dims are used for later checks?
        # self.ignore = ignored
        # self.ignore.update({k: v for k, v in self.dims.items() if not v.active})

        print(f"INIT dims={self.dims.keys()}")

        # ensure all the required keys are in the profile
        keys = []
        for d in self.dims.values():
            keys.append(d.key)

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

    def remove(self, keys, ignore_dim=None, others=False, collect=False):
        self.deactivate(keys, ignore_dim, others, collect)
        self.dims = {k: v for k, v in self.dims.items() if v.active}

    def update(self, ds, attributes, variable_keys):
        for k, d in self.dims.items():
            d.update(ds, attributes, self.profile.squeeze)

        self.dims = {k: v for k, v in self.dims.items() if v.active}

    def allowed(self, key):
        return all(d.allowed(key) for d in self.dims.values())

    @property
    def active_dim_keys(self):
        return [d.key for d in self.dims.values() if d.active]

    def make_coords(self):
        r = {d.coord.name: d.coord.make_var(self.profile) for d in self.dims.values() if d.coord is not None}
        return r

    def as_coord(self, tensor):
        r = {}

        def _get(k):
            for d in self.dims.values():
                if k == d.key:
                    return d

        for k, v in tensor.user_coords.items():
            for d in self.dims.values():
                d = _get(k)
                name, coord = d.as_coord(k, v, tensor)
                r[name] = coord
        return r

    def to_list(self, copy=True):
        if copy:
            return [d.copy() for d in self.dims.values()]
        return list(self.dims.values())


class Dim:
    name = None
    key = None
    alias = None
    drop = None
    # predefined_index = -1

    def __init__(self, owner, name=None, key=None):
        self.owner = owner
        self.profile = owner.profile
        self.active = True
        self.alias = ensure_iterable(self.alias)
        self.drop = ensure_iterable(self.drop)
        if name is not None:
            self.name = name

        if self.key is None:
            self.key = self.name

        self.coords = {}

    def copy(self):
        return self.__class__(self.owner)

    def _replace_dim(self, key_src, key_dst):
        if key_dst not in self.profile.dim_keys:
            try:
                idx = self.profile.dim_keys.index(key_src)
                self.profile.dim_keys[idx] = key_dst
            except ValueError:
                self.profile.dim_keys.append(key_dst)

    def __contains__(self, key):
        return key == self.name or key in self.alias

    def allowed(self, key):
        return key not in self and key not in self.drop

    def check(self):
        if self.active:
            self.active = self.condition()
            if self.active:
                self.deactivate_drop_list()

    def condition(self):
        return True

    def update(self, ds, attributes, squeeze=True):
        # if self.key in ds.indices():
        #     print(f"-> {self.name} key={self.key} active={self.active} ds={ds.index(self.key)}")

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
            if not (self.key in ds.indices() and len(ds.index(self.key)) > 1):
                self.active = False
        else:
            if not (self.key in ds.indices() and len(ds.index(self.key)) >= 1):
                self.active = False

        self.deactivate_drop_list()

    def deactivate_drop_list(self):
        self.owner.deactivate([self.name, self.key] + self.drop, ignore_dim=self)

    def as_coord(self, key, values, tensor):
        if key not in self.coords:
            from .coord import Coord

            self.coords[key] = Coord.make(key, values, ds=tensor.source)
        return key, self.coords[key]

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, key={self.key})"


class DateDim(Dim):
    name = "date"
    drop = ["valid_datetime", "base_datetime", "forecast_reference_time"]


class TimeDim(Dim):
    name = "time"
    drop = ["valid_datetime", "base_datetime"]


class StepDim(Dim):
    name = "step"
    drop = ["valid_datetime", "stepRange"]


class ValidTimeDim(Dim):
    name = "valid_time"
    drop = ["time", "date", "step", "base_datetime", "validityTime", "validityDate"]
    rank = 1


class ForecastRefTimeDim(Dim):
    name = "forecast_reference_time"
    drop = ["time", "date", "valid_datetime", "dataTime", "dataDate"]
    alias = ["base_datetime"]


class LevelDim(Dim):
    drop = ["levelist", "level"]
    alias = "levelist"

    def __init__(self, owner, key, *args, **kwargs):
        self.key = key
        self.name = key
        super().__init__(owner, *args, **kwargs)

    def copy(self):
        return self.__class__(self.owner, self.key)


class LevelPerTypeDim(Dim):
    name = "level_per_type"
    drop = ["levelist", "levtype", "typeOfLevel"]

    def __init__(self, owner, level_key, level_type_key, *args, **kwargs):
        self.key = level_key
        self.level_key = level_key
        self.level_type_key = level_type_key
        super().__init__(owner, *args, **kwargs)

    def copy(self):
        return self.__class__(self.owner, self.level_key, self.level_type_key)

    def as_coord(self, key, values, tensor):
        lev_type = tensor.source[0].metadata(self.level_type_key)
        if not lev_type:
            raise ValueError(f"{d.type_key} not found in metadata")

        if lev_type not in self.coords:
            from .coord import Coord

            coord = Coord.make(lev_type, list(values), ds=tensor.source)
            self.coords[lev_type] = coord
        return lev_type, self.coords[lev_type]


class LevelAndTypeDim(Dim):
    name = "level_and_type"
    drop = ["level", "levelist", "typeOfLevel", "levtype"]

    def adjust_dims(self):
        self._insert_at("level", self.name)
        super().adjust_dims()

    def condition(self):
        return False


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

    def __init__(self, owner, name, *args, **kwargs):
        self.name = name
        super().__init__(owner, *args, **kwargs)

    def copy(self):
        return self.__class__(self.owner, self.name)


PREDEFINED_DIMS = {}
for i, d in enumerate(
    [
        NumberDim,
        ForecastRefTimeDim,
        DateDim,
        TimeDim,
        StepDim,
        ValidTimeDim,
        LevelDim,
        LevelPerTypeDim,
        LevelAndTypeDim,
    ]
):
    PREDEFINED_DIMS[d.name] = d
    d.predefined_index = i
