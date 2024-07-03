# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
import threading

# from earthkit.data.readers.netcdf import get_fields_from_ds
from earthkit.data.core.order import build_remapping
from earthkit.data.utils import ensure_iterable

LOG = logging.getLogger(__name__)


MARS_GRIB_KEYS_NAMES = [
    "param",
    "class",
    "stream",
    "type",
    "expver",
    "date",
    "hdate",
    "andate",
    "time",
    "antime",
    "step",
    "reference",
    "anoffset",
    "verify",
    "fcmonth",
    "fcperiod",
    "leadtime",
    "opttime",
    "origin",
    "domain",
    "method",
    "diagnostic",
    "iteration",
    "number",
    "quantile",
    "levtype",
    "levelist",
]

GEO_KEYS = ["md5GridSection"]


CUSTOM_VARIABLE_KEYS = ["param_level"]
VARIABLE_KEYS = [
    "param",
    "variable",
    "parameter",
    "shortName",
    "long_name",
    "name",
    "cfName",
    "cfVarName",
] + CUSTOM_VARIABLE_KEYS


CUSTOM_KEYS = ["valid_datetime", "base_datetime", "level_and_type"]

CF_GRIB_KEYS_NAMES = [
    "cfVarName",
    "class",
    "stream",
    "type",
    "expver",
    "date",
    "hdate",
    "andate",
    "time",
    "antime",
    "step",
    "reference",
    "anoffset",
    "verify",
    "fcmonth",
    "fcperiod",
    "leadtime",
    "opttime",
    "origin",
    "domain",
    "method",
    "diagnostic",
    "iteration",
    "number",
    "quantile",
    "typeOfLevel",
    "level",
    "units",
]


CF_VAR_ATTRIBUTES = ["cfName", "units"]
CF_MAPPING = {"cfName": "standard_name"}

COORD_ATTRS = {
    # geography
    "latitude": {"units": "degrees_north", "standard_name": "latitude", "long_name": "latitude"},
    "longitude": {"units": "degrees_east", "standard_name": "longitude", "long_name": "longitude"},
    # vertical
    "base_datetime": {
        # "units": "seconds since 1970-01-01T00:00:00",
        # "calendar": "proleptic_gregorian",
        "standard_name": "forecast_reference_time",
        "long_name": "initial time of forecast",
    },
    "step": {
        # "units": "hours",
        "standard_name": "forecast_period",
        "long_name": "time since forecast_reference_time",
    },
    "time": {
        # "units": "seconds since 1970-01-01T00:00:00",
        # "calendar": "proleptic_gregorian",
        "standard_name": "time",
        "long_name": "valid_time",
    },
    "valid_datetime": {
        # "units": "seconds since 1970-01-01T00:00:00",
        # "calendar": "proleptic_gregorian",
        "standard_name": "time",
        "long_name": "valid_time",
    },
    "valid_time": {
        # "units": "seconds since 1970-01-01T00:00:00",
        # "calendar": "proleptic_gregorian",
        "standard_name": "time",
        "long_name": "valid_time",
    },
    "levelist": {
        "units": "hPa",
        "positive": "down",
        "stored_direction": "decreasing",
        "standard_name": "air_pressure",
        "long_name": "pressure",
    },
}


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


DEFAULT_METADATA_KEYS = {
    "CF": [
        "shortName",
        "units",
        "name",
        "cfName",
        "cfVarName",
        "missingValue",
        "totalNumber",
        "numberOfDirections",
        "numberOfFrequencies",
        "NV",
        "gridDefinitionDescription",
    ]
}


def get_metadata_keys(tag, metadata):
    if tag == "describe":
        return metadata.describe_keys()
    elif tag in DEFAULT_METADATA_KEYS:
        return DEFAULT_METADATA_KEYS[tag]
    elif tag == "":
        return []

    raise ValueError(f"Unsupported metadata tag={tag}")


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

        if self.profile.variable_key in self:
            raise ValueError(
                (
                    f"Variable key {self.profile.variable_key} cannot be in "
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
        print("UPDATE levtype", ds.index("levtype"))
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


class ProfileConf:
    def __init__(self):
        self._conf = None
        self._lock = threading.Lock()

    def get(self, name):
        if name not in self._conf:
            self._load(name)
        return self._conf[name]

    def _load(self, name):
        if name not in self._conf:
            with self._lock:
                here = os.path.dirname(__file__)
                path = os.path.join(here, f"{name}.yaml")
                if os.path.exists(path):
                    import yaml

                    try:
                        with open(path, "r") as f:
                            self._conf[name] = yaml.safe_load(f)
                    except Exception as e:
                        LOG.exception(f"Failed to import array backend code {name} from {path}. {e}")
                raise ValueError(f"Profile {name} not found")


PROFILE_CONF = ProfileConf()


class IndexProfile:
    fixed_dim_order = False

    def __init__(
        self,
        index_keys=None,
        mandatory_keys=None,
        variable_key=None,
        squeeze=True,
        extra_index_keys=None,
        remapping=None,
        drop_variables=None,
        valid_datetime_dim=False,
        base_datetime_dim=False,
        valid_datetime_coord=False,
        level_per_type_dim=False,
    ):
        self.squeeze = squeeze
        self.index_keys = [] if index_keys is None else list(index_keys)

        # print("INIT index_keys", self.index_keys)
        mandatory_keys = [] if mandatory_keys is None else list(mandatory_keys)
        self.add_keys(mandatory_keys)
        # print("INIT index_keys", self.index_keys)

        # print("INIT extra_index_keys", extra_index_keys)
        extra_index_keys = [] if extra_index_keys is None else ensure_iterable(extra_index_keys)

        self.add_keys(ensure_iterable(extra_index_keys))
        # print("INIT index_keys", self.index_keys)
        if variable_key is not None:
            self.add_keys([variable_key])

        self.dims = []

        # print("INIT index_keys", self.index_keys)

        remapping = build_remapping(remapping)
        # print(f"{remapping=}")
        if remapping:
            for k in remapping.lists:
                d = RemappingDim(self, k, remapping.lists[k])
                self.dims.append(d)

        for k in self.index_keys:
            if not remapping or k not in remapping.lists:
                ck = CompoundKey.make(k)
                if ck is not None:
                    d = CompoundKeyDim(self, ck)
                    # print("CompoundKeyDim", ck.name, ck.keys)
                    self.dims.append(d)

        if valid_datetime_dim:
            self.dims.append(ValidDatetimeDim(self))
        elif base_datetime_dim:
            self.dims.append(BaseDatetimeDim(self))
            self.dims.append(StepDim(self))
            if valid_datetime_coord:
                self.add_keys(["valid_datetime"])
        else:
            self.dims.extend([DateDim(self), TimeDim(self), StepDim(self)])

        self.level_per_type_dim = level_per_type_dim
        if level_per_type_dim:
            self.dims.append(LevelPerTypeDim(self))
        # elif "level_and_type" in self.index_keys:
        #     self.dims.append(LevelAndTypeDim(self))
        else:
            self.dims.append(LevelDim(self))
            self.dims.append(LevelTypeDim(self))

        self.dims.append(NumberDim(self))

        # print("INIT dim_keys", self.dim_keys)
        self.drop_variables = drop_variables

        self.variables = []
        if variable_key is not None:
            self.user_variable_key = True
            self.variable_key = variable_key
        else:
            self.user_variable_key = False
            self.variable_key = self.guess_variable_key()

        # print("INIT variable key", self.variable_key)
        # print("INIT index_keys", self.index_keys)
        # print("INIT dim_keys", self.dim_keys)

    @staticmethod
    def make(name, *args, **kwargs):
        profile = PROFILES.get(name, IndexProfile)
        conf = PROFILE_CONF.get(name)
        return profile.from_conf(conf, *args, **kwargs)

    @classmethod
    def from_conf(cls, conf, *args, **kwargs):
        conf = conf.copy()
        options = conf.pop("options", {})
        kwargs.update(options)

        # self.index_keys = conf["index_keys"]
        # self.mandatory_keys = conf.get("mandatory_keys", [])
        # self.groups = conf.get("groups", {})

        # for k in self.mandatory_keys:
        #     if k not in self.index_keys:
        #         self.index_keys.append(k)

        return cls(*args, **kwargs, **conf)

    @property
    def dim_keys(self):
        return [d.name for d in self.dims if d.active]

    def add_keys(self, keys):
        self.index_keys += [key for key in keys if key not in self.index_keys]

    def guess_variable_key(self):
        """If any remapping/compound key contains a param key, the variable key is set
        to that key.
        """
        for d in self.dims:
            if any(p in d for p in VARIABLE_KEYS):
                # print(f"GUESS deactivate dim={d.name} keys={d.drop}")
                assert d.name in self.index_keys
                d.active = False
                d.deactivate_related()
                return d.name

        for k in CUSTOM_VARIABLE_KEYS:
            if k in self.index_keys:
                return k

        return VARIABLE_KEYS[0]

    # def adjust_dims_to_remapping(self):
    #     if self.remapping:
    #         for k, v in self.remapping.lists.items():
    #             for _, d in self.managed_dims.items():
    #                 if k in d or any(p in d for p in v):
    #                     d.remove()

    #             # if k in self.dim_keys:
    #             #     for rk in v:
    #             #         group = self._key_group(rk)
    #             #         for key in group:
    #             #             if key in self.dim_keys:
    #             #
    #             #

    def remove_dims(self, keys):
        self.dims = [d for d in self.dims if any(k in d for k in keys)]

    def _remove_dim_keys(self, drop_keys):
        self.dim_keys = [key for key in self.dim_keys if key not in drop_keys]

    def _squeeze(self, ds, attributes):
        self.dim_keys = [key for key in self.dim_keys if key in ds.indices() and key not in attributes]

    def _update_variables(self, ds):
        if not self.user_variable_key and self.variable_key in VARIABLE_KEYS:
            self.variables = ds.index(self.variable_key)
            if not self.variables:
                for k in VARIABLE_KEYS:
                    if k != self.variable_key:
                        self.variables = ds.index(k)
                        if self.variables:
                            self.variable_key = k
                            break
        else:
            self.variables = ds.index(self.variable_key)
            if self.drop_variables:
                self.variables = [v for v in self.variables if v not in self.drop_variables]

        if not self.variables:
            raise ValueError(f"No values found for variable key {self.variable_key}")

    def _update_dims(self, ds, attributes):
        # variable keys cannot be dimensions
        # print("UPDATE dim_keys[0]", self.dim_keys)
        var_keys = VARIABLE_KEYS + [self.variable_key]
        for d in self.dims:
            # print(f" d={d.name}")
            if d.active and any(k in d for k in var_keys):
                # print("DEACTIVATE dim={d.name} keys={d.group}")
                d.active = False
                d.deactivate_related()

        # print("UPDATE dim_keys[0a]", self.dim_keys)

        for d in self.dims:
            d.update(ds, attributes, self.squeeze)
        # print("UPDATE dim_keys[0b]", self.dim_keys)

        # if self.level_per_type_dim:
        #     print("UPDATE levtype", ds.index("levtype"))
        #     for x in ds.index("levtype"):
        #         self.dims.append(LevelPerTypeDim(self))

        new_dims = []
        for k in self.index_keys:
            if len(ds.index(k)) > 1:
                if k not in var_keys and all(d.allows(k) for d in self.dims):
                    new_dims.append(OtherDim(self, k))
        self.dims.extend(new_dims)

        # var_keys = VARIABLE_KEYS + [self.variable_key]
        # for d in self.dims:
        #     if d.active and any(k in d for k in var_keys):
        #         d.active = False

        # print("UPDATE dim_keys[1]", self.dim_keys)

        # self.dim_keys = [
        #     key
        #     for key in self.dim_keys
        #     if key in self.managed_dims
        #     or (key in ds.indices() and key not in attributes)
        # ]

        # for ck in self.compound_keys:
        #     self._remove_dim_keys.remove(ck.keys)

        # print("UPDATE dim_keys[2]", self.dim_keys)

        # assert self.dim_keys
        assert self.variable_key not in self.dim_keys

    def update(self, ds, attributes):
        """
        Parameters
        ----------
        ds: fieldlist
            FieldList object with cached metadata
        attributes: dict
            Index keys which has a single (valid) value
        """
        self._update_variables(ds)
        self._update_dims(ds, attributes)

        assert self.variable_key is not None
        assert self.variables
        # assert self.dim_keys
        assert self.variable_key not in self.dim_keys

        # print("UPDATE variable_key", self.variable_key)
        # print("UPDATE variables", self.variables)
        # print(" -> dim_keys", self.dim_keys)

    @property
    def sort_keys(self):
        return [self.variable_key] + self.dim_keys

    def attributes(self):
        return dict()

    def var_attributes(self):
        return list()

    def coord_attrs(self, name):
        return COORD_ATTRS.get(name, {})


class MarsProfile(IndexProfile):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            index_keys=MARS_GRIB_KEYS_NAMES,
            mandatory_keys=GEO_KEYS,
            **kwargs,
        )


class Coord:
    def __init__(self, name, vals, dims=None):
        self.name = name
        self.vals = vals
        self.dims = dims
        if not self.dims:
            self.dims = (self.name,)
        self.convert()

    @staticmethod
    def make(name, *args, **kwargs):
        if name in ["date", "valid_datetime", "base_datetime"]:
            return DateTimeCoord(name, *args, **kwargs)
        elif name in ["step"]:
            return StepCoord(name, *args, **kwargs)
        return Coord(name, *args, **kwargs)

    def make_var(self, profile):
        import xarray

        # self.profile.remap_coords(self.name)
        return xarray.Variable(profile.rename_dims(self.dims), self.vals, profile.coord_attrs(self.name))

    def convert(self):
        pass


class DateTimeCoord(Coord):
    def convert(self):
        if isinstance(self.vals, list):
            from earthkit.data.utils.dates import to_datetime_list

            self.vals = to_datetime_list(self.vals)


class StepCoord(Coord):
    def convert(self):
        from earthkit.data.utils.dates import step_to_delta

        self.vals = [step_to_delta(x) for x in self.vals]


class CFProfile(IndexProfile):
    fixed_dim_order = True

    def __init__(self, *args, variable_key=None, **kwargs):
        variable_key = "cfVarName"
        super().__init__(
            *args,
            index_keys=CF_GRIB_KEYS_NAMES,
            mandatory_keys=GEO_KEYS,
            variable_key=variable_key,
            **kwargs,
        )

    def attributes(self):
        return {"Conventions": "CF-1.8"}

    def var_attributes(self):
        return CF_VAR_ATTRIBUTES

    def remap(self, d):
        def _remap(k):
            return CF_MAPPING.get(k, k)

        return {_remap(k): v for k, v in d.items()}

    # def add_coords(self, name, vals):
    #     if not self.tensor_coords:
    #         self.tensor_coords = {
    #             k: (k, v, self.profile.coord_attrs(k)) for k, v in tensor.user_coords.items()
    #         }
    #     else:
    #         for k, v in tensor.user_coords.items():
    #             if k not in self.tensor_coords:
    #                 self.tensor_coords[k] = (k, v, self.profile.coord_attrs(k))

    def rename_dims(self, dims):
        r = {"valid_datetime": "valid_time", "base_datetime": "forecast_reference_time", "levelist": "level"}
        return [r.get(d, d) for d in dims]

    def rename_coords(self, coords):
        r = {"valid_datetime": "valid_time", "base_datetime": "forecast_reference_time", "levelist": "level"}
        return {r.get(k, k): v for k, v in coords.items()}

    def adjust_attributes(self, attrs):
        attrs.pop("units", None)
        return attrs


PROFILES = {"mars": MarsProfile, "cf": CFProfile}
