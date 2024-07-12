# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

import numpy
import xarray
import xarray.core.indexing as indexing

from earthkit.data.core.order import build_remapping
from earthkit.data.utils import ensure_iterable

LOG = logging.getLogger(__name__)


class Grid:
    def __init__(self, field, flatten_values=False):
        from earthkit.data.indexing.tensor import FieldListTensor

        self.dims, self.coords, self.coords_dim = FieldListTensor._field_part(field, flatten_values)


class TensorBackendArray(xarray.backends.common.BackendArray):
    def __init__(self, tensor, dims, shape, xp, variable):
        super().__init__()
        self.tensor = tensor
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
        # print(f"dims: {self.dims} key: {key} shape: {self.shape}")
        # isels = dict(zip(self.dims, key))
        # r = self.ekds.isel(**isels)
        # print(f"t-coords={self.tensor.user_coords}")
        r = self.tensor[key]
        # print(r.source.ls())
        # print(f"r-shape: {r.user_shape}")

        field_index = r.field_indexes(key)
        # print(f"field.index={field_index} coords={r.user_coords}")
        # result = r.to_numpy(index=field_index).squeeze()
        result = r.to_numpy(index=field_index)
        # print("result", result.shape)
        # result = self.ekds.isel(**isels).to_numpy()

        # print("result", result.shape)
        # print(f"Loaded {self.xp.__name__} with shape: {result.shape}")

        # Loading as numpy but then converting. This needs to be changed upstream (eccodes)
        # to load directly into cupy.
        # Maybe some incompatibilities when trying to copy from FFI to cupy directly
        result = self.xp.asarray(result)

        return result


class TensorBackendBuilder:
    def __init__(
        self,
        ds,
        profile,
        dims,
        attributes,
        grid=None,
        flatten_values=False,
        timedelta_step=False,
        valid_datetime_coord=False,
        level_per_type_dim=False,
        geo_coords=True,
        array_module=numpy,
    ):
        self.ds = ds
        self.profile = profile
        self.dims = dims
        self.attributes = attributes

        self.flatten_values = flatten_values
        self.timedelta_step = timedelta_step
        self.valid_datetime_coord = valid_datetime_coord
        self.level_per_type_dim = level_per_type_dim
        self.array_module = array_module

        self.tensor_coords = {}
        self.field_coords = {}

        self.grid = grid
        if self.grid is None:
            self.grid = Grid(self.ds[0], self.flatten_values)

        if geo_coords:
            self.field_coords = self._make_field_coords()

    @property
    def coords(self):
        r = {k: v.make_var(self.profile) for k, v in self.tensor_coords.items()}

        # r = {k: v for k, v in self.tensor_coords.items()}
        r.update(self.field_coords)
        return r

    def _make_field_coords(self):
        r = {}
        for k, v in self.grid.coords.items():
            dims = {x: self.grid.dims[x] for x in self.grid.coords_dim[k]}
            r[k] = xarray.Variable(dims, v, self.profile.add_coord_attrs(k))
        return r

    def var_dims(self, tensor):
        """Return the list of xr dimensions for the tensor"""
        dims = list(tensor.full_dims.keys())
        dims = self.adjust_level_dim(dims, tensor)
        return dims

    def collect_coords(self, tensor):
        from .coord import Coord

        for k, v in tensor.user_coords.items():
            if k not in self.tensor_coords:
                self.tensor_coords[k] = Coord.make(k, v, ds=tensor.source)

        # if not self.tensor_coords:
        #     self.tensor_coords = {
        #         k: (k, v, self.profile.coord_attrs(k)) for k, v in tensor.user_coords.items()
        #     }
        # else:
        #     for k, v in tensor.user_coords.items():
        #         if k not in self.tensor_coords:
        #             self.tensor_coords[k] = (k, v, self.profile.coord_attrs(k))

        self.adjust_level(tensor)
        self.adjust_date(tensor)

    def adjust_level(self, tensor):
        if self.level_per_type_dim:
            self.tensor_coords.pop("level", None)
            if "level" in tensor.user_dims:
                lev_type = tensor.source[0].metadata("levtype")
                # print("->lev_type", lev_type)
                if not lev_type:
                    raise ValueError("levtype not found in metadata")
                if lev_type not in self.tensor_coords:
                    self.tensor_coords[lev_type] = (
                        lev_type,
                        list(tensor.user_coords["level"]),
                    )

    def adjust_level_dim(self, dims, tensor):
        if self.level_per_type_dim:
            if "level" in dims:
                lev_type = tensor.source[0].metadata("levtype")
                if lev_type in self.tensor_coords:
                    idx = dims.index("level")
                    dims[idx] = lev_type
        return dims

    def adjust_date(self, tensor):
        if (
            self.valid_datetime_coord
            and "valid_datetime" not in tensor.user_dims
            and "valid_datetime" not in self.tensor_coords
        ):
            from .coord import Coord

            _dims, _vals = tensor.make_valid_datetime()
            if _dims is None or _vals is None:
                raise ValueError("valid_datetime coord could not be created")
            self.tensor_coords["valid_datetime"] = Coord.make("valid_datetime", _vals, dims=_dims)

            # self.tensor_coords["valid_datetime"] = xarray.Variable(_dims, _vals)

    def adjust_step(self):
        # TODO: ensure only called once
        if self.timedelta_step and "step" in self.tensor_coords:
            from earthkit.data.utils.dates import step_to_delta

            d, v = self.tensor_coords["step"]
            self.tensor_coords["step"] = (d, [step_to_delta(x) for x in v])

    def _get_field_coords(self):
        r = {}
        for k, v in self.grid.coords.items():
            dims = {x: self.grid.dims[x] for x in self.grid.coords_dim[k]}
            r[k] = xarray.Variable(dims, v)
        return r

    def _compare(self, name, vals1, vals2):
        pass

    def build(self):
        xr_vars = {}
        # dims = profile.dim_keys

        # we assume each variable forms a full cube
        for variable in self.profile.variables:
            xr_vars[variable] = self.make_variable(self.ds, self.dims, self.profile.variable_key, variable)

        # self.adjust_step()

        # attrs = self.attributes.copy()
        # attrs.update(self.profile.attributes())
        # attrs = self.profile.adjust_attributes(attrs)
        attrs = self.profile.g_attrs.attrs(self.ds)
        coords = self.profile.rename_coords(self.coords)
        dataset = xarray.Dataset(xr_vars, coords=coords, attrs=attrs)

        # dataset = self.profile.rename_dims(dataset)
        # dataset = self.profile.rename_coords(dataset)
        return dataset

    def make_variable(self, ds, dims, key, name):
        ds_var = ds.sel(**{key: name})

        tensor_dims = []
        for d in dims:
            if len(ds_var.index(d)) > 1 or (not self.profile.squeeze and len(ds_var.index(d)) >= 1):
                tensor_dims.append(d)

        print("tensor_dims", tensor_dims)
        tensor = ds_var.to_tensor(
            *tensor_dims,
            sort=False,
            progress_bar=False,
            field_dims_and_coords=(self.grid.dims, self.grid.coords),
            flatten_values=self.flatten_values,
        )

        # print(f" full_dims={tensor.full_dims}")
        # print(f" full_shape={tensor.full_shape}")

        self.collect_coords(tensor)

        var_dims = self.var_dims(tensor)
        var_dims = self.profile.rename_dims(var_dims)

        backend_array = TensorBackendArray(
            tensor,
            var_dims,
            tensor.full_shape,
            self.array_module,
            name,
        )

        # print("tensor.full_shape", tensor.full_shape)
        data = indexing.LazilyIndexedArray(backend_array)

        # Get metadata keys which are common for all fields, and not listed in dataset attrs
        # kk = [k for k in self.profile.index_keys if k not in self.attributes]
        # var_attrs = ds.common_attributes_other(ds_var, kk)

        var_attrs = {
            k: ds_var.index(k)[0] for k in self.profile.var_attributes() if len(ds_var.index(k)) >= 1
        }

        var_attrs = self.profile.remap(var_attrs)
        # var_attrs = {k: v[0] for k, v in ds_var.indices().items() if len(v) == 1}

        # var_attrs = _get_common_attributes(
        #     ek_variable.source,
        #     [k for k in var_metadata_keys if k not in attributes],
        # )

        # print(f"var_attrs: {var_attrs}")

        # if hasattr(ds_var[0], "_offset") and hasattr(ekds, "path"):
        #     var_attrs["metadata"] = (
        #         "grib_handle",
        #         ekds.path,
        #         ds_var[0]._offset,
        #     )
        # else:
        #     var_attrs["metadata"] = ("id", id(ds_var[0].metadata()))

        # # print(f" -> var_attrs: {var_attrs}")

        # print("var_dims=", var_dims)
        var = xarray.Variable(var_dims, data, attrs=var_attrs)
        return var


class DatasetBuilder:
    def __init__(
        self,
        ds,
        # var_key=None,
        var_metadata_keys=None,
        # variable_mapping=None,
        # drop_variables=None,
        # extra_index_keys=None,
        # ignore_index_keys=None,
        # dims=None,
        # squeeze=True,
        # auto_split=False,
        # split_dims=None,
        flatten_values=False,
        remapping=None,
        profile="mars",
        # base_datetime_dim=False,
        # valid_datetime_dim=False,
        # valid_datetime_coord=False,
        # timedelta_step=False,
        # level_and_type_dim=False,
        # level_per_type_dim=False,
        add_geo_coords=True,
        merge_cf_and_pf=False,
        errors=None,
        array_module=numpy,
        **kwargs,
    ):
        """
        auto_split: bool
            When it is True and the data does not form a complete hypercube automatically
            tries to split the data into multiple hypercubes and returns a list of datasets (one
            dataset per hypercube). When it is False and the data does not form a complete hypercube
            rases an error. Default is False.
        split_dims: str, or iterable of str, None
            Dimension or list of dimensions to use for splitting the data into multiple hypercubes.
            Default is None.
        """
        self.ds = ds
        self.kwargs = kwargs

        # self.var_key = var_key
        self.var_metadata_keys = ensure_iterable(var_metadata_keys)
        # self.variable_mapping = variable_mapping
        # self.drop_variables = ensure_iterable(drop_variables)
        # self.extra_index_keys = ensure_iterable(extra_index_keys)
        # self.ignore_index_keys = ensure_iterable(ignore_index_keys)
        # self.dims = ensure_iterable(dims)
        # self.squeeze = squeeze
        # self.auto_split = auto_split
        # self.split_dims = ensure_iterable(split_dims)
        self.flatten_values = flatten_values
        self.remapping = remapping
        self.profile_name = profile
        # self.base_datetime_dim = base_datetime_dim
        # self.valid_datetime_dim = valid_datetime_dim
        # self.valid_datetime_coord = valid_datetime_coord
        # self.timedelta_step = timedelta_step
        # self.level_and_type_dim = level_and_type_dim
        # self.level_per_type_dim = level_per_type_dim
        self.add_geo_coords = add_geo_coords
        self.merge_cf_and_pf = merge_cf_and_pf
        self.errors = errors
        self.array_module = array_module

        self.grids = {}

        # patches = None
        # if self.merge_cf_and_pf:
        #     patches = {"type": {"cf": "pf"}, "number": {None: 0}}

        # self.remapping = build_remapping(self.remapping, patches)

    def parse(self):
        assert not hasattr(self.ds, "_ek_builder")

        patches = None
        if self.merge_cf_and_pf:
            patches = {"type": {"cf": "pf"}, "number": {None: 0}}

        remapping = build_remapping(self.remapping, patches)

        from .profile import Profile

        profile = Profile.make(self.profile_name, remapping=remapping, **self.kwargs)
        # profile = profile(
        #     remapping=remapping,
        #     var_key=self.var_key,
        #     extra_index_keys=self.extra_index_keys,
        #     drop_variables=self.drop_variables,
        #     valid_datetime_dim=self.valid_datetime_dim,
        #     base_datetime_dim=self.base_datetime_dim,
        #     valid_datetime_coord=self.valid_datetime_coord,
        #     level_per_type_dim=self.level_per_type_dim,
        #     squeeze=self.squeeze,
        # )

        # print(f"var_metadata_keys: {self.var_metadata_keys}")
        # print(f"profile index_keys={profile.index_keys}")
        # print(f"profile dim_keys={profile.dim_keys}")
        if isinstance(self.var_metadata_keys, str):
            # get first field
            first = self.ds[0]

            from .profile import get_metadata_keys

            self.var_metadata_keys = get_metadata_keys(self.var_metadata_keys, first.metadata())

            # release first field
            first = None

        assert isinstance(self.var_metadata_keys, list)
        profile.add_keys(self.var_metadata_keys)
        # print(f"profile index_keys={profile.index_keys}")

        from .fieldlist import WrappedFieldList

        # create new fieldlist and ensure all the required metadata is kept in memory
        ds = WrappedFieldList(self.ds, profile.index_keys, remapping=remapping)
        # print(f"{remapping=}")
        # print(f"ds: {ds.indices()}")

        # global attributes are keys which are the same for all the fields
        # attributes = {k: v[0] for k, v in ds_ori.indices().items() if len(v) == 1}
        attributes = ds.common_indices()

        # LOG.info(f"{attributes=}")

        if hasattr(ds, "path"):
            attributes["ekds_source"] = ds.path

        # attributes["institution"] = "European Centre fot Medium-range Weather Forecasts"

        # print(f"attributes: {attributes}")

        profile.update(ds, attributes)

        # the data is only sorted once
        ds_sorted = ds.order_by(profile.sort_keys)

        # dims = profile.dim_keys

        # print(f"sort_keys: {profile.sort_keys}")
        # print(f"dims: {profile.dim_keys}")

        return ds, ds_sorted, profile, attributes

    def grid(self, ds):
        grids = ds.index("md5GridSection")
        if len(grids) != 1:
            raise ValueError(f"Expected one grid, got {len(grids)}")
        grid = grids[0]
        key = (grid, self.flatten_values)
        if key not in self.grids:
            self.grids = {key: Grid(ds[0], self.flatten_values)}
        return self.grids[key]


class SingleDatasetBuilder(DatasetBuilder):
    def __init__(self, *args, **kwargs):
        auto_split = kwargs.get("auto_split", False)
        split_dims = kwargs.get("split_dims", None)

        if auto_split or split_dims:
            raise ValueError("SingleDatasetMaker does not support splitting")

        super().__init__(*args, **kwargs)

    def build(self):
        ds, ds_sorted, profile, attributes = self.parse()
        dims = profile.dim_keys
        builder = TensorBackendBuilder(
            ds_sorted,
            profile,
            dims,
            attributes,
            grid=self.grid(ds),
            flatten_values=self.flatten_values,
            timedelta_step=profile.step_as_timedelta,
            valid_datetime_coord=profile.add_valid_time_coord,
            level_per_type_dim=profile.add_level_per_type_dim,
            geo_coords=self.add_geo_coords,
            array_module=numpy,
        )

        return builder.build()


class SplitDatasetBuilder(DatasetBuilder):
    def __init__(self, *args, **kwargs):
        auto_split = kwargs.get("auto_split", False)
        split_dims = kwargs.get("split_dims", None)

        if not auto_split and not split_dims:
            raise ValueError("SplitDatasetMaker requires split or split_dims")

        super().__init__(*args, **kwargs)

    def build(self):
        from .splitter import Splitter

        _, ds_sorted, profile, attributes = self.parse()
        splitter = Splitter.make(self.auto_split, self.split_dims)
        datasets = []
        for s_dims, s_ds in splitter.split(ds_sorted, profile):
            # print(f"split_dims: {s_dims}   {type(s_ds)}")
            builder = TensorBackendBuilder(
                s_ds,
                profile,
                s_dims,
                attributes,
                grid=self.grid(s_ds),
                flatten_values=self.flatten_values,
                timedelta_step=profile.step_as_timedelta,
                valid_datetime_coord=profile.add_valid_datetime_coord,
                level_per_type_dim=profile.add_level_per_type_dim,
                geo_coords=self.add_geo_coords,
                array_module=numpy,
            )

            s_ds._ek_builder = builder
            datasets.append(xarray.open_dataset(s_ds, **self.kwargs))
            s_ds._ek_builder = None

        return datasets[0] if len(datasets) == 1 else datasets
