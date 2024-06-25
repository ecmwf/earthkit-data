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
from collections import defaultdict
from itertools import product

import numpy
import xarray
import xarray.core.indexing as indexing
from xarray.backends import BackendEntrypoint

from earthkit.data import FieldList
from earthkit.data import from_object
from earthkit.data import from_source

# from earthkit.data.readers.netcdf import get_fields_from_ds
from earthkit.data.core import Base
from earthkit.data.core.order import build_remapping
from earthkit.data.indexing.fieldlist import FieldArray
from earthkit.data.indexing.tensor import FieldListTensor
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
        # if self.name not in self.group:
        #     self.group = [self.name] + self.group

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
        if self.name in ds.indices():
            print(f"-> {self.name} active={self.active} ds={ds.index(self.name)}")

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
                print(f"-> {self.name} found in ds")
                self.deactivate_related()
                # for d in self.profile.dims:
                #     if d != self and any(g in d for g in self.group):
                #         d.active = False
                # self.profile._remove_dim_keys(set(self.group) - {self.name})
                # print(f" dims: {self.profile.dim_keys}")
                # return
            # else:
            #     print(f"-> {self.name} not found in ds")
            #     for k in self.group:
            #         if k in ds.indices() and k not in attributes:
            #             self._replace_dim(self.name, k)
            #             self.name = k
            #             self.profile._remove_dim_keys(set(self.group) - {self.name})
            #             return
            else:
                self.active = False
                self.deactivate_related()
        else:
            if self.name in ds.indices() and len(ds.index(self.name)) >= 1:
                print(f"-> {self.name} found in ds")
                self.deactivate_related()
            else:
                self.active = False
                self.deactivate_related()

    def deactivate_related(self):
        for d in self.profile.dims:
            if d.active and d != self:
                if any(g in d for g in self.all_dims):
                    print(f"deactivate name={self.name} d={d.name} self.group={self.all_dims}")
                    d.active = False
                if d.active and self.same(d):
                    d.active = False


# class ParamDim(Dim):
#     name = "param"
#     group = ["variable", "shortName", "long_name", "name", "cfName", "cfVarName"]


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


class Coords:
    def __init__(
        self,
        grid,
        add_valid_datetime_coord=False,
        add_geo_coords=True,
        use_timedelta_step=False,
        use_level_per_type=False,
    ):
        self._user_coords = {}
        if add_geo_coords:
            self._field_coords = self._from_grid(grid)
        else:
            self._field_coords = {}
        self.add_valid_datetime_coord = add_valid_datetime_coord
        self.use_timedelta_step = use_timedelta_step
        self._step_converted = False
        self.use_level_per_type = use_level_per_type
        self.dims = []

    @property
    def coords(self):
        r = {k: v for k, v in self._user_coords.items()}
        r.update(self._field_coords)
        return r

    def collect(self, tensor):
        if not self._user_coords:
            self._user_coords = {k: (k, v) for k, v in tensor.user_coords.items()}
        else:
            for k, v in tensor.user_coords.items():
                if k not in self._user_coords:
                    self._user_coords[k] = (k, v)

        if self.use_level_per_type:
            self._user_coords.pop("level", None)
            if "level" in tensor.user_dims:
                lev_type = tensor.source[0].metadata("levtype")
                # print("->lev_type", lev_type)
                if not lev_type:
                    raise ValueError("levtype not found in metadata")
                if lev_type not in self._user_coords:
                    self._user_coords[lev_type] = (
                        lev_type,
                        list(tensor.user_coords["level"]),
                    )

        if (
            self.add_valid_datetime_coord
            and "valid_datetime" not in tensor.user_dims
            and "valid_datetime" not in self._user_coords
        ):
            _dims, _vals = tensor.make_valid_datetime()
            if _dims is None or _vals is None:
                raise ValueError("valid_datetime coord could not be created")
            self._user_coords["valid_datetime"] = xarray.Variable(_dims, _vals)

        self._convert_step()

        self.dims = []
        self._dims(tensor)

    def _dims(self, tensor):
        self.dims = list(tensor.full_dims.keys())
        if self.use_level_per_type:
            if "level" in self.dims:
                lev_type = tensor.source[0].metadata("levtype")
                if lev_type in self._user_coords:
                    idx = self.dims.index("level")
                    self.dims[idx] = lev_type

    def _convert_step(self):
        if self.use_timedelta_step and not self._step_converted and "step" in self._user_coords:
            from earthkit.data.utils.dates import step_to_delta

            d, v = self._user_coords["step"]
            self._user_coords["step"] = (d, [step_to_delta(x) for x in v])
            self._step_converted = True

    def _from_grid(self, grid):
        r = {}
        if len(grid.dims) == 2:
            if len(grid.coords) == 2:
                if all(x in grid.dims for x in grid.coords.keys()):
                    for k, v in grid.coords.items():
                        print(f"grid coord: {k} grid_dims: {k}:{grid.dims[k]} shape: {v.shape}")
                        r[k] = xarray.Variable({k: grid.dims[k]}, v)
                else:
                    for k, v in grid.coords.items():
                        print(f"grid coord: {k} grid_dims: {grid.dims} shape: {v.shape}")
                        r[k] = xarray.Variable(grid.dims, v)

            # if len(grid.coords) == 2:
            #     for k, v in grid.coords.items():
            #         print(f"grid coord: {k} grid_dims: {grid.dims} shape: {v.shape}")
            #         r[k] = xarray.Variable(grid.dims, v)
            else:
                raise ValueError(
                    (
                        f"Invalid number of grid coordinates {len(grid.coords)}=1 found. When"
                        " the number of grid dimensions=2 there must 2 grid coordinates."
                        f"grid coordinates keys = {grid.coords.keys}"
                    )
                )
        elif len(grid.dims) == 1:
            dim_name = next(iter(grid.dims))
            for k, v in grid.coords.items():
                dim_name = next(iter(grid.dims))
                if k not in self._user_coords:
                    r[k] = (dim_name, v)
        else:
            raise ValueError(f"Unsupported grid dims {grid.dims}")
        # if len(grid.coords) == 2 and len(grid.dims) == 2:
        #     for k, v in grid.coords.items():
        #         # r[k] = (k, v)
        #         r[k] = xarray.Variable(grid.dims, v)

        # if len(grid.coords) == len(grid.dims):
        #     for k, v in grid.coords.items():
        #         # r[k] = (k, v)
        #         r[k] = xarray.Variable(grid.dims, v)
        # else:
        #     for k, v in grid.coords.items():
        #         dim_name = next(iter(grid.dims))
        #         if k not in self._user_coords:
        #             r[k] = (dim_name, v)
        return r


class Grid:
    def __init__(self, ds, flatten_values=False):
        grids = ds.index("md5GridSection")
        if len(grids) != 1:
            raise ValueError(f"Expected one grid, got {len(grids)}")

        first = ds[0]
        self.dims, self.coords = FieldListTensor._field_part(first, flatten_values)
        # print(f"grid dims: {self.dims}")
        # print(f"grid coords: {self.coords.keys()}")


class ProfileConf:
    def __init__(self):
        self._conf = None
        self._lock = threading.Lock()

    def get(self, name):
        if name not in self._conf:
            self._load(name)
        return self._conf[name]

    def _load(self, name):
        """Load the available backend objects"""
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
    def __init__(
        self,
        index_keys=None,
        mandatory_keys=None,
        variable_key=None,
        dims=None,
        squeeze=True,
        extra_index_keys=None,
        remapping=None,
        drop_variables=None,
        use_valid_datetime=False,
        use_base_datetime=False,
        add_level_type=False,
        add_valid_datetime_coord=False,
        use_level_per_type_dim=False,
    ):
        self.squeeze = squeeze
        self.index_keys = [] if index_keys is None else list(index_keys)

        print("INIT index_keys", self.index_keys)
        mandatory_keys = [] if mandatory_keys is None else list(mandatory_keys)
        self.add_keys(mandatory_keys)
        print("INIT index_keys", self.index_keys)

        print("INIT extra_index_keys", extra_index_keys)
        extra_index_keys = [] if extra_index_keys is None else ensure_iterable(extra_index_keys)

        self.add_keys(ensure_iterable(extra_index_keys))
        print("INIT index_keys", self.index_keys)
        if variable_key is not None:
            self.add_keys([variable_key])

        self.dims = []

        print("INIT index_keys", self.index_keys)

        remapping = build_remapping(remapping)
        print(f"{remapping=}")
        if remapping:
            for k in remapping.lists:
                d = RemappingDim(self, k, remapping.lists[k])
                self.dims.append(d)

            #     if k in self.index_keys:
            #         self.index_keys.remove(k)
            # for k in self.index_keys:
            #     if k in remapping.lists:
            #         d = RemappingDim(self, k, remapping.lists[k])
            #         self.dims.append(d)

        for k in self.index_keys:
            if not remapping or k not in remapping.lists:
                ck = CompoundKey.make(k)
                if ck is not None:
                    d = CompoundKeyDim(self, ck)
                    print("CompoundKeyDim", ck.name, ck.keys)
                    self.dims.append(d)

        if use_valid_datetime:
            self.dims.append(ValidDatetimeDim(self))
        elif use_base_datetime:
            self.dims.append(BaseDatetimeDim(self))
            self.dims.append(StepDim(self))
            if add_valid_datetime_coord:
                self.add_keys(["valid_datetime"])
        else:
            self.dims.extend([DateDim(self), TimeDim(self), StepDim(self)])

        self.use_level_per_type_dim = use_level_per_type_dim
        if use_level_per_type_dim:
            self.dims.append(LevelPerTypeDim(self))
        # elif "level_and_type" in self.index_keys:
        #     self.dims.append(LevelAndTypeDim(self))
        else:
            self.dims.append(LevelDim(self))

        self.dims.append(NumberDim(self))

        print("INIT dim_keys", self.dim_keys)
        self.drop_variables = drop_variables

        # for k in self.index_keys:
        #     if not any(k in d for d in self.dims):
        #         self.dims.append(OtherDim(self, k))

        # self.drop_variables = drop_variables

        # for k in self.remapping.lists:
        #     self.add_keys([k])

        # # self.dim_keys = list(self.index_keys)
        # self.managed_dims = {}
        # if use_valid_datetime:
        #     self.managed_dims["datetime"] = ValidDatetimeDim(self)
        # elif use_base_datetime:
        #     self.managed_dims["datetime"] = BaseDatetimeDim(self)
        #     self.managed_dims["step"] = StepDim(self)
        #     if add_valid_datetime_coord:
        #         self.add_keys(["valid_datetime"])
        # else:
        #     self.managed_dims["date"] = DateDim(self)
        #     self.managed_dims["time"] = TimeDim(self)
        #     self.managed_dims["step"] = StepDim(self)

        # self.use_level_per_type_dim = use_level_per_type_dim
        # if use_level_per_type_dim:
        #     self.managed_dims["level"] = LevelPerTypeDim(self)
        # elif "level_and_type" in self.index_keys:
        #     self.managed_dims["level"] = LevelAndTypeDim(self)
        # else:
        #     self.managed_dims["level"] = LevelDim(self)

        # self.managed_dims["number"] = NumberDim(self)

        self.variables = []
        if variable_key is not None:
            self.user_variable_key = True
            self.variable_key = variable_key
        else:
            self.user_variable_key = False
            self.variable_key = self.guess_variable_key()

        print("INIT variable key", self.variable_key)
        print("INIT index_keys", self.index_keys)
        print("INIT dim_keys", self.dim_keys)

    @staticmethod
    def make(name):
        return MarsProfile
        # conf = PROFILE_CONF.get(name)
        # return IndexProfile.from_conf(conf)

    @classmethod
    def from_conf(cls, conf):
        self = cls()
        self.index_keys = conf["index_keys"]
        self.mandatory_keys = conf.get("mandatory_keys", [])
        self.groups = conf.get("groups", {})

        for k in self.mandatory_keys:
            if k not in self.index_keys:
                self.index_keys.append(k)

        return self

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
                print(f"GUESS deactivate dim={d.name} keys={d.drop}")
                assert d.name in self.index_keys
                d.active = False
                d.deactivate_related()
                return d.name

        for k in CUSTOM_VARIABLE_KEYS:
            if k in self.index_keys:
                return k

        return VARIABLE_KEYS[0]

    def adjust_dims_to_remapping(self):
        if self.remapping:
            for k, v in self.remapping.lists.items():
                for _, d in self.managed_dims.items():
                    if k in d or any(p in d for p in v):
                        d.remove()

                # if k in self.dim_keys:
                #     for rk in v:
                #         group = self._key_group(rk)
                #         for key in group:
                #             if key in self.dim_keys:
                #
                #

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
        print("UPDATE dim_keys[0]", self.dim_keys)
        var_keys = VARIABLE_KEYS + [self.variable_key]
        for d in self.dims:
            print(f" d={d.name}")
            if d.active and any(k in d for k in var_keys):
                print("DEACTIVATE dim={d.name} keys={d.group}")
                d.active = False
                d.deactivate_related()

        print("UPDATE dim_keys[0a]", self.dim_keys)

        for d in self.dims:
            d.update(ds, attributes, self.squeeze)
        print("UPDATE dim_keys[0b]", self.dim_keys)

        if self.use_level_per_type_dim:
            for x in ds.index("levtype"):
                self.dims.append(LevelPerTypeDim(self))

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

        print("UPDATE dim_keys[1]", self.dim_keys)

        # self.dim_keys = [
        #     key
        #     for key in self.dim_keys
        #     if key in self.managed_dims
        #     or (key in ds.indices() and key not in attributes)
        # ]

        # for ck in self.compound_keys:
        #     self._remove_dim_keys.remove(ck.keys)

        print("UPDATE dim_keys[2]", self.dim_keys)

        # assert self.dim_keys
        assert self.variable_key not in self.dim_keys
        print(" -> dim_keys", self.dim_keys)

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

        print("UPDATE variable_key", self.variable_key)
        print("UPDATE variables", self.variables)
        print(" -> dim_keys", self.dim_keys)

    @property
    def sort_keys(self):
        return [self.variable_key] + self.dim_keys


class MarsProfile(IndexProfile):
    def __init__(self, *args, **kwargs):
        super().__init__(
            *args,
            index_keys=MARS_GRIB_KEYS_NAMES,
            mandatory_keys=GEO_KEYS,
            **kwargs,
        )


class WrappedFieldList(FieldArray):
    def __init__(self, fieldlist, keys, db=None, fields=None, remapping={}):
        super().__init__()
        self.ds = fieldlist
        self.keys = keys
        self.db = db if db is not None else []

        self.remapping = build_remapping(remapping)
        # print(f"remapping vals: {self.remapping.lists}")
        if fields is not None:
            self.fields = fields
        else:
            self._parse()

    def _parse(self):
        indices = defaultdict(set)
        for i, f in enumerate(self.ds):
            r = f._attributes(self.keys, remapping=self.remapping)
            self.db.append(r)
            self.append(WrappedField(None, r, self.ds, i))

            for k, v in r.items():
                if v is not None:
                    indices[k].add(v)

        self._md_indices = {k: sorted(list(v)) for k, v in indices.items()}

    def common_attributes(self, keys):
        if self.db:
            return {
                k: v
                for k, v in self.db[0].items()
                if k in keys and all([d[k] is not None and v == d[k] for d in self.db])
            }

    def common_attributes_other(self, ds, keys):
        common_entries = dict()
        for f in ds:
            if not common_entries:
                common_entries = {k: f.metadata(k) for k in keys}
            else:
                d = f.metadata(list(common_entries.keys()))
                common_entries = {
                    key: value
                    for i, (key, value) in enumerate(common_entries.items())
                    if d[i] is not None and value == d[i]
                }

        return common_entries

    # def unique_values(self, *coords, remapping={}):
    #     print(f"unique_values: {coords}")
    #     assert all(c in self._md_indices for c in coords)
    #     return {k: tuple(self._md_indices[k]) for k in coords}

    # def sel(self, *args, **kwargs):
    #     r = super().sel(*args, **kwargs)
    #     assert r._index is self
    #     _indices = r._indices
    #     fields = [f for f in r]
    #     db = [self.db[i] for i in _indices]
    #     return self.__class__(self.ds, self.keys, db, fields)

    # def append(self, field):
    #     self.fields.append(field)

    # def _getitem(self, n):
    #     return self.fields[n]

    # def __len__(self):
    #     return len(self.fields)

    # def __repr__(self) -> str:
    #     return f"FieldArray({len(self.fields)})"


# def flatten_arg(func):
#     @functools.wraps(func)
#     def wrapped(self, *args, **kwargs):
#         _kwargs = {**kwargs}
#         _kwargs["flatten"] = len(self.field_shape) == 1
#         return func(self, *args, **_kwargs)

#     return w


class WrappedField:
    def __init__(self, field, metadata, ds, idx):
        self._field = field
        self._meta = metadata
        self._ds = ds
        self._idx = idx

    @property
    def field(self):
        if self._field is None:
            self._field = self._ds[self._idx]
        return self._field

    def unload(self):
        self._field = None

    def clear_meta(self):
        self._meta = {}

    def _keys(self, *args):
        key = []
        key_arg_type = None
        if len(args) == 1 and isinstance(args[0], str):
            key_arg_type = str
        elif len(args) >= 1:
            key_arg_type = tuple
            for k in args:
                if isinstance(k, list):
                    key_arg_type = list
                    break

        for k in args:
            if isinstance(k, str):
                key.append(k)
            elif isinstance(k, (list, tuple)):
                key.extend(k)
            else:
                raise ValueError(f"metadata: invalid key argument={k}")

        return key, key_arg_type

    def metadata(self, *keys, **kwargs):
        if not keys:
            return self.field.metadata(*keys, **kwargs)

        _k, key_arg_type = self._keys(*keys)
        assert isinstance(_k, list)
        if all(k in self._meta for k in _k):
            r = []
            for k in _k:
                r.append(self._meta[k])
            if key_arg_type is str:
                return r[0]
            elif key_arg_type is tuple:
                return tuple(r)
            else:
                return r

        # print(f"Key={_k} not found in local metadata")
        r = self.field.metadata(*keys, **kwargs)
        self.unload()
        return r

    def __getattr__(self, name):
        return getattr(self.field, name)

    def to_numpy(self, *args, **kwargs):
        v = self.field.to_numpy(*args, **kwargs)
        self.unload()
        return v


def get_metadata_keys(tag, metadata):
    if tag == "describe":
        return metadata.describe_keys()
    elif tag in DEFAULT_METADATA_KEYS:
        return DEFAULT_METADATA_KEYS[tag]
    elif tag == "":
        return []

    raise ValueError(f"Unsupported metadata tag={tag}")


class EarthkitBackendArray(xarray.backends.common.BackendArray):
    def __init__(self, ekds, dims, shape, xp, variable):
        super().__init__()
        self.ekds = ekds
        self.dims = dims
        self.shape = shape
        self.dtype = xp.dtype(xp.float32)
        self.xp = xp
        self._var = variable

    def nbytes(self):
        from math import prod

        return prod(self.shape) * self.dtype.itemsize

    def __getitem__(self, key: xarray.core.indexing.ExplicitIndexer):
        # indexing_support = indexing.IndexingSupport.BASIC
        # raw_key, numpy_indices = indexing.decompose_indexer(
        #     key, self.shape, indexing_support
        # )
        # result = self._raw_indexing_method(raw_key.tuple)
        # if numpy_indices.tuple:
        #     # index the loaded np.ndarray
        #     result = indexing.NdArrayLikeIndexingAdapter(result)[numpy_indices]
        # return result
        return indexing.explicit_indexing_adapter(
            key,
            self.shape,
            indexing.IndexingSupport.BASIC,
            self._raw_indexing_method,
        )
        # bug in xarray here? tries to create a NumpyIndexingAdapter instead of NdArrayLikeIndexingAdapter
        # patched in local copy for now, but could construct this ourself

    def _raw_indexing_method(self, key: tuple):
        # must be threadsafe
        # print("_var", self._var)
        print(f"dims: {self.dims} key: {key} shape: {self.shape}")
        # isels = dict(zip(self.dims, key))
        # r = self.ekds.isel(**isels)
        r = self.ekds[key]

        field_index = r.field_indexes(key)
        result = r.to_numpy(field_index=field_index).squeeze()
        # result = self.ekds.isel(**isels).to_numpy()

        # print("result", result.shape)
        # print(f"Loaded {self.xp.__name__} with shape: {result.shape}")

        # Loading as numpy but then converting. This needs to be changed upstream (eccodes)
        # to load directly into cupy.
        # Maybe some incompatibilities when trying to copy from FFI to cupy directly
        result = self.xp.asarray(result)

        return result


def _get_common_attributes(ds, keys):
    common_entries = {}
    if len(ds) > 0:
        first = ds[0]
        common_entries = {key: first.metadata(key) for key in keys if key in first.metadata()}
        for f in ds[1:]:
            dictionary = f.metadata()
            common_entries = {
                key: value
                for key, value in common_entries.items()
                if key in dictionary and common_entries[key] == dictionary[key]
            }
    return common_entries


class GeoCoord:
    def __init__(self) -> None:
        pass

    # def add(self, key, value):
    #     setattr(self, key, value


class EarthkitBackendEntrypoint(BackendEntrypoint):
    def open_dataset(
        self,
        filename_or_obj,
        source_type="file",
        drop_variables=None,
        dims_order=None,
        extra_index_keys=None,
        array_module=numpy,
        variable_metadata_keys=[],
        variable_key=None,
        basic=True,
        flatten_values=False,
        remapping=None,
        profile="mars",
        use_base_datetime_dim=False,
        use_valid_datetime_dim=False,
        add_valid_datetime_coord=False,
        use_timedelta_step=False,
        use_level_and_type_dim=False,
        use_level_per_type_dim=False,
        add_geo_coords=True,
        merge_cf_and_pf=False,
        squeeze=True,
    ):
        r"""
        dims_order: list, None
            List of dimensions in the order they should be used. When defined
            no other dimensions are used. Might be incompatible with some
            other options.
        squeeze: bool
            Remove dimensions which has one or zero valid values. Default is True.
        variable_key: str, None
            Metadata key to use for defining the xarray dataset variables. It cannot be
            defined as a dimension. When None, the key is automatically determined.
        drop_variables: list, None
            List of variables to drop from the dataset. Default is None.
        extra_index_keys: list, None
            List of additional metadata keys to use as index keys. Only enabled when
            no ``dims_order`` is specified.
        flatten_values: bool
            Flatten the values per field resulting in a single dimension called
            "values" representing a field. Otherwise the field shape is used to form
            the field dimensions. When the fields are defined on an unstructured grid (e.g.
            reduced Gaussian) or are spectral (e.g. spherical harmonics) this option is
            ignored and the field values are always represented by a single "values"
            dimension. Default is False.
        use_base_datetime_dim: bool
            The ``date`` and ``time`` dimensions are combined into a single dimension
            called `base_datetime` with datetime64 values. Default is False.
        use_valid_datetime_dim: bool
            The ``date``, ``time`` and ``step`` dimensions are combined into a single
            dimension called `valid_datetime` with np.datetime64 values. Default is False.
        use_timedelta_step: bool
            Convert the ``step`` dimension to np.timedelta64 values. Default is False.
        add_valid_datetime_coord: bool
            Add a `valid_datetime` coordinate containing np.datetime64 values to the
            dataset. Only used when ``use_valid_datetime_dim`` is False. Default is False.
        add_geo_coords: bool
            Add geographic coordinates to the dataset when field values are represented by
            a single "values" dimension. Default is True.
        remapping: dict, None
            Define new metadata keys for indexing. Default is None.
        use_level_and_type_dim: bool
            Use a single dimension for level and type of level. Cannot be used when
            ``use_level_per_type_dim`` is True. Default is False.
        use_level_per_type_dim: bool
            Use a separate dimension for each level type.  Cannot be used when
            ``use_level_and_type_dim`` is True.  Default is False.
        merge_cf_and_pf: bool
            Treat ENS control forecasts as if they had "type=pf" and "number=0" metadata values.
            Default is False.
        """
        self.drop_variables = drop_variables
        self.dims_order = dims_order
        self.extra_index_keys = extra_index_keys
        self.array_module = array_module
        self.variable_metadata_keys = variable_metadata_keys
        self.variable_key = variable_key
        self.basic = basic
        self.flatten_values = flatten_values
        self.remapping = remapping
        self.profile = profile
        self.squeeze = squeeze
        self.use_base_datetime_dim = use_base_datetime_dim
        self.use_valid_datetime_dim = use_valid_datetime_dim
        self.add_valid_datetime_coord = add_valid_datetime_coord
        self.use_timedelta_step = use_timedelta_step
        self.use_level_and_type_dim = use_level_and_type_dim
        self.use_level_per_type_dim = use_level_per_type_dim
        self.merge_cf_and_pf = merge_cf_and_pf
        self.add_geo_coords = add_geo_coords

        if isinstance(filename_or_obj, Base):
            ekds = filename_or_obj
        elif isinstance(filename_or_obj, str):  # TODO: Add Path? or handle with try statement
            ekds = from_source(source_type, filename_or_obj)
        else:
            ekds = from_object(filename_or_obj)

        return self._create(ekds)

    @classmethod
    def guess_can_open(cls, filename_or_obj):
        return True  # filename_or_obj.endswith(".grib")

    # def guess_can_open(cls, ek_object):
    #     return isinstance(ek_object, Base)

    # class EarthkitObjectBackendEntrypoint(BackendEntrypoint):
    #     def open_dataset(
    #         self,
    #         ekds,
    #         drop_variables=None,
    #         dims_order=None,
    #         array_module=numpy,
    #         variable_metadata_keys="describe",
    #         variable_index=["param", "variable", "shortName"],
    #         basic=True,
    #         flatten_values=False,
    #         remapping=None,
    #         profile="mars",
    #     ):

    def _create(self, ekds):
        # print(f"remapping: {self.remapping}, profile: {self.profile}")

        remapping = build_remapping(self.remapping)

        profile = IndexProfile.make(self.profile)(
            remapping=remapping,
            variable_key=self.variable_key,
            extra_index_keys=self.extra_index_keys,
            drop_variables=self.drop_variables,
            use_valid_datetime=self.use_valid_datetime_dim,
            use_base_datetime=self.use_base_datetime_dim,
            add_valid_datetime_coord=self.add_valid_datetime_coord,
            use_level_per_type_dim=self.use_level_per_type_dim,
            squeeze=self.squeeze,
        )

        # print(f"variable_metadata_keys: {self.variable_metadata_keys}")
        # print(f"profile index_keys={profile.index_keys}")
        # print(f"profile dim_keys={profile.dim_keys}")
        if isinstance(self.variable_metadata_keys, str):
            # get first field
            first = ekds[0]

            self.variable_metadata_keys = get_metadata_keys(self.variable_metadata_keys, first.metadata())

            # release first field
            first = None

        assert isinstance(self.variable_metadata_keys, list)
        profile.add_keys(self.variable_metadata_keys)
        # print(f"profile index_keys={profile.index_keys}")

        # create new fieldlist and ensure all the required metadata is kept in memory
        ds_ori = WrappedFieldList(ekds, profile.index_keys, remapping=remapping)
        # print(f"ds_ori: {ds_ori.indices()}")

        # global attributes are keys which are the same for all the fields
        attributes = {k: v[0] for k, v in ds_ori.indices().items() if len(v) == 1}

        LOG.info(f"{attributes=}")

        if hasattr(ekds, "path"):
            attributes["ekds_source"] = ekds.path

        # attributes["institution"] = "European Centre fot Medium-range Weather Forecasts"

        # print(f"attributes: {attributes}")

        profile.update(ds_ori, attributes)
        ds = ds_ori.order_by(profile.sort_keys)
        dims = profile.dim_keys

        # print(f"sort_keys: {profile.sort_keys}")
        print(f"dims: {dims}")

        if self.basic:
            xr_vars = {}

            grid = Grid(ds, flatten_values=self.flatten_values)
            xr_coords = Coords(
                grid,
                use_timedelta_step=self.use_timedelta_step,
                add_geo_coords=self.add_geo_coords,
                add_valid_datetime_coord=self.add_valid_datetime_coord,
                use_level_per_type=self.use_level_per_type_dim,
            )

            # we assume each variable forms a full cube
            for variable in profile.variables:
                # print(variable)
                ds_var = ds.sel(**{profile.variable_key: variable})

                v_dims = []
                for d in dims:
                    if len(ds_var.index(d)) > 1 or (not self.squeeze and len(ds_var.index(d)) >= 1):
                        v_dims.append(d)

                print(f"v_dims: {v_dims}")

                tensor = ds_var.to_tensor(
                    *v_dims,
                    sort=False,
                    progress_bar=False,
                    field_dims_and_coords=(grid.dims, grid.coords),
                    flatten_values=self.flatten_values,
                )

                # print(f" full_dims={tensor.full_dims}")
                # print(f" full_shape={tensor.full_shape}")

                xr_coords.collect(tensor)
                # xr_dims = list(tensor.full_dims.keys())

                # xr_coords.check_dims(xr_dims, tensor)

                # print(f" {tensor.full_coords.keys()} shape={tensor.full_shape}")
                # print(f" {xr_dims=}")

                backend_array = EarthkitBackendArray(
                    tensor,
                    xr_coords.dims,
                    tensor.full_shape,
                    self.array_module,
                    variable,
                )

                data = indexing.LazilyIndexedArray(backend_array)

                # Get metadata keys which are common for all fields, and not listed in dataset attrs

                kk = [k for k in profile.index_keys if k not in attributes]
                var_attrs = ds_ori.common_attributes_other(ds_var, kk)
                # var_attrs = {}

                # var_attrs = _get_common_attributes(
                #     ek_variable.source,
                #     [k for k in variable_metadata_keys if k not in attributes],
                # )

                # print(f"var_attrs: {var_attrs}")

                if hasattr(ds_var[0], "_offset") and hasattr(ekds, "path"):
                    var_attrs["metadata"] = (
                        "grib_handle",
                        ekds.path,
                        ds_var[0]._offset,
                    )
                else:
                    var_attrs["metadata"] = ("id", id(ds_var[0].metadata()))

                # print(f" -> var_attrs: {var_attrs}")

                # Corentin method:
                # var_attrs["metadata"] = ekds_variable[0].metadata()
                print("DIMS=", xr_coords.dims)
                var = xarray.Variable(xr_coords.dims, data, attrs=var_attrs)
                xr_vars[variable] = var

            print(f"xr_coords: {xr_coords.coords.keys()}")

            dataset = xarray.Dataset(xr_vars, coords=xr_coords.coords, attrs=attributes)
            return dataset

    # @classmethod
    # def guess_can_open(cls, ek_object):
    #     return isinstance(ek_object, Base)


# class EarthkitBackendEntrypoint(EarthkitObjectBackendEntrypoint):
#     def open_dataset(
#         self,
#         filename_or_obj_or_request,
#         source_type="file",
#         drop_variables=None,
#         dims_order=None,
#         array_module=numpy,
#         variable_metadata_keys=[],
#         variable_index=["param", "variable", "shortName"],
#         basic=True,
#         flatten_values=False,
#         remapping=None,
#         profile="mars",
#     ):
#         if isinstance(filename_or_obj, Base):
#             ekds = filename_or_obj
#         elif isinstance(
#             filename_or_obj, str
#         ):  # TODO: Add Path? or handle with try statement
#             ekds = from_source(source_type, filename_or_obj_or_request)
#         else:
#             ekds = from_object(filename_or_obj)

#         return EarthkitObjectBackendEntrypoint.open_dataset(
#             self,
#             ekds,
#             drop_variables=drop_variables,
#             dims_order=dims_order,
#             array_module=array_module,
#             variable_metadata_keys=variable_metadata_keys,
#             variable_index=variable_index,
#             basic=basic,
#             flatten_values=flatten_values,
#             remapping=remapping,
#             profile=profile,
#         )

#     @classmethod
#     def guess_can_open(cls, filename_or_obj):
#         return True  # filename_or_obj.endswith(".grib")


def data_array_to_list(da):
    dims = [dim for dim in da.dims if dim not in ["values", "X", "Y", "lat", "lon"]]
    coords = {key: value for key, value in da.coords.items() if key in dims}

    data_list = []
    metadata_list = []
    for values in product(*[coords[dim].values for dim in dims]):
        local_coords = dict(zip(dims, values))
        xa_field = da.sel(**local_coords)

        # extract metadata from object
        if hasattr(da, "earthkit"):
            metadata = da.earthkit.metadata
        else:
            raise ValueError(
                "Earthkit attribute not found in DataArray. Required for conversion to FieldList!"
            )

        metadata = metadata.override(**local_coords)
        data_list.append(xa_field.values)
        metadata_list.append(metadata)
    return data_list, metadata_list


class XarrayEarthkit:
    def to_grib(self, filename):
        fl = self.to_fieldlist()
        fl.save(filename)


@xarray.register_dataarray_accessor("earthkit")
class XarrayEarthkitDataArray(XarrayEarthkit):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    # Making it not a property so it behaves like a regular earthkit metadata object
    @property
    def metadata(self):
        _metadata = self._obj.attrs.get("metadata", tuple())
        if len(_metadata) < 1:
            from earthkit.data.readers.netcdf import XArrayMetadata

            return XArrayMetadata(self._obj)
        if "id" == _metadata[0]:
            import ctypes

            return ctypes.cast(_metadata[1], ctypes.py_object).value
        elif "grib_handle" == _metadata[0]:
            from earthkit.data.readers.grib.codes import GribCodesReader
            from earthkit.data.readers.grib.metadata import GribMetadata

            handle = GribCodesReader.from_cache(_metadata[1]).at_offset(_metadata[2])
            return GribMetadata(handle)
        else:
            from earthkit.data.readers.netcdf import XArrayMetadata

            return XArrayMetadata(self._obj)

    # Corentin property method:
    # @property
    # def metadata(self):
    #     return self._obj.attrs.get("metadata", None)

    # @metadata.setter
    # def metadata(self, value):
    #     self._obj.attrs["metadata"] = value

    # @metadata.deleter
    # def metadata(self):
    #     self._obj.attrs.pop("metadata", None)

    def to_fieldlist(self):
        data_list, metadata_list = data_array_to_list(self._obj)
        field_list = FieldList.from_numpy(numpy.array(data_list), metadata_list)
        return field_list


@xarray.register_dataset_accessor("earthkit")
class XarrayEarthkitDataSet(XarrayEarthkit):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj
        print("CALLED")

    def to_fieldlist(self):
        data_list = []
        metadata_list = []
        for var in self._obj.data_vars:
            da = self._obj
            da_data, da_metadata = data_array_to_list(da)
            data_list.extend(da_data)
            metadata_list.extend(da_metadata)
        field_list = FieldList.from_numpy(numpy.array(data_list), metadata_list)
        return field_list
