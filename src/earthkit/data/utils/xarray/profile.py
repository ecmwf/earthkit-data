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
from abc import ABCMeta
from abc import abstractmethod
from functools import cached_property

from earthkit.data.utils import ensure_dict
from earthkit.data.utils import ensure_iterable

LOG = logging.getLogger(__name__)


GEO_KEYS = ["md5GridSection"]
MANDATORY_KEYS = GEO_KEYS
IGNORE_ATTRS = ["md5GridSection"]


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
        return self._conf[name]

    def _load(self, name):
        with self._lock:
            if name not in self._conf and name != "defaults":
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

    @cached_property
    def defaults(self):
        here = os.path.dirname(__file__)
        path = os.path.join(here, "defaults.yaml")
        if os.path.exists(path):
            import yaml

            try:
                with open(path, "r") as f:
                    return yaml.safe_load(f)
            except Exception as e:
                LOG.exception(f"Failed read profile defaults file {path}. {e}")
                raise
        else:
            raise ValueError(f"Profile defaults not found! path={path}")


PROFILE_CONF = ProfileConf()


class ProfileVariable(metaclass=ABCMeta):
    key = None

    @property
    @abstractmethod
    def is_mono(self):
        pass

    @abstractmethod
    def update(self, ds):
        """
        Parameters
        ----------
        ds: fieldlist
            FieldList object with cached metadata
        """
        pass

    @abstractmethod
    def check(self, profile):
        """
        Check the variable against the profile.
        This is called after the variable has been updated.
        """
        pass


class KeyVariable(ProfileVariable):
    def __init__(self, key, drop, rename_map):
        self.key = key
        self.drop = drop
        self.rename_map = rename_map
        self.variables = []

    @property
    def is_mono(self):
        return False

    def rename(self, v):
        """
        Rename the variable using the rename map.
        If the variable is not in the rename map, return the original name.
        """
        return self.rename_map.get(v, v)

    def update(self, ds):
        """
        Parameters
        ----------
        ds: fieldlist
            FieldList object with cached metadata
        """

        self.variables = ds.index(self.key)

        if self.drop:
            self.variables = [v for v in self.variables if v not in self.drop]

        if not self.variables:
            raise ValueError(f"No metadata values found for variable key {self.key}")

    def check(self, profile):
        assert self.key not in profile.dim_keys
        assert self.key is not None
        assert self.variables
        assert self.key not in profile.dim_keys


class MonoVariable(ProfileVariable):
    def __init__(self, name=None):
        self.name = name or "data"

    @property
    def is_mono(self):
        return True

    def rename(self, v):
        """
        Rename the variable using the rename map.
        If the variable is not in the rename map, return the original name.
        """
        return v

    def update(self, ds):
        """
        Parameters
        ----------
        ds: fieldlist
            FieldList object with cached metadata
        """
        # MonoVariable does not have a key, so no update needed
        pass

    def check(self, profile):
        pass


class Profile:
    USER_ONLY_OPTIONS = ["remapping", "patches", "fill_metadata"]
    DEFAULT_PROFILE_NAME = "mars"

    def __init__(
        self,
        name=None,
        **kwargs,
    ):
        from .attrs import Attrs
        from .dim import DimHandler

        self._kwargs = dict(**kwargs)
        self.name = name
        self.index_keys = []

        patches = dict()

        # defaults
        fill_md = kwargs.pop("fill_metadata", None)
        if fill_md:
            if not isinstance(fill_md, dict):
                raise ValueError("fill_metadata must be a dict!")
            for k, v in fill_md.items():
                if isinstance(v, (str, int, float, bool)):
                    patches[k] = lambda x: x if x is not None else v
                elif isinstance(v, dict) or callable(v):
                    patches[k] = v

        self.remapping = RemappingBuilder(kwargs.pop("remapping", None), patches)

        # variables
        mono_variable = kwargs.pop("mono_variable")
        variable_key = kwargs.pop("variable_key")
        drop_variables = kwargs.pop("drop_variables")
        rename_variables_map = kwargs.pop("rename_variables")
        if mono_variable:
            mono_variable_name = None
            if isinstance(mono_variable, str):
                mono_variable_name = mono_variable
            self.variable = MonoVariable(name=mono_variable_name)
        else:
            if variable_key:
                self.variable = KeyVariable(variable_key, drop_variables, rename_variables_map)
                self.add_keys([self.variable.key])
            else:
                raise ValueError("variable_key must be a non-empty str!")

        # dims
        self.dims = DimHandler(
            self,
            kwargs.pop("extra_dims"),
            kwargs.pop("drop_dims"),
            kwargs.pop("ensure_dims"),
            kwargs.pop("fixed_dims"),
            kwargs.pop("split_dims"),
            kwargs.pop("rename_dims"),
            kwargs.pop("dim_roles"),
            kwargs.pop("dim_name_from_role_name"),
            kwargs.pop("dims_as_attrs"),
            kwargs.pop("time_dim_mode"),
            kwargs.pop("level_dim_mode"),
            kwargs.pop("squeeze"),
        )

        # coordinates
        self.add_valid_time_coord = kwargs.pop("add_valid_time_coord")
        self.add_geo_coords = kwargs.pop("add_geo_coords")

        # attributes
        self.attrs = Attrs(
            self,
            kwargs.pop("attrs_mode"),
            kwargs.pop("attrs"),
            kwargs.pop("variable_attrs"),
            kwargs.pop("global_attrs"),
            kwargs.pop("coord_attrs"),
            kwargs.pop("rename_attrs"),
        )

        self.add_earthkit_attrs = kwargs.pop("add_earthkit_attrs")

        # generic
        self.decode_times = kwargs.pop("decode_times")
        self.decode_timedelta = kwargs.pop("decode_timedelta")
        self.lazy_load = kwargs.pop("lazy_load")
        self.release_source = kwargs.pop("release_source")
        self.direct_backend = kwargs.pop("direct_backend")
        self.strict = kwargs.pop("strict")
        self.errors = kwargs.pop("errors")

        # values
        self.flatten_values = kwargs.pop("flatten_values")
        self.dtype = kwargs.pop("dtype")
        self.array_backend = kwargs.pop("array_backend")

        if "array_module" in kwargs:
            raise ValueError(
                "'array_module' is deprecated. Use 'array_backend' instead. "
                "If you are using 'array_module', please update your code to use 'array_backend'."
            )

        # if self.array_backend == "numpy":
        #     import numpy as np

        #     self.array_module = np

        if kwargs:
            raise ValueError(f"Unsupported options: {kwargs}")

        self.add_keys(ensure_iterable(MANDATORY_KEYS))

        self.prepend_keys(self.dims.split_dims)

        # print("INIT variable key", self.variable_key)
        # print("INIT index_keys", self.index_keys)
        # print("INIT dim_keys", self.dim_keys)

    @staticmethod
    def make(name_or_def, *args, force=False, **kwargs):
        # print("name_or_def", name_or_def)

        if isinstance(name_or_def, Profile):
            if force:
                return name_or_def.copy()
            else:
                return name_or_def

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
        import copy

        kwargs = copy.deepcopy(kwargs)
        opt = copy.deepcopy(PROFILE_CONF.defaults)

        def _deprec_array_module(data):
            """Deprecated: use 'array_backend' instead"""
            if "array_module" in data:
                import warnings

                warnings.warn("'array_module' is deprecated. Use 'array_backend' instead", DeprecationWarning)

                array_module = kwargs.pop("array_module")
                if data.get("array_backend", None) is None:
                    data["array_backend"] = array_module

        _deprec_array_module(kwargs)

        for d in [conf, kwargs]:
            for k, v in d.items():
                if k in PROFILE_CONF.defaults and v is not None:
                    if isinstance(PROFILE_CONF.defaults[k], dict):
                        if not isinstance(v, dict):
                            raise ValueError(f"Expected dict for key {k} in profile {name}")
                        if "__overwrite__" in v:
                            v.pop("__overwrite__")
                            opt[k] = v
                        else:
                            opt[k].update(v)
                    elif isinstance(PROFILE_CONF.defaults[k], list):
                        opt[k] = ensure_iterable(v)
                    else:
                        opt[k] = v
                elif k not in PROFILE_CONF.defaults:
                    if k in cls.USER_ONLY_OPTIONS:
                        opt[k] = v
                    else:
                        raise ValueError(f"Unknown key {k} in profile {name}")

        def _check_type(k, v, t):
            if isinstance(PROFILE_CONF.defaults[k], t):
                if not isinstance(v, t):
                    raise ValueError(f"Expected {t.__name__} for key {k} in profile {name}")
                return True

        for k, v in opt.items():
            if k in PROFILE_CONF.defaults:
                any(_check_type(k, v, t) for t in [dict, list, bool])

        if opt["decode_timedelta"] is None:
            opt["decode_timedelta"] = opt["decode_times"]

        return cls(*args, name=name, **opt)

    @classmethod
    def to_docs(cls, name):
        """Used to generate documentation"""
        import copy

        if name is None:
            conf = {}
        else:
            conf = PROFILE_CONF.get(name)

        opt = copy.deepcopy(PROFILE_CONF.defaults)

        for k, v in conf.items():
            if k in PROFILE_CONF.defaults and v is not None:
                if isinstance(PROFILE_CONF.defaults[k], dict):
                    if not isinstance(v, dict):
                        raise ValueError(f"Expected dict for key {k} in profile {name}")
                    if "__overwrite__" in v:
                        v.pop("__overwrite__")
                        opt[k] = v
                    else:
                        opt[k].update(v)
                elif isinstance(PROFILE_CONF.defaults[k], list):
                    opt[k] = ensure_iterable(v)
                else:
                    opt[k] = v
            elif k not in PROFILE_CONF.defaults:
                if k in cls.USER_ONLY_OPTIONS:
                    opt[k] = v
                else:
                    raise ValueError(f"Unknown key {k} in profile {name}")

        return opt

    def copy(self):
        return Profile(name=self.name, **self._kwargs)

    @property
    def dim_keys(self):
        return self.dims.active_dim_keys

    def add_keys(self, keys):
        self.index_keys += [key for key in keys if key not in self.index_keys]

    def prepend_keys(self, keys):
        if keys:
            self.index_keys = keys + [k for k in self.index_keys if k not in keys]

    # def update_variables(self, ds):
    #     if not self.mono:
    #         self.variables = ds.index(self.variable_key)

    #         if self.drop_variables:
    #             self.variables = [v for v in self.variables if v not in self.drop_variables]

    #         if not self.variables:
    #             raise ValueError(f"No metadata values found for variable key {self.variable_key}")

    def update(self, ds):
        """
        Parameters
        ----------
        ds: fieldlist
            FieldList object with cached metadata
        attributes: dict
            Index keys which has a single (valid) value
        """
        # print("index_keys", self.index_keys)
        # print("dim_keys", self.dim_keys)
        self.variable.update(ds)
        self.dims.update(ds)
        self.variable.check(self)

        # if not self.mono:
        #     self.variables = ds.index(self.variable_key)

        #     if self.drop_variables:
        #         self.variables = [v for v in self.variables if v not in self.drop_variables]

        #     if not self.variables:
        #         raise ValueError(f"No metadata values found for variable key {self.variable_key}")

        #     # variable_keys = VARIABLE_KEYS + [self.variable_key]
        #     # self.dims.remove(variable_keys, others=True)
        #     self.dims.update(ds)
        #     assert self.variable_key not in self.dim_keys

        #     assert self.variable_key is not None
        #     assert self.variables
        #     assert self.variable_key not in self.dim_keys
        # else:
        #     self.dims.update(ds)

        # print("UPDATE variable_key", self.variable_key)
        # print("UPDATE variables", self.variables)
        # print(" -> dim_keys", self.dim_keys)

    @property
    def sort_keys(self):
        if self.variable.key:
            keys = self.dims.split_dims + [self.variable.key]
        else:
            keys = self.dims.split_dims
        keys += [k for k in self.dim_keys if k not in keys]
        return keys

    def rename_dims_map(self):
        return self.dims.rename_dims_map

    # def rename_variable(self, v):
    #     return self.variable.rename_map.get(v, v)

    def rename_dataset_dims(self, dataset):
        return self.dims.rename_dataset_dims(dataset)
