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

from earthkit.data.core.order import build_remapping
from earthkit.data.utils import ensure_iterable

from .dim import BaseDatetimeDim
from .dim import CompoundKeyDim
from .dim import DateDim
from .dim import LevelDim
from .dim import LevelPerTypeDim
from .dim import LevelTypeDim
from .dim import NumberDim
from .dim import OtherDim
from .dim import RemappingDim
from .dim import StepDim
from .dim import TimeDim
from .dim import ValidDatetimeDim

LOG = logging.getLogger(__name__)


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


class ProfileConf:
    def __init__(self):
        self._conf = {}
        self._lock = threading.Lock()

    def get(self, name):
        if name not in self._conf:
            self._load(name)
        return dict(**self._conf[name])

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
                else:
                    raise ValueError(f"Profile {name} not found! path={path}")


PROFILE_CONF = ProfileConf()


class IndexProfile:
    fixed_dim_order = False

    def __init__(
        self,
        index_keys=None,
        ignore_index_keys=None,
        mandatory_keys=None,
        var_key=None,
        squeeze=True,
        extra_index_keys=None,
        remapping=None,
        drop_variables=None,
        valid_datetime_dim=False,
        base_datetime_dim=False,
        valid_datetime_coord=False,
        base_datetime_coord=False,
        timedelta_step=False,
        level_and_type_dim=False,
        level_per_type_dim=False,
        no_levtype_dim=False,
        fixed_dims=False,
        var_attrs=None,
        attr_mapping=None,
        dim_coord_mapping=None,
        global_attrs=None,
        coord_attrs=None,
        level_maps=None,
        dims=None,
        merge_pf_and_cf=False,
        merge_pl_levels=False,
    ):

        def _ensure_dict(d):
            return {} if d is None else d

        self.fixed_dims = _ensure_dict(fixed_dims)
        self.var_attrs = _ensure_dict(var_attrs)
        self.attr_mapping = _ensure_dict(attr_mapping)
        self.dim_coord_mapping = _ensure_dict(dim_coord_mapping)
        self.global_attrs = _ensure_dict(global_attrs)
        self.coord_attrs = _ensure_dict(coord_attrs)
        self.level_maps = _ensure_dict(level_maps)
        self.squeeze = squeeze
        self.valid_datetime_dim = valid_datetime_dim
        self.base_datetime_dim = base_datetime_dim
        self.valid_datetime_coord = valid_datetime_coord
        self.timedelta_step = timedelta_step
        self.level_and_type_dim = level_and_type_dim
        self.level_per_type_dim = level_per_type_dim
        self.var_key = var_key

        self.index_keys = [] if index_keys is None else list(index_keys)

        # print("INIT index_keys", self.index_keys)
        mandatory_keys = [] if mandatory_keys is None else list(mandatory_keys)
        self.add_keys(mandatory_keys)
        # print("INIT index_keys", self.index_keys)

        # print("INIT extra_index_keys", extra_index_keys)
        extra_index_keys = [] if extra_index_keys is None else ensure_iterable(extra_index_keys)

        self.add_keys(ensure_iterable(extra_index_keys))
        # print("INIT index_keys", self.index_keys)
        if var_key is not None:
            self.add_keys([var_key])

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
        if var_key is not None:
            self.user_var_key = True
            self.var_key = var_key
        else:
            self.user_var_key = False
            self.var_key = self.guess_var_key()

        # print("INIT variable key", self.var_key)
        # print("INIT index_keys", self.index_keys)
        # print("INIT dim_keys", self.dim_keys)

    @staticmethod
    def make(name, *args, **kwargs):
        # profile = PROFILES.get(name, IndexProfile)
        conf = PROFILE_CONF.get(name)
        return IndexProfile.from_conf(name, conf, *args, **kwargs)

    @classmethod
    def from_conf(cls, name, conf, *args, **kwargs):
        conf = conf.copy()
        options = conf.pop("options", {})

        for k, v in kwargs.items():
            if v is not None and k in conf and conf[k] != v:
                raise ValueError("Cannot specify kwargs for built in option" f" {k} in profile={name}!")

        kwargs = dict(**kwargs)
        kwargs.update(options)

        # print("kwargs", kwargs)
        # print(f"from_conf name={name} conf={conf} args={args} kwargs={kwargs}")
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

    def guess_var_key(self):
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
        if not self.user_var_key and self.var_key in VARIABLE_KEYS:
            self.variables = ds.index(self.var_key)
            if not self.variables:
                for k in VARIABLE_KEYS:
                    if k != self.var_key:
                        self.variables = ds.index(k)
                        if self.variables:
                            self.var_key = k
                            break
        else:
            self.variables = ds.index(self.var_key)
            if self.drop_variables:
                self.variables = [v for v in self.variables if v not in self.drop_variables]

        if not self.variables:
            raise ValueError(f"No values found for variable key {self.var_key}")

    def _update_dims(self, ds, attributes):
        # variable keys cannot be dimensions
        # print("UPDATE dim_keys[0]", self.dim_keys)
        var_keys = VARIABLE_KEYS + [self.var_key]
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

        # var_keys = VARIABLE_KEYS + [self.var_key]
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
        assert self.var_key not in self.dim_keys

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

        assert self.var_key is not None
        assert self.variables
        # assert self.dim_keys
        assert self.var_key not in self.dim_keys

        # print("UPDATE var_key", self.var_key)
        # print("UPDATE variables", self.variables)
        # print(" -> dim_keys", self.dim_keys)

    @property
    def sort_keys(self):
        return [self.var_key] + self.dim_keys

    def attributes(self):
        return self.global_attrs

    def var_attributes(self):
        return self.var_attrs

    def add_coord_attrs(self, name):
        return self.coord_attrs.get(name, {})

    def add_level_coord_attrs(self, name, levtype):
        # print("add_level_coord_attrs", name, levtype)
        level_key = self.level_maps.get("key", None)
        if level_key in levtype:
            return self.level_maps.get(levtype[level_key], {})
        else:
            raise ValueError(f"Cannot determine level type for coordinate {name}")

    def rename_dims(self, dims):
        return [self.dim_coord_mapping.get(d, d) for d in dims]

    def rename_coords(self, coords):
        return {self.dim_coord_mapping.get(k, k): v for k, v in coords.items()}

    def adjust_attributes(self, attrs):
        attrs.pop("units", None)
        return attrs

    def remap(self, d):
        def _remap(k):
            return self.attr_mapping.get(k, k)

        return {_remap(k): v for k, v in d.items()}
