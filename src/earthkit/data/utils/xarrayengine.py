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

LOG = logging.getLogger(__name__)


MARS_GRIB_KEYS_NAMES = [
    "param",
    "class",
    "stream",
    "levtype",
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

VARIABLE_KEYS = ["param", "variable", "parameter", "shortName"]


class Dim:
    name = None
    alias = None
    group = None

    def __init__(self, profile):
        self.profile = profile
        self.adjust_dims()
        if self.name not in self.profile.index_keys:
            self.profile.add_keys([self.name])

    def _insert_at(self, key):
        if self.name not in self.profile.dim_keys:
            try:
                idx = self.profile.dim_keys.index(key)
                self.profile.dim_keys[idx] = self.name
            except ValueError:
                pass

    def adjust_dims(self):
        if self.name not in self.profile.dim_keys:
            self.profile.dim_keys.append(self.name)
        self.profile._remove_dim_keys(self.group)

    def convert(self, value):
        return value


class DateDim(Dim):
    name = "date"
    group = ["valid_datetime", "base_datetime"]


class TimeDim(Dim):
    name = "time"
    group = ["valid_datetime", "base_datetime"]


class StepDim(Dim):
    name = "step"
    group = ["valid_datetime"]


class ValidDatetimeDim(Dim):
    name = "valid_datetime"
    group = ["time", "date", "step", "base_datetime"]

    def adjust_dims(self):
        self._insert_at("date")
        super().adjust_dims()


class BaseDatetimeDim(Dim):
    name = "base_datetime"
    group = ["time", "date", "valid_datetime"]

    def adjust_dims(self):
        self._insert_at("date")
        super().adjust_dims()


class LevelDim(Dim):
    name = "levelist"
    group = ["level", "levtype", "typeOfLevel"]


class LevelPerTypeDim(Dim):
    name = "level"
    group = ["levelist", "levtype", "typeOfLevel"]

    def rename(self, name):
        self.name = name


class LevelAndTypeDim(Dim):
    name = "level_and_type"
    group = ["level", "levelist", "typeOfLevel", "levtype"]

    def adjust_dims(self):
        self._insert_at("level")
        super().adjust_dims()


class NumberDim(Dim):
    name = "number"
    group = []


class Coords:
    def __init__(
        self,
        grid,
        add_valid_datetime_coord=False,
        use_timedelta_step=False,
    ):
        self._user_coords = {}
        self._field_coords = self._from_grid(grid)
        self.add_valid_datetime_coord = add_valid_datetime_coord
        self.use_timedelta_step = use_timedelta_step
        self._step_converted = False

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

    def _convert_step(self):
        if self.use_timedelta_step and not self._step_converted and "step" in self._user_coords:
            from earthkit.data.utils.dates import step_to_delta

            d, v = self._user_coords["step"]
            self._user_coords["step"] = (d, [step_to_delta(x) for x in v])
            self._step_converted = True

    def _from_grid(self, grid):
        r = {}
        if len(grid.coords) == len(grid.dims):
            for k, v in grid.coords.items():
                r[k] = (k, v)
        else:
            for k, v in grid.coords.items():
                dim_name = next(iter(grid.dims))
                if k not in self._user_coords:
                    r[k] = (dim_name, v)
        return r


class Grid:
    def __init__(self, ds, flatten_values=False):
        grids = ds.index("md5GridSection")
        if len(grids) != 1:
            raise ValueError(f"Expected one grid, got {len(grids)}")

        first = ds[0]
        self.dims, self.coords = FieldListTensor._field_part(first, flatten_values)
        print(f"grid dims: {self.dims}")
        print(f"grid coords: {self.coords.keys()}")


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
        remapping=None,
        drop_variables=None,
        use_valid_datetime=False,
        use_base_datetime=False,
        add_level_type=False,
    ):
        self.index_keys = [] if index_keys is None else index_keys
        mandatory_keys = [] if mandatory_keys is None else mandatory_keys
        self.add_keys(mandatory_keys)

        # self.index_keys = index_keys
        self.remapping = build_remapping(remapping)
        self.drop_variables = drop_variables

        for k in remapping.lists:
            self.add_keys([k])

        self.dim_keys = list(self.index_keys)
        self.managed_dims = {}

        if use_valid_datetime:
            self.managed_dims["datetime"] = ValidDatetimeDim(self)
        elif use_base_datetime:
            self.managed_dims["datetime"] = BaseDatetimeDim(self)
            self.managed_dims["step"] = StepDim(self)
            self.add_keys(["valid_datetime"])
        else:
            self.managed_dims["date"] = DateDim(self)
            self.managed_dims["time"] = TimeDim(self)
            self.managed_dims["step"] = StepDim(self)

        # self.managed_dims["level"] = LevelAndTypeDim(self)
        self.managed_dims["level"] = LevelDim(self)
        self.managed_dims["number"] = NumberDim(self)

        self.variable_key = self.guess_variable_key()
        self.variables = []

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

    def add_keys(self, keys):
        self.index_keys += [key for key in keys if key not in self.index_keys]

    def guess_variable_key(self):
        """If any remapping contains a param key, the variable key is set to that key."""
        if self.remapping:
            for k, v in self.remapping.lists.items():
                if any(p in VARIABLE_KEYS for p in v):
                    return k

        return VARIABLE_KEYS[0]

    def adjust_dims_to_remapping(self):
        if self.remapping:
            for k, v in self.remapping.lists.items():
                if k in self.dim_keys:
                    for rk in v:
                        group = self._key_group(rk)
                        for key in group:
                            if key in self.dim_keys:
                                self._remove_dim_keys([key])

    def _remove_dim_keys(self, drop_keys):
        self.dim_keys = [key for key in self.dim_keys if key not in drop_keys]

    def _squeeze(self, ds, attributes):
        self.dim_keys = [key for key in self.dim_keys if key in ds.indices() and key not in attributes]

    def update(self, ds, attributes):
        """
        Parameters
        ----------
        ds: fieldlist
            FieldList object with cached metadata
        attributes: dict
            Index keys which has a singe (valid) value
        """
        # find a valid variable key
        if self.variable_key in VARIABLE_KEYS:
            for k in VARIABLE_KEYS:
                vv = ds.index(k)
                if len(vv) > 0:
                    self.variable_key = k
                    break

        assert self.variable_key is not None
        print("variable_key", self.variable_key)

        # variable keys cannot be dimensions
        self._remove_dim_keys(VARIABLE_KEYS + [self.variable_key])
        assert self.dim_keys
        assert self.variable_key not in self.dim_keys
        print(" -> dim_keys", self.dim_keys)

        self.dim_keys = [key for key in self.dim_keys if key in ds.indices() and key not in attributes]

        assert self.dim_keys
        assert self.variable_key not in self.dim_keys
        print(" -> dim_keys", self.dim_keys)

        self.variables = ds.index(self.variable_key)

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
        print(f"remapping vals: {self.remapping.lists}")
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

        print(f"Key={_k} not found in local metadata")
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
        array_module=numpy,
        variable_metadata_keys=[],
        variable_index=["param", "variable", "shortName"],
        basic=True,
        flatten_values=False,
        remapping=None,
        profile="mars",
    ):

        self.drop_variables = drop_variables
        self.dims_order = dims_order
        self.array_module = array_module
        self.variable_metadata_keys = variable_metadata_keys
        self.variable_index = variable_index
        self.basic = basic
        self.flatten_values = flatten_values
        self.remapping = remapping
        self.profile = profile

        self.use_base_datetime_dim = False
        self.use_valid_datetime_dim = False
        self.add_valid_datetime_coord = False
        self.use_timedelta_step = False
        self.use_level_and_type_dim = False
        self.use_level_per_type_dim = False

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
        print(f"remapping: {self.remapping}, profile: {self.profile}")

        remapping = build_remapping(self.remapping)

        profile = IndexProfile.make(self.profile)(
            remapping=remapping,
            drop_variables=self.drop_variables,
            use_valid_datetime=False,
            use_base_datetime=False,
        )

        print(f"variable_metadata_keys: {self.variable_metadata_keys}")
        print(f"profile index_keys={profile.index_keys}")
        print(f"profile dim_keys={profile.dim_keys}")
        if isinstance(self.variable_metadata_keys, str):
            # get first field
            first = ekds[0]

            self.variable_metadata_keys = get_metadata_keys(self.variable_metadata_keys, first.metadata())

            # release first field
            first = None

        assert isinstance(self.variable_metadata_keys, list)
        profile.add_keys(self.variable_metadata_keys)
        print(f"profile index_keys={profile.index_keys}")

        # create new fieldlist and ensure all the required metadata is kept in memory
        ds_ori = WrappedFieldList(ekds, profile.index_keys, remapping=remapping)
        print(f"ds_ori: {ds_ori.indices()}")

        # global attributes are keys which are the same for all the fields
        attributes = {k: v[0] for k, v in ds_ori.indices().items() if len(v) == 1}

        LOG.info(f"{attributes=}")

        if hasattr(ekds, "path"):
            attributes["ekds_source"] = ekds.path

        # attributes["institution"] = "European Centre fot Medium-range Weather Forecasts"

        print(f"attributes: {attributes}")

        profile.update(ds_ori, attributes)
        ds = ds_ori.order_by(profile.sort_keys)
        dims = profile.dim_keys

        print(f"sort_keys: {profile.sort_keys}")
        print(f"dims: {dims}")

        if self.basic:
            xr_vars = {}

            grid = Grid(ds, flatten_values=self.flatten_values)
            xr_coords = Coords(
                grid,
                use_timedelta_step=self.use_timedelta_step,
                add_valid_datetime_coord=self.add_valid_datetime_coord,
            )

            # we assume each variable forms a full cube
            for variable in profile.variables:
                print(variable)
                ds_var = ds.sel(**{profile.variable_key: variable})

                v_dims = []
                for d in dims:
                    if len(ds_var.index(d)) > 1:
                        v_dims.append(d)

                print(f"v_dims: {v_dims}")

                tensor = ds_var.to_tensor(
                    *v_dims,
                    sort=False,
                    progress_bar=False,
                    field_dims_and_coords=(grid.dims, grid.coords),
                    flatten_values=self.flatten_values,
                )

                print(f" full_dims={tensor.full_dims}")
                print(f" full_shape={tensor.full_shape}")

                xr_coords.collect(tensor)
                xr_dims = list(tensor.full_dims.keys())

                print(f" {tensor.full_coords.keys()} shape={tensor.full_shape}")
                print(f" {xr_dims=}")

                backend_array = EarthkitBackendArray(
                    tensor, xr_dims, tensor.full_shape, self.array_module, variable
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
                var = xarray.Variable(xr_dims, data, attrs=var_attrs)
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
