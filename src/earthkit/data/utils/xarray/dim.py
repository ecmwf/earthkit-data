# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.utils import ensure_dict
from earthkit.data.utils import ensure_iterable
from earthkit.data.utils.dates import datetime_from_grib

LOG = logging.getLogger(__name__)


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


COMPOUND_KEYS = {v.name: v for v in [ParamLevelKey]}


ENS_KEYS = ["number", "perturbationNumber", "realization"]
LEVEL_KEYS = ["level", "levelist", "topLevel", "bottomLevel", "levels"]
LEVEL_TYPE_KEYS = ["typeOfLevel", "levtype"]
DATE_KEYS = ["date", "andate", "validityDate", "dataDate", "hdate", "referenceDate", "indexingDate"]
TIME_KEYS = ["time", "antime", "validityTime", "dataTime", "referenceTime", "indexingTime"]
STEP_KEYS = ["step_timedelta", "step", "endStep", "stepRange", "forecastMonth", "fcmonth"]
MONTH_KEYS = ["forecastMonth", "fcmonth"]
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

KEYS = (
    ENS_KEYS
    + LEVEL_KEYS
    + LEVEL_TYPE_KEYS
    + DATE_KEYS
    + TIME_KEYS
    + STEP_KEYS
    + VALID_DATETIME_KEYS
    + BASE_DATETIME_KEYS
)


def get_keys(keys, drop=None):
    r = list(keys)
    if drop:
        drop = ensure_iterable(drop)
        r = [k for k in r if k not in drop]
    return r


def find_alias(key, drop=None):
    keys = KEYS
    r = []
    for k in keys:
        if key in k:
            r.extend(k)

    if drop:
        drop = ensure_iterable(drop)
        r = [k for k in r if k not in drop]
    return r


def make_dim(owner, *args, name=None, key=None, **kwargs):
    predef_key = key or name

    if predef_key in PREDEFINED_DIMS:
        return PREDEFINED_DIMS[predef_key](owner, *args, name=name, key=key, **kwargs)

    ck = CompoundKey.make(name)
    if ck is not None:
        d = CompoundKeyDim(owner, ck)
    else:
        # print("args", args, "kwargs", kwargs, "name", name, "key", key)
        d = OtherDim(owner, *args, name=name, key=key, **kwargs)
    return d


class Dim:
    """Represent a dimension.

    Parameters
    ----------
    name: str
        Name of the dimension.
    key: str
        Metadata key to be used to get the values of the dimension.
    alias: list
        List of metadata keys that has the same meaning as the ``key``.
    drop: list
        List of metadata keys used to identify the dimensions that cannot be used when the
        current dimension is ``active``. When this dimension is active and the dimension
        consistency is checked all the other dimensions containing any keys from ``drop``
        as ``name``, ``key`` or ``alias`` should be deactivated.
    active: bool
        Status. Only active dimensions are used in the dataset construction.
    """

    name = None
    key = None
    label = None
    alias = None
    drop = None
    enforce_unique = False

    def __init__(self, owner, name=None, key=None, alias=None, drop=None, active=True):
        self.owner = owner
        self.profile = owner.profile
        self.active = active

        if name is not None:
            self.name = name

        if key is not None:
            self.key = key

        if not self.key and self.name:
            self.key = self.name

        if not self.name and self.key:
            self.name = self.key

        if not self.name:
            raise ValueError("name must be specified")

        if not self.key:
            raise ValueError("key must be specified")

        if alias is not None:
            self.alias = alias

        if drop is not None:
            self.drop = drop

        def _drop(v):
            return [k for k in v if k not in [self.name, self.key]]

        self.alias = _drop(ensure_iterable(self.alias))
        self.drop = _drop(ensure_iterable(self.drop))

        assert self.name not in self.alias
        assert self.name not in self.drop
        assert self.key not in self.alias
        assert self.key not in self.drop

        self.coords = {}

    def __contains__(self, key):
        return key in [self.name, self.key] or key in self.alias

    def check(self):
        # print(f"CHECK {self.name} {self.key} {self.active}")
        if self.active:
            self.active = self.condition()
            if self.active:
                self.deactivate_drop_list()

    def condition(self):
        return True

    def update(self, ds):
        # if self.key in ds.indices():
        #     print(f"-> {self.name} key={self.key} active={self.active} ds={ds.index(self.key)}")

        if not self.active:
            return

        # sanity check
        if self.profile.variable.key in self:
            raise ValueError(
                (f"Variable key {self.profile.variable.key} cannot be in " f"dimension={self.name}")
            )

        # print(f"key={self.key} index={ds.index(self.key)}")

        vals = ds.index(self.key)

        if len(vals) == 0:
            self.active = False

        # assert self.name in self.profile.dim_keys, f"self.name={self.name}"
        # if self.key not in self.owner.ensure_dims:
        #     num = len(ds.index(self.key))
        #     if num == 0 or (self.key not in self.owner.ensure_dims and num == 1 and squeeze):
        #         self.active = False

        # self.deactivate_drop_list()

    def deactivate_drop_list(self):
        self.owner.deactivate([self.name, self.key] + self.drop, ignore_dim=self)

    def as_coord(self, key, values, component, source):
        if key not in self.coords:
            from .coord import Coord

            self.coords[key] = Coord.make(key, values, ds=source, component=component)
        return key, self.coords[key]

    def remapping_keys(self):
        return []

    def __repr__(self):
        return f"{self.__class__.__name__}(name={self.name}, key={self.key})"


class NumberDim(Dim):
    alias = get_keys(ENS_KEYS)


class DateDim(Dim):
    name = "date"
    drop = get_keys(DATE_KEYS + DATETIME_KEYS, drop="date")


class TimeDim(Dim):
    name = "time"
    drop = get_keys(TIME_KEYS + DATETIME_KEYS, drop="time")


# class StepDim(Dim):
#     name = "step"
#     drop = get_keys(STEP_KEYS + VALID_DATETIME_KEYS, drop="step")


class StepDim(Dim):
    name = "step"
    drop = get_keys(STEP_KEYS + VALID_DATETIME_KEYS, drop=["step_timedelta"])


class ValidTimeDim(Dim):
    name = "valid_time"
    drop = get_keys(DATE_KEYS + TIME_KEYS + DATETIME_KEYS, drop="valid_time")


class ForecastRefTimeDim(Dim):
    name = "forecast_reference_time"
    drop = get_keys(DATE_KEYS + TIME_KEYS + DATETIME_KEYS, drop="forecast_reference_time")
    alias = ["base_datetime"]


class IndexingTimeDim(Dim):
    name = "indexing_time"
    drop = get_keys(DATE_KEYS + TIME_KEYS + DATETIME_KEYS, drop="indexing_time")


class ReferenceTimeDim(Dim):
    name = "reference_time"
    drop = get_keys(DATE_KEYS + TIME_KEYS + DATETIME_KEYS, drop="reference_time")


class CustomForecastRefDim(Dim):
    @staticmethod
    def _datetime(val):
        if not val:
            return None
        else:
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
            self.key = self._name(date, time)
            self.drop = [date, time]
            if active:
                owner.register_remapping(
                    {self.key: "{" + date + "}_{" + time + "}"},
                    patch={self.key: CustomForecastRefDim._datetime},
                )
        else:
            raise ValueError(f"Invalid keys={keys}")
        super().__init__(owner, *args, active=active, **kwargs)

    def _name(self, date, time):
        if date.endswith("Date") and time.endswith("Time") and date[:-4] == time[:-4]:
            return date[:-4] + "_time"
        return f"{date}_{time}"


class LevelDim(Dim):
    alias = get_keys(LEVEL_KEYS)


class LevelTypeDim(Dim):
    alias = get_keys(LEVEL_TYPE_KEYS)
    enforce_unique = True


class LevelPerTypeDim(Dim):
    name = "_level_per_type"
    drop = get_keys(LEVEL_KEYS + LEVEL_TYPE_KEYS, drop=name)

    def __init__(self, owner, level_key, level_type_key, *args, **kwargs):
        self.key = level_key
        self.level_key = level_key
        self.level_type_key = level_type_key
        super().__init__(owner, *args, **kwargs)

    def as_coord(self, key, values, component, source):
        lev_type = source[0].metadata(self.level_type_key)
        if not lev_type:
            raise ValueError(f"{self.level_type_key} not found in metadata")

        if lev_type not in self.coords:
            from .coord import Coord

            coord = Coord.make(lev_type, list(values), ds=source)
            self.coords[lev_type] = coord
        return lev_type, self.coords[lev_type]


class LevelAndTypeDim(Dim):
    name = "level_and_type"
    drop = get_keys(LEVEL_KEYS + LEVEL_TYPE_KEYS, drop=name)

    def __init__(self, owner, level_key, level_type_key, active=True, *args, **kwargs):
        self.level_key = level_key
        self.level_type_key = level_type_key
        if active:
            owner.register_remapping(
                {self.name: "{" + self.level_key + "}{" + self.level_type_key + "}"},
            )
        super().__init__(owner, *args, active=active, **kwargs)

    def remapping_keys(self):
        return [self.level_key, self.level_type_key]


class RemappingDim(Dim):
    def __init__(self, owner, name, keys, **kwargs):
        self.name = name
        self.keys = [k for k in keys if k]
        self.drop = self.build_drop(keys)
        super().__init__(owner, **kwargs)

    def build_drop(self, keys):
        r = list(keys)
        for k in keys:
            r.extend(find_alias(k))
        return r

    def remapping_keys(self):
        return self.keys


class CompoundKeyDim(RemappingDim):
    def __init__(self, owner, ck):
        self.ck = ck
        super().__init__(owner, ck.name, ck.keys)


class OtherDim(Dim):
    pass


class DimRole:
    NAMES = ("number", "date", "time", "step", "level", "level_type", "forecast_reference_time", "valid_time")

    def __init__(self, d, name_as_key=True):
        self.d = d
        self.name_as_key = name_as_key

        if "ens" in d:
            import warnings

            warnings.warn("'ens' key in dim_roles is deprecated. Use 'number' instead", DeprecationWarning)
            self.d["number"] = self.d.pop("ens")

        for k in d:
            if k not in self.NAMES:
                raise ValueError(f"Invalid dim role name={k}. Must be one of {self.NAMES}")

    def role(self, name, default=None, raise_error=True):
        if name in self.d:
            return self.d[name], name if self.name_as_key else self.d[name]
        if default is not None:
            return default
        if raise_error:
            raise ValueError(f"Dim role {name} not found in {self.d}")
        else:
            return default, default


class DimMode:
    default = {}  # maps key to name

    def build(self, profile, owner, active=True, dims=None):
        if not dims:
            dims = self.default
        return {name: make_dim(owner, name=name, key=key, active=active) for name, key in dims.items()}


class ForecastTimeDimMode(DimMode):
    name = "forecast"
    DATES = ["date", "dataDate"]
    TIMES = ["time", "dataTime"]

    def build(self, profile, owner, active=True):
        ref_time_key, ref_time_name = owner.dim_roles.role("forecast_reference_time", raise_error=False)

        if ref_time_key == "forecast_reference_time":
            ref_time_dim = ForecastRefTimeDim(owner, name=ref_time_name, active=active)
        elif ref_time_key:
            ref_time_dim = make_dim(owner, name=ref_time_name, key=ref_time_key, active=active)
        else:
            date, _ = owner.dim_roles.role("date")
            time, _ = owner.dim_roles.role("time")
            built_in = date in self.DATES and time in self.TIMES
            if built_in:
                ref_time_dim = ForecastRefTimeDim(owner, name=ref_time_name, active=active)
            else:
                ref_time_dim = CustomForecastRefDim(owner, [date, time], name=ref_time_name, active=active)

        step_key, step_name = owner.dim_roles.role("step")
        step_dim = make_dim(owner, name=step_name, key=step_key, active=active)

        self.register_ref_time_key(ref_time_dim.key)
        self.register_step_key(step_dim.key)

        return {d.name: d for d in [ref_time_dim, step_dim]}

    def register_ref_time_key(self, name):
        global BASE_DATETIME_KEYS
        global VALID_DATETIME_KEYS
        if name not in BASE_DATETIME_KEYS:
            BASE_DATETIME_KEYS.append(name)

    def register_step_key(self, name):
        global STEP_KEYS
        if name not in STEP_KEYS:
            STEP_KEYS.append(name)


class ValidTimeDimMode(DimMode):
    name = "valid_time"
    default = {"valid_time": "valid_time"}


class RawTimeDimMode(DimMode):
    name = "raw"

    def build(self, profile, owner, active=True):
        dims = {}
        for k in ["date", "time", "step"]:
            key, name = owner.dim_roles.role(k)
            dims[name] = key
        return super().build(profile, owner, active=active, dims=dims)


class LevelDimMode(DimMode):
    name = "level"

    def build(self, profile, owner, **kwargs):
        # level
        key, name = owner.dim_roles.role("level")
        level_dim = LevelDim(owner, name=name, key=key, **kwargs)

        # level_type
        key, name = owner.dim_roles.role("level_type")
        level_type_dim = LevelTypeDim(owner, name=name, key=key, **kwargs)

        return {level_dim.key: level_dim, level_type_dim.key: level_type_dim}


class LevelAndTypeDimMode(DimMode):
    name = "level_and_type"
    dim = LevelAndTypeDim

    def build(self, profile, owner, **kwargs):

        level_key, _ = owner.dim_roles.role("level")
        level_type_key, _ = owner.dim_roles.role("level_type")
        return {self.name: self.dim(owner, level_key, level_type_key, **kwargs)}


class LevelPerTypeDimMode(LevelAndTypeDimMode):
    name = "level_per_type"
    dim = LevelPerTypeDim


TIME_DIM_MODES = {v.name: v for v in [ForecastTimeDimMode, ValidTimeDimMode, RawTimeDimMode]}
LEVEL_DIM_MODES = {v.name: v for v in [LevelDimMode, LevelPerTypeDimMode, LevelAndTypeDimMode]}


class DimBuilder:
    used = {}
    ignored = {}

    def dims(self):
        return self.used, self.ignored


class NumberDimBuilder(DimBuilder):
    name = "number"

    def __init__(self, profile, owner):
        key, name = owner.dim_roles.role("number")
        self.used = {self.name: NumberDim(owner, name=name, key=key)}


class TimeDimBuilder(DimBuilder):
    name = "time"

    def __init__(self, profile, owner):
        mode = TIME_DIM_MODES.get(owner.time_dim_mode, None)
        if mode is None:
            raise ValueError(f"Unknown time_dim_mode={owner.time_dim_mode}")

        mode = mode()
        self.used = mode.build(profile, owner)
        self.ignored = {
            k: v().build(profile, owner, active=False) for k, v in TIME_DIM_MODES.items() if v != mode
        }


class LevelDimBuilder(DimBuilder):
    name = "level"

    def __init__(self, profile, owner):
        mode = LEVEL_DIM_MODES.get(owner.level_dim_mode, None)
        if mode is None:
            raise ValueError(f"Unknown level_dim_mode={owner.level_dim_mode}")

        mode = mode()
        self.used = mode.build(profile, owner)
        self.ignored = {
            k: v().build(profile, owner, active=False) for k, v in LEVEL_DIM_MODES.items() if v != mode
        }


DIM_BUILDERS = {v.name: v for v in [NumberDimBuilder, TimeDimBuilder, LevelDimBuilder]}


def ensure_dim_map(d):
    if isinstance(d, dict):
        return d
    d = ensure_iterable(d)
    r = {}
    for k in d:
        if isinstance(k, str):
            r[k] = k
        elif isinstance(k, tuple) and len(k) == 2:
            r[k[0]] = k[1]
        elif isinstance(k, dict):
            for kk, vv in k.items():
                r[kk] = vv
    return r


class DimHandler:
    def __init__(
        self,
        profile,
        extra_dims,
        drop_dims,
        ensure_dims,
        fixed_dims,
        split_dims,
        rename_dims,
        dim_roles,
        dim_name_from_role_name,
        dims_as_attrs,
        time_dim_mode,
        level_dim_mode,
        squeeze,
    ):

        self.profile = profile

        self.dim_roles = DimRole(dim_roles, name_as_key=dim_name_from_role_name)
        # self.dim_name_from_role_name = dim_name_from_role_name
        self.extra_dims = ensure_dim_map(extra_dims)
        self.drop_dims = ensure_iterable(drop_dims)
        self.ensure_dims = ensure_iterable(ensure_dims)
        self.fixed_dims = ensure_dim_map(fixed_dims)
        self.split_dims = ensure_iterable(split_dims)
        self.rename_dims_map = ensure_dict(rename_dims)
        self.dims_as_attrs = list(ensure_iterable(dims_as_attrs))
        self.time_dim_mode = time_dim_mode
        self.level_dim_mode = level_dim_mode
        self.squeeze = squeeze

        # if "ens" in self.dim_roles:
        #     Warning.deprecated("'ens' key in dim_roles is deprecated. Use 'number' instead")
        #     self.dim_roles["number"] = self.dim_roles.pop("ens")

        # if self.dim_name_from_role_name:
        #     d = {v: k for k, v in self.dim_roles.items()}
        #     for k in list(self.rename_dims_map.keys()):
        #         if k in self.dim_roles:
        #             d[self.dim_roles[k]] = self.rename_dims_map.pop(k)

        #     d.update(self.rename_dims_map)
        #     self.rename_dims_map = d

        self.var_key_dim = None

        if self.fixed_dims:
            self.dims = self._init_fixed_dims()
        else:
            dims = self._init_dims()

            assert self.var_key_dim

            # prepend the variable key as dimension to ensure it will be used
            # in the checks
            assert "__var_key_dim__" not in dims
            self.dims = {"__var_key_dim__": self.var_key_dim, **dims}

            # print(f"INIT dims={self.dims}")
            # check dims consistency. The ones that can be used
            # marked as active
            for k, d in self.dims.items():
                d.check()

            var_keys = ["__var_key_dim__"]
            if self.profile.variable.key:
                var_keys.append(self.profile.variable.key)

            # print(f" -> dims={self.dims}")
            # check for any dimensions related to variable keys. These have to
            # be removed from the list of active dims.
            var_dims = self.deactivate(var_keys, others=True, collect=True)
            if var_dims:
                if self.profile.variable.key in var_dims:
                    var_dims.remove(self.profile.variable.key)
                if var_dims:
                    raise ValueError(self.var_dim_found_error_message(var_dims))

            # only the active dims are used
            dims = {k: v for k, v in self.dims.items() if v.active and k not in self.core_dim_order}
            for k in self.core_dim_order:
                if k not in dims and k in self.dims and self.dims[k].active:
                    dims[k] = self.dims[k]

            self.dims = dims

        # LOG.debug(f"self.dims={self.dims}")

        # for d in self.dims.values():
        #     if d.name != d.key:
        #         if d.name in self.rename_dims_map:
        #             self.rename_dims_map[d.key] = d.name
        #         else d
        #         if d.key not in self.rename_dims_map:
        #             self.rename_dims_map[d.key] = d.name
        #         else d

        # if self.dim_name_from_role_name:
        #     d = {v: k for k, v in self.dim_roles.items()}
        #     for k in list(self.rename_dims_map.keys()):
        #         if k in self.dim_roles:
        #             d[self.dim_roles[k]] = self.rename_dims_map.pop(k)

        #     d.update(self.rename_dims_map)
        #     self.rename_dims_map = d

        self.var_key_dim = None

        # ensure all the required keys are in the profile
        keys = []
        for d in self.dims.values():
            keys.append(d.key)

        self.profile.add_keys(keys)

        # self.profile.prepend_keys(self.split_dims)

    def _init_remapping_dims(self, keys):
        # A remapping can be either a variable key or a user specified dimension. They can contain
        # variable related keys, which will be checked later.
        remapping = self.profile.remapping.build()
        remapping_dims = {}
        if remapping:
            for k in remapping.lists:
                d = RemappingDim(self, k, remapping.components(k))
                if k == self.profile.variable.key:
                    self.var_key_dim = d
                elif k in keys:
                    remapping_dims[k] = d
                # else:
                #     raise ValueError(f"Key {k} found in remapping but not in extra_dims or ensure_dims")
        return remapping_dims

    def _init_fixed_dims(self):
        assert self.fixed_dims

        if self.profile.variable.key in self.fixed_dims:
            raise ValueError((f"Variable key {self.profile.variable.key} cannot be in fixed_dims."))
        if self.extra_dims:
            raise ValueError(f"extra_dims={self.extra_dims} cannot be used with fixed_dims")
        if self.drop_dims:
            raise ValueError(f"drop_dims={self.drop_dims} cannot be used with fixed_dims")

        # if self.ensure_dims:
        #     for k in self.ensure_dims:
        #         if k not in self.fixed_dims and k not in self.split_dims:
        #             raise ValueError(
        #                 (
        #                     f'Key "{k}" found in ensure_dims but not found in fixed_dims! '
        #                     "When fixed_dims specified ensure_dims can only contain keys "
        #                     "from fixed_dims"
        #                 )
        #             )

        # self.ensure_dims = [k for k in self.fixed_dims]
        self.ensure_dims = list(self.fixed_dims.keys())
        dims = {k: make_dim(self, name=k, key=v) for k, v in self.fixed_dims.items()}
        return dims

    def _init_dims(self):
        assert not self.fixed_dims

        for k in self.drop_dims:
            if k in self.extra_dims:
                raise ValueError(f"Key {k} cannot be in drop_dims and extra_dims")
            if k in self.ensure_dims:
                raise ValueError(f"Key {k} cannot be in drop_dims and ensure_dims")

        for k in self.split_dims:
            if k not in self.drop_dims and k not in self.extra_dims and k not in self.ensure_dims:
                self.drop_dims.append(k)

        def _remove_duplicates(keys):
            r = []
            for k in keys:
                if k not in r:
                    r.append(k)
            return r

        if self.profile.variable.key:
            var_keys = [self.profile.variable.key]
        else:
            var_keys = []

        # non-core dims
        keys = list(self.extra_dims.keys()) + self.ensure_dims
        keys = _remove_duplicates(keys)

        remapping_dims = self._init_remapping_dims(keys)
        dims = dict(**remapping_dims)

        if not self.var_key_dim:
            assert self.profile.variable.key is not None
            self.var_key_dim = make_dim(self, name=self.profile.variable.key)

        # dims at this point can only contain remapping dims
        for k in keys:
            # note: remapping overrides existing keys
            if k not in dims:
                dims[k] = make_dim(self, name=k)

        dims = {k: v for k, v in dims.items() if k not in self.drop_dims}
        # print(f"dims", dims)

        # initial check for variable-related dimensions
        invalid_var_keys = []
        for k in dims.keys():
            if k in var_keys:
                invalid_var_keys.append(k)

        if invalid_var_keys:
            raise ValueError(self.var_dim_found_error_message(invalid_var_keys))

        # add predefined dimensions
        core_dims = {}
        ignored = {}
        self.core_dim_order = []
        for k, v in DIM_BUILDERS.items():
            builder = v(self.profile, self)
            used, ignored = builder.dims()
            for k, v in used.items():
                core_dims[k] = v
                self.core_dim_order.append(k)

            ignored.update(ignored)

        for k in list(ignored.keys()):
            if k in remapping_dims:
                ignored.pop(k)

        # print(f"ignored", ignored)

        # construct initial dims, ensure core dims are in the right order
        all_dims = {}
        for k in dims:
            if k in remapping_dims or (k not in core_dims and k not in ignored):
                if k in self.ensure_dims or k not in self.drop_dims:
                    all_dims[k] = dims[k]

            # # if k not in self.drop_dims and k not in self.split_dims:
            # if k in self.ensure_dims or k not in self.drop_dims and

            # if k not in self.drop_dims and (k not in self.split_dims or k in self.ensure_dims):
            #     if k in remapping_dims or (k not in core_dims and k not in ignored):
            #         all_dims[k] = dims[k]

        for k in core_dims:
            if k not in all_dims and k not in self.drop_dims and k not in remapping_dims:
                # assert k not in all_dims
                all_dims[k] = core_dims[k]

        # print(f"all_dims", all_dims)
        return all_dims

    def var_dim_found_error_message(self, keys):
        return (
            f'Variable-related keys "{keys}"" cannot be dimensions. Such a key'
            " must be specified as the variable_key. The variable_key can only "
            f'be set to a single key. Its current value is "{self.profile.variable.key}"'
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

    def update(self, ds):
        for d in self.dims.values():
            d.update(ds)

        self.dims = {k: v for k, v in self.dims.items() if v.active}

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
                name, coord = d.as_coord(k, v, tensor.source)
                r[name] = coord

        return r

    def to_list(self):
        return list(self.dims.values())

    def get_dims(self, names):
        r = []
        for name in names:
            if name in self.dims:
                r.append(self.dims[name])
            else:
                r.append(make_dim(self, name=name))
        return r

    def rename_dataset_dims(self, dataset):
        # first rename the dimensions where the name and key are different
        mapping = {}
        for d in self.dims.values():
            if d.key in dataset.dims and d.name != d.key:
                mapping[d.key] = d.name
        if mapping:
            dataset = dataset.rename(mapping)

        # then apply the user defined rename_dims_map
        if self.rename_dims_map:
            mapping = {k: v for k, v in self.rename_dims_map.items() if k in dataset.dims}
            if mapping:
                dataset = dataset.rename(mapping)

        return dataset


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
    if d.name:
        PREDEFINED_DIMS[d.name] = d
    else:
        assert d.alias
        for k in d.alias:
            if k not in PREDEFINED_DIMS:
                PREDEFINED_DIMS[k] = d
