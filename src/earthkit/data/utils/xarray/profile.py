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

# CUSTOM_VARIABLE_KEYS = ["param_level"]
# VARIABLE_KEYS = [
#     "param",
#     "variable",
#     "parameter",
#     "shortName",
#     "long_name",
#     "name",
#     "cfName",
#     "cfVarName",
# ] + CUSTOM_VARIABLE_KEYS


# CUSTOM_KEYS = ["valid_datetime", "base_datetime", "level_and_type"]

# DEFAULT_METADATA_KEYS = {
#     "CF": [
#         "shortName",
#         "units",
#         "name",
#         "cfName",
#         "cfVarName",
#         "missingValue",
#         "totalNumber",
#         "numberOfDirections",
#         "numberOfFrequencies",
#         "NV",
#         "gridDefinitionDescription",
#     ]
# }


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
        with self._lock:
            if name not in self._conf:
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
    def __init__(
        self,
        variable_key="param",
        drop_variables=None,
        rename_variables=None,
        extra_dims=None,
        drop_dims=None,
        ensure_dims=None,
        fixed_dims=None,
        split_dims=None,
        rename_dims=None,
        dims_as_attrs=None,
        dim_roles=None,
        time_dim_mode="forecast",
        level_dim_mode="level",
        squeeze=True,
        attrs_mode=None,
        attrs=None,
        variable_attrs=None,
        global_attrs=None,
        coord_attrs=None,
        rename_attrs=None,
        remapping=None,
        add_valid_time_coord=False,
        add_geo_coords=True,
        decode_time=True,
        strict=True,
        level_maps=None,
    ):
        from .attrs import Attrs
        from .dim import Dims

        self.index_keys = []

        patches = dict()
        self.remapping = RemappingBuilder(remapping, patches)

        # variables
        self.variables = []
        self.variable_key = variable_key
        if variable_key is None:
            raise ValueError("variable_key must be set!")

        self.add_keys([self.variable_key])
        self.drop_variables = drop_variables
        self.rename_variables_map = ensure_dict(rename_variables)

        # dims
        self.dims = Dims(
            self,
            extra_dims,
            drop_dims,
            ensure_dims,
            fixed_dims,
            split_dims,
            rename_dims,
            dim_roles,
            dims_as_attrs,
            time_dim_mode,
            level_dim_mode,
            squeeze,
        )

        self.level_maps = ensure_dict(level_maps)

        # coordinates
        self.add_valid_time_coord = add_valid_time_coord
        self.add_geo_coords = add_geo_coords

        # attributes
        self.attrs = Attrs(self, attrs_mode, attrs, variable_attrs, global_attrs, coord_attrs, rename_attrs)

        # generic
        self.decode_time = decode_time
        self.strict = strict

        self.add_keys(ensure_iterable(MANDATORY_KEYS))

        self.prepend_keys(self.dims.split_dims)

        # print("INIT variable key", self.variable_key)
        # print("INIT index_keys", self.index_keys)
        # print("INIT dim_keys", self.dim_keys)

    @staticmethod
    def make(name_or_def, *args, **kwargs):
        if name_or_def is None:
            name_or_def = {}

        if isinstance(name_or_def, str):
            conf = PROFILE_CONF.get(name_or_def)
            name = name_or_def
        elif isinstance(name_or_def, dict):
            conf = name_or_def
            name = ""
        else:
            raise ValueError(f"Unsupported type for name_or_def: {type(name_or_def)}")

        return Profile.from_conf(name, conf, *args, **kwargs)

    @classmethod
    def from_conf(cls, name, conf, *args, **kwargs):
        conf = conf.copy()
        # options = conf.pop("frozen_options", {})

        # if isinstance(options, list):
        #     options = {}

        kwargs = dict(**kwargs)
        # kwargs.update(options)
        conf.update((k, v) for k, v in kwargs.items() if v is not None)
        return cls(*args, **conf)

    @property
    def dim_keys(self):
        return self.dims.active_dim_keys

    def add_keys(self, keys):
        self.index_keys += [key for key in keys if key not in self.index_keys]

    def prepend_keys(self, keys):
        if keys:
            self.index_keys = keys + [k for k in self.index_keys if k not in keys]

    # def guess_variable_key(self):
    #     """If any remapping/compound key contains a param key, the variable key is set
    #     to that key.
    #     """
    #     names = self.dims.deactivate(VARIABLE_KEYS, others=True, collect=True)
    #     if names:
    #         return names[0]

    #     for k in CUSTOM_VARIABLE_KEYS:
    #         if k in self.index_keys:
    #             return k

    #     return VARIABLE_KEYS[0]

    def update_variables(self, ds):
        self.variables = ds.index(self.variable_key)

        if self.drop_variables:
            self.variables = [v for v in self.variables if v not in self.drop_variables]

        if not self.variables:
            raise ValueError(f"No metadata values found for variable key {self.variable_key}")

    def update_dims(self, ds, attributes):
        # variable keys cannot be dimensions
        variable_keys = [self.variable_key]
        # variable_keys = VARIABLE_KEYS + [self.variable_key]
        # self.dims.remove(variable_keys, others=True)
        self.dims.update(ds, attributes, variable_keys)
        assert self.variable_key not in self.dim_keys

    def update(self, ds):
        """
        Parameters
        ----------
        ds: fieldlist
            FieldList object with cached metadata
        attributes: dict
            Index keys which has a single (valid) value
        """
        self.variables = ds.index(self.variable_key)

        if self.drop_variables:
            self.variables = [v for v in self.variables if v not in self.drop_variables]

        if not self.variables:
            raise ValueError(f"No metadata values found for variable key {self.variable_key}")

        # variable_keys = VARIABLE_KEYS + [self.variable_key]
        # self.dims.remove(variable_keys, others=True)
        self.dims.update(ds)
        assert self.variable_key not in self.dim_keys

        # self.update_variables(ds)
        #         self.update_dims(ds, attributes)

        assert self.variable_key is not None
        assert self.variables
        assert self.variable_key not in self.dim_keys

        # print("UPDATE variable_key", self.variable_key)
        # print("UPDATE variables", self.variables)
        # print(" -> dim_keys", self.dim_keys)

    @property
    def sort_keys(self):
        keys = self.dims.split_dims + [self.variable_key]
        keys += [k for k in self.dim_keys if k not in keys]
        return keys

    def var_attributes(self):
        return self.variable_attrs

    def add_coord_attrs(self, name):
        return self.attrs.coord_attrs.get(name, {})

    def add_level_coord_attrs(self, name, levtype):
        # print("add_level_coord_attrs", name, levtype)
        level_key = self.level_maps.get("key", None)
        if level_key in levtype:
            return self.level_maps.get(levtype[level_key], {})
        else:
            return {}
            # raise ValueError(f"Cannot determine level type for coordinate {name}")

    def rename_dims(self, dims):
        return [self.dims.rename_dims_map.get(d, d) for d in dims]

    def rename_coords(self, coords):
        return {self.dims.rename_dims_map.get(k, k): v for k, v in coords.items()}

    def rename_variable(self, v):
        return self.rename_variables_map.get(v, v)
