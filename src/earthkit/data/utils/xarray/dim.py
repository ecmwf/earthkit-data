# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

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
    keys = ["param", "level", "levelist"]


# class LevelAndTypeKey(CompoundKey):
#     name = "level_and_type"
#     keys = ["level", "levtype"]


COMPOUND_KEYS = {v.name: v for v in [ParamLevelKey]}
LEVEL_KEYS = ["level", "levelist", "topLevel", "bottomLevel", "levels", "typeOfLevel", "levtype"]
DATE_KEYS = ["date", "andate", "validityDate", "dataDate", "hdate", "referenceDate", "indexingDate"]
TIME_KEYS = ["time", "antime", "validityTime", "dataTime", "referenceTime", "indexingTime"]
STEP_KEYS = ["step", "endStep", "stepRange"]
VALID_DATETIME_KEYS = ["valid_time", "valid_datetime"]
BASE_DATETIME_KEYS = [
    "forecast_reference_time",
    "base_time",
    "base_datetime",
    "reference_time",
    "reference_datetime",
    "indexing_time",
    "indexing_datetime",
]
DATETIME_KEYS = BASE_DATETIME_KEYS + VALID_DATETIME_KEYS


def get_keys(keys, drop=None):
    r = list(keys)
    if drop:
        drop = ensure_iterable(drop)
        r = [k for k in r if k not in drop]
    return r


def find_related_keys(key, drop=None):
    keys = [LEVEL_KEYS, DATE_KEYS]
    r = []
    for k in keys:
        if key in k:
            r.extend(k)

    if drop:
        drop = ensure_iterable(drop)
        r = [k for k in r if k not in drop]
    return r


def find_alias(key, drop=None):
    keys = [LEVEL_KEYS, DATE_KEYS]
    r = []
    for k in keys:
        if key in k:
            r.extend(k)

    if drop:
        drop = ensure_iterable(drop)
        r = [k for k in r if k not in drop]
    return r


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


class Dim:
    name = None
    key = None
    keys = []
    alias = None
    drop = None
    # predefined_index = -1

    def __init__(self, owner, name=None, key=None, active=True):
        self.owner = owner
        self.profile = owner.profile
        self.active = active
        self.alias = ensure_iterable(self.alias)
        self.drop = ensure_iterable(self.drop)
        if name is not None:
            self.name = name

        if self.key is None:
            self.key = self.name

        self.coords = {}

    def copy(self):
        return self.__class__(self.owner)

    # def _replace_dim(self, key_src, key_dst):
    #     if key_dst not in self.profile.dim_keys:
    #         try:
    #             idx = self.profile.dim_keys.index(key_src)
    #             self.profile.dim_keys[idx] = key_dst
    #         except ValueError:
    #             self.profile.dim_keys.append(key_dst)

    def __contains__(self, key):
        return key in [self.name, self.key] or key in self.keys or key in self.alias

    def allowed(self, key):
        return key not in self and key not in self.drop

    def check(self):
        # print(f"CHECK {self.name} {self.key} {self.active}")
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
        if self.key not in self.profile.ensure_dims:
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
    drop = get_keys(DATE_KEYS + DATETIME_KEYS, drop=name)


class TimeDim(Dim):
    name = "time"
    drop = get_keys(TIME_KEYS + DATETIME_KEYS, drop=name)


class StepDim(Dim):
    name = "step"
    drop = get_keys(STEP_KEYS + VALID_DATETIME_KEYS, drop=name)


class ValidTimeDim(Dim):
    name = "valid_time"
    drop = get_keys(DATE_KEYS + TIME_KEYS + DATETIME_KEYS, drop=name)


class ForecastRefTimeDim(Dim):
    name = "forecast_reference_time"
    drop = get_keys(DATE_KEYS + TIME_KEYS + DATETIME_KEYS, drop=name)
    alias = ["base_datetime"]


class IndexingTimeDim(Dim):
    name = "indexing_time"
    drop = get_keys(DATE_KEYS + TIME_KEYS + DATETIME_KEYS, drop=name)


class ReferenceTimeDim(Dim):
    name = "reference_time"
    drop = get_keys(DATE_KEYS + TIME_KEYS + DATETIME_KEYS, drop=name)


class CustomForecastRefDim(Dim):
    @staticmethod
    def _datetime(val):
        if not val:
            return None
        else:
            from earthkit.data.utils.dates import datetime_from_grib

            try:
                date, time = val.split("_")
                return datetime_from_grib(int(date), int(time)).isoformat()
            except Exception:
                return val

    def __init__(self, owner, keys, *args, active=True, **kwargs):
        if isinstance(keys, str):
            self.key = keys
        elif isinstance(keys, list) and len(keys) == 2:
            date = keys[0]
            time = keys[1]
            self.key = f"{date}_{time}"
            self.drop = [date, time]
            if active:
                owner.register_remapping(
                    {self.key: "{" + date + "}_{" + time + "}"},
                    patch={self.key: CustomForecastRefDim._datetime},
                )
        else:
            raise ValueError(f"Invalid keys={keys}")
        super().__init__(owner, *args, active=active, **kwargs)

    def copy(self):
        return self.__class__(self.owner, self.key)


class LevelDim(Dim):
    alias = "levelist"

    def __init__(self, owner, key, *args, **kwargs):
        self.key = key
        self.name = key
        self.drop = get_keys(LEVEL_KEYS, drop=self.name)
        super().__init__(owner, *args, **kwargs)

    def copy(self):
        return self.__class__(self.owner, self.key)


class LevelPerTypeDim(Dim):
    name = "level_per_type"
    drop = get_keys(LEVEL_KEYS, drop=name)

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
    drop = get_keys(LEVEL_KEYS, drop=name)

    def __init__(self, owner, level_key, level_type_key, active=True, *args, **kwargs):
        self.level_key = level_key
        self.level_type_key = level_type_key
        if active:
            owner.register_remapping(
                {self.name: "{" + self.level_key + "}{" + self.level_type_key + "}"},
            )
        super().__init__(owner, *args, active=active, **kwargs)

    def copy(self):
        return self.__class__(self.owner, self.level_key, self.level_type_key, active=self.active)


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
        self.keys = [k for k in keys if k]
        self.drop = self.build_drop(keys)
        super().__init__(owner)

    def build_drop(self, keys):
        r = list(keys)
        for k in keys:
            r.extend(find_alias(k))
        return r

    def copy(self):
        return self.__class__(self.owner, self.name, self.keys)


class CompoundKeyDim(RemappingDim):
    def __init__(self, owner, ck):
        # self.name = ck.name
        self.ck = ck
        # self.drop = ck.keys
        super().__init__(owner, ck.name, ck.keys)

    def copy(self):
        return self.__class__(self.owner, self.ck)


class OtherDim(Dim):
    drop = []

    def __init__(self, owner, name, *args, **kwargs):
        self.name = name
        super().__init__(owner, *args, **kwargs)

    def copy(self):
        return self.__class__(self.owner, self.name)


class DimMode:
    def make_dim(self, owner, name, *args, **kwargs):
        if name in PREDEFINED_DIMS:
            return PREDEFINED_DIMS[name](owner, *args, **kwargs)
        return OtherDim(owner, name, *args, **kwargs)

    def build(self, profile, owner, active=True):
        return {name: self.make_dim(owner, name, active=active) for name in self.default}


class ForecastTimeDimMode(DimMode):
    name = "forecast"
    default = ["forecast_reference_time", "step"]
    mappings = {"seasonal": {"datetime": "indexing_time", "step": "forecastMonth"}}

    def build(self, profile, owner, active=True):
        mapping = profile.time_dim_mapping
        if mapping:
            if isinstance(mapping, str):
                mapping = self.mappings.get(mapping, None)
                if mapping is None:
                    raise ValueError(f"Unknown mapping={mapping}")

            if isinstance(mapping, dict):
                step = mapping.get("step", None)
                if step is None:
                    raise ValueError(f"step is required in mapping={mapping}")

                datetime = mapping.get("datetime", None)
                if datetime:
                    return {name: self.make_dim(owner, name, active=active) for name in [datetime, step]}
                else:
                    datetime = [mapping["date"], mapping["time"]]
                    dim1 = CustomForecastRefDim(owner, datetime, active=active)
                    dim2 = self.make_dim(owner, step, active=active)
                    return {d.name: d for d in [dim1, dim2]}
            else:
                raise ValueError(f"Unsupported mapping type={type(mapping)}")

        else:
            return {name: self.make_dim(owner, name, active=active) for name in self.default}


class ValidTimeDimMode(DimMode):
    name = "valid_time"
    default = ["valid_time"]


class RawTimeDimMode(DimMode):
    name = "raw"
    default = ["date", "time", "step"]


class LevelDimMode(DimMode):
    name = "level"
    default = ["level"]
    dim = LevelDim
    alias = LEVEL_KEYS

    def build(self, profile, owner, **kwargs):
        level_key = profile.vocabulary.level()
        level_type_key = profile.vocabulary.level_type()
        return {self.name: self.dim(owner, level_key, level_type_key, **kwargs)}


class LevelPerTypeDimMode(LevelDimMode):
    name = "level_per_type"
    default = ["level_per_type"]
    dim = LevelPerTypeDim


class LevelAndTypeDimMode(LevelDimMode):
    name = "level_and_type"
    default = ["level_and_type"]
    dim = LevelAndTypeDim


TIME_DIM_MODES = {v.name: v for v in [ForecastTimeDimMode, ValidTimeDimMode, RawTimeDimMode]}
LEVEL_DIM_MODES = {v.name: v for v in [LevelDimMode, LevelPerTypeDimMode, LevelAndTypeDimMode]}


class DimGroup:
    used = {}
    ignored = {}

    def dims(self):
        return self.used, self.ignored


class NumberDimGroup(DimGroup):
    name = "number"

    def __init__(self, profile, owner):
        self.used = {self.name: NumberDim(owner)}


class TimeDimGroup(DimGroup):
    name = "time"

    def __init__(self, profile, owner):
        mode = TIME_DIM_MODES.get(profile.time_dim_mode, None)
        if mode is None:
            raise ValueError(f"Unknown time_dim_mode={profile.time_dim_mode}")

        mode = mode()
        self.used = mode.build(profile, owner)
        self.ignored = {
            k: v().build(profile, owner, active=False) for k, v in TIME_DIM_MODES.items() if v != mode
        }


class LevelDimGroup(DimGroup):
    name = "level"

    def __init__(self, profile, owner):
        mode = LEVEL_DIM_MODES.get(profile.level_dim_mode, None)
        if mode is None:
            raise ValueError(f"Unknown level_dim_mode={profile.level_dim_mode}")

        mode = mode()
        self.used = mode.build(profile, owner)
        self.ignored = {
            k: v().build(profile, owner, active=False) for k, v in LEVEL_DIM_MODES.items() if v != mode
        }


DIM_GROUPS = {v.name: v for v in [NumberDimGroup, TimeDimGroup, LevelDimGroup]}


class Dims:
    def __init__(self, profile, dims=None):
        self.profile = profile

        if dims is not None:
            self.dims = dims
            return

        self.dims = {}
        ignored = {}

        # print("INIT index_keys", self.profile.index_keys)

        # initial check for variable-related keys
        from .profile import VARIABLE_KEYS

        var_keys = [self.profile.variable_key] + VARIABLE_KEYS
        keys = list(self.profile.index_keys)
        # if self.profile.variable_key in keys:
        #     keys.remove(self.profile.variable_key)
        keys += self.profile.extra_dims + self.profile.ensure_dims + self.profile.fixed_dims
        if self.profile.variable_key in keys:
            keys.remove(self.profile.variable_key)

        invalid_var_keys = []
        for k in keys:
            if k in var_keys:
                assert k != self.profile.variable_key
                invalid_var_keys.append(k)
                # print("index_keys=", self.profile.index_keys)
                # print("extra_dims=", self.profile.extra_dims)
                # print("fixed_dims=", self.profile.fixed_dims)

        if invalid_var_keys:
            raise ValueError(self.var_dim_found_error_message(invalid_var_keys))

        # each remapping is a dimension. They can contain variable related keys.
        remapping = self.profile.remapping.build()
        if remapping:
            for k in remapping.lists:
                self.dims[k] = RemappingDim(self, k, remapping.keys(k))

        # search for compound keys. Note: the variable key can be a compound key
        # so has to be added here. If a remapping uses the same key name, the compound
        # key is not added.
        for k in [self.profile.variable_key] + keys:
            if not remapping or k not in remapping.lists:
                ck = CompoundKey.make(k)
                if ck is not None:
                    self.dims[k] = CompoundKeyDim(self, ck)

        # add predefined dimensions
        self.core_dim_order = []
        groups = {}
        for k, v in DIM_GROUPS.items():
            gr = v(self.profile, self)
            groups[k] = gr
            used, ignored = gr.dims()
            for k, v in used.items():
                # print(f"ADD DIM {k} {v}")
                if k not in self.dims:
                    self.dims[k] = v
                    self.core_dim_order.append(k)
                else:
                    ignored[k] = v
            ignored.update(ignored)

        # each key can define a dimension
        for k in keys:
            if k not in self.dims and k not in ignored:
                if not remapping or k not in remapping.lists:
                    self.dims[k] = OtherDim(self, name=k)

        # print(f"INIT dims={self.dims}")
        # check dims consistency. The ones can be used
        # marked as active
        for k, d in self.dims.items():
            d.check()
        # print(f" -> dims={self.dims}")
        # check for any dimensions related to variable keys. These have to
        # be removed from the list of active dims.
        var_dims = self.deactivate(var_keys, others=True, collect=True)
        if var_dims:
            if self.profile.variable_key in var_dims:
                var_dims.remove(self.profile.variable_key)
            if var_dims:
                raise ValueError(self.var_dim_found_error_message(var_dims))

        # only the active dims are used
        dims = {k: v for k, v in self.dims.items() if v.active and k not in self.core_dim_order}
        for k in self.core_dim_order:
            if self.dims[k].active:
                dims[k] = self.dims[k]

        self.dims = dims

        # # ignored dims are used for later checks?
        # self.ignore = ignored
        # self.ignore.update({k: v for k, v in self.dims.items() if not v.active})

        # print(f"INIT dims={self.dims.keys()}")

        # ensure all the required keys are in the profile
        keys = []
        for d in self.dims.values():
            keys.append(d.key)

        self.profile.add_keys(keys)

    def var_dim_found_error_message(self, keys):
        return (
            f"Variable-related keys {keys} cannot be dimensions. They must"
            " be specified as the variable_key, which can only be set to single key. "
            f'Current settings: variable_key="{self.profile.variable_key}"'
        )

    def register_remapping(self, remapping, patch=None):
        self.profile.remapping.add(remapping, patch)

    def deactivate(self, keys, ignore_dim=None, others=False, collect=False):
        names = []
        for d in self.dims.values():
            if d.active and d != ignore_dim:
                if any(key in d for key in keys):
                    # print(f"deactivate d={d.name} keys={keys}")
                    d.active = False
                    if others:
                        d.deactivate_drop_list()
                    if collect:
                        names.append(d.name)

        if collect:
            return names

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
