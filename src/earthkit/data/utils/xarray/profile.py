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

from earthkit.data.utils import ensure_dict
from earthkit.data.utils import ensure_iterable

LOG = logging.getLogger(__name__)


GEO_KEYS = ["md5GridSection"]
MANDATORY_KEYS = GEO_KEYS
IGNORE_ATTRS = ["md5GridSection"]

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


class RemappingBuilder:
    def __init__(self, remappings, patches=None):
        self.remappings = dict(**ensure_dict(remappings))
        self.patches = dict(**ensure_dict(patches))

    def build(self):
        from earthkit.data.core.order import build_remapping

        return build_remapping(self.remappings, patches=self.patches)

    def add(self, remapping, patches=None):
        self.remappings.update(remapping)
        if patches is not None:
            self.patches.update(patches)


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
                        LOG.exception(f"Failed read profile conf {name} from {path}. {e}")
                        raise
                else:
                    raise ValueError(f"Profile {name} not found! path={path}")


PROFILE_CONF = ProfileConf()


class Profile:
    fixed_dim_order = False

    def __init__(
        self,
        vocabulary=None,
        index_keys=None,
        variable_key=None,
        drop_variables=None,
        attrs=None,
        attrs_strategy=None,
        variable_attrs=None,
        extra_variable_attrs=None,
        drop_variable_attrs=None,
        variable_attrs_strategy=None,
        global_attrs=None,
        extra_global_attrs=None,
        drop_global_attrs=None,
        global_attrs_strategy=None,
        predefined_dims=None,
        extra_dims=None,
        drop_dims=None,
        ensure_dims=None,
        fixed_dims=None,
        dims_as_attrs=None,
        squeeze=True,
        remapping=None,
        time_dim_mode="forecast",
        time_dim_mapping=None,
        add_valid_time_coord=False,
        decode_time=True,
        # step_as_timedelta=False,
        level_dim_mode="level",
        coord_attrs=None,
        dim_coord_mapping=None,
        attr_mapping=None,
        level_maps=None,
        merge_pf_and_cf=False,
        attrs_mode=None,
        attrs_mapping=None,
        add_geo_coords=True,
        merge_cf_and_pf=False,
        **kwargs,
    ):

        if kwargs:
            raise ValueError(f"Profile got unsupported arguments: {kwargs}")

        from .dim import Vocabulary

        self.vocabulary = Vocabulary.make(vocabulary)

        self.fixed_dims = ensure_iterable(fixed_dims)
        self.attrs = ensure_iterable(attrs)
        self.variable_attrs = ensure_iterable(variable_attrs)
        self.attr_mapping = ensure_dict(attr_mapping)
        self.dim_coord_mapping = ensure_dict(dim_coord_mapping)
        self.global_attrs = ensure_dict(global_attrs)
        self.coord_attrs = ensure_dict(coord_attrs)
        self.level_maps = ensure_dict(level_maps)
        self.squeeze = squeeze
        self.time_dim_mode = time_dim_mode
        self.time_dim_mapping = ensure_dict(time_dim_mapping)
        self.decode_time = decode_time
        # self.add_valid_time_dim = add_valid_time_dim
        # self.add_forecast_ref_time_dim = add_forecast_ref_time_dim
        self.add_valid_time_coord = add_valid_time_coord
        # self.step_as_timedelta = step_as_timedelta
        self.level_dim_mode = level_dim_mode
        # self.add_level_and_type_dim = add_level_and_type_dim
        # self.add_level_per_type_dim = add_level_per_type_dim
        self.add_geo_coords = add_geo_coords
        self.variable_key = variable_key

        self.global_attrs = ensure_dict(global_attrs)
        self.extra_global_attrs = ensure_dict(extra_global_attrs)
        self.drop_global_attrs = ensure_iterable(drop_global_attrs)
        self.global_attrs_strategy = global_attrs_strategy
        self.predefined_dims = ensure_iterable(predefined_dims)
        self.extra_dims = ensure_iterable(extra_dims)
        self.drop_dims = ensure_iterable(drop_dims)
        self.ensure_dims = ensure_iterable(ensure_dims)
        self.dims_as_attrs = ensure_iterable(dims_as_attrs)
        self.merge_cf_and_pf = merge_cf_and_pf

        # if self.add_forecast_ref_time_dim and self.add_valid_time_dim:
        #     raise ValueError("Cannot add both forecast_ref_time and valid_time dims")

        self.index_keys = ensure_iterable(index_keys)
        # self.add_keys(ensure_iterable(MANDATORY_KEYS))
        # self.add_keys(ensure_iterable(extra_dims))
        # print("INIT index_keys", self.index_keys)
        # if variable_key is not None:
        #     self.add_keys([variable_key])

        patches = dict()
        if self.merge_cf_and_pf:
            patches = {"type": {"cf": "pf"}, "number": {None: 0}}
        self.remapping = RemappingBuilder(remapping, patches)

        self.variables = []
        self.variable_key = variable_key
        if variable_key is None:
            raise ValueError("variable_key must be set!")
        self.add_keys([self.variable_key])

        # self.frozen_variable_key = variable_key is not None
        # self.variable_key = variable_key if self.frozen_variable_key else self.guess_variable_key()
        # if self.variable_key is not None:
        #     self.add_keys([self.variable_key])

        from .attrs import GlobalAttrs
        from .dim import Dims

        # print("INIT index_keys", self.index_keys)
        self.dims = Dims(self)
        self.g_attrs = GlobalAttrs(self)

        self.add_keys(ensure_iterable(MANDATORY_KEYS))
        self.add_keys(self.attrs)
        self.add_keys(self.variable_attrs)
        self.add_keys(self.global_attrs)

        # print("INIT dim_keys", self.dim_keys)
        self.drop_variables = drop_variables

        # print("INIT variable key", self.variable_key)
        # print("INIT index_keys", self.index_keys)
        # print("INIT dim_keys", self.dim_keys)

    @staticmethod
    def make(name, *args, **kwargs):
        conf = PROFILE_CONF.get(name)
        return Profile.from_conf(name, conf, *args, **kwargs)

    @classmethod
    def from_conf(cls, name, conf, *args, **kwargs):
        conf = conf.copy()
        options = conf.pop("frozen_options", {})

        if isinstance(options, list):
            options = {}

        # for k, v in kwargs.items():
        #     if v is not None and k in conf and conf[k] != v:
        #         raise ValueError(f"Cannot specify {k} as a kwarg. It is a frozen option in profile={name}")

        kwargs = dict(**kwargs)
        # print("kwargs", kwargs)
        # print("options", options)
        kwargs.update(options)
        conf.update((k, v) for k, v in kwargs.items() if v is not None)
        return cls(*args, **conf)

    def make_dims(self):
        return self.dims.make_dims()

    @property
    def dim_keys(self):
        return self.dims.active_dim_keys

    def add_keys(self, keys):
        self.index_keys += [key for key in keys if key not in self.index_keys]

    def guess_variable_key(self):
        """If any remapping/compound key contains a param key, the variable key is set
        to that key.
        """
        names = self.dims.deactivate(VARIABLE_KEYS, others=True, collect=True)
        if names:
            return names[0]

        for k in CUSTOM_VARIABLE_KEYS:
            if k in self.index_keys:
                return k

        return VARIABLE_KEYS[0]

    def update_variables(self, ds):
        self.variables = ds.index(self.variable_key)

        # if not self.frozen_variable_key and self.variable_key in VARIABLE_KEYS:
        #     # try to find a valid variable out of the predefined variable keys
        #     if not self.variables:
        #         for k in VARIABLE_KEYS:
        #             if k != self.variable_key:
        #                 self.variables = ds.index(k)
        #                 if self.variables:
        #                     self.variable_key = k
        #                     break
        # else:
        if self.drop_variables:
            self.variables = [v for v in self.variables if v not in self.drop_variables]

        if not self.variables:
            raise ValueError(f"No metadata values found for variable key {self.variable_key}")

    def update_dims(self, ds, attributes):
        # variable keys cannot be dimensions
        variable_keys = VARIABLE_KEYS + [self.variable_key]
        self.dims.remove(variable_keys, others=True)
        self.dims.update(ds, attributes, variable_keys)
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
        self.update_variables(ds)
        self.update_dims(ds, attributes)

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
        return self.global_attrs

    def var_attributes(self):
        return self.variable_attrs

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

    def collect_coords(self, tensor):
        return self.dims.as_coord(tensor)
