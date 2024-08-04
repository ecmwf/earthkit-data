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

from earthkit.data.utils import ensure_iterable

LOG = logging.getLogger(__name__)


class VariableBuilder:
    def __init__(self, var_dims, data, extra_attr_keys, tensor):
        self.var_dims = var_dims
        self.data = data
        self.attrs = {}
        self.extra_attr_keys = ensure_iterable(extra_attr_keys)
        self.tensor = tensor

    def build(self):
        return xarray.Variable(self.var_dims, self.data, attrs=self.attrs)

    def load_attrs(self, keys, strict=True):
        keys = keys + self.extra_attr_keys
        attr_keys = []
        attrs = {}
        ns_keys = []
        for k in keys:
            if k not in self.var_dims and k not in attr_keys:
                if k.startswith("namespace="):
                    ns_keys.append(k.split("=")[1])
                else:
                    attr_keys.append(k)

        first = None

        # TODO: do we need a strict mode here? The extra cost has to be justified
        if strict:
            from .fieldlist import unique_values

            attrs = unique_values(self.tensor.source, attr_keys)
        else:
            first = self.tensor.source[0]
            attrs = {k: [v] for k, v in first._attributes(attr_keys, default=None).items()}

        if ns_keys:
            if not first:
                first = self.tensor.source[0]
            r = first.metadata(namespace=ns_keys)
            for k, v in r.items():
                attrs[k] = [v]

        self.attrs = attrs

    def adjust_attrs(self, drop_keys=None, rename=None):
        drop_keys = ensure_iterable(drop_keys)
        self.attrs = {k: v[0] for k, v in self.attrs.items() if k not in drop_keys and len(v) == 1}
        if callable(rename):
            self.attrs = rename(self.attrs)


class TensorBackendArray(xarray.backends.common.BackendArray):
    def __init__(self, tensor, dims, shape, xp, variable):
        super().__init__()
        self.tensor = tensor
        self.dims = dims
        self.shape = shape
        self.dtype = xp.dtype(xp.float64)
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

        # ensure axes are squeezed when needed
        singles = [i for i in list(range(len(r.user_shape))) if isinstance(key[i], int)]
        if singles:
            result = result.squeeze(axis=tuple(singles))

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
        # common_metadata=None,
        grid=None,
        flatten_values=False,
        array_module=numpy,
    ):
        self.ds = ds
        self.profile = profile
        self.dims = dims
        # print("Builder, dims=", dims)
        # self.common_metadata = common_metadata

        self.flatten_values = flatten_values
        self.array_module = array_module

        # coords within the tensor describing the non-field dimensions.
        # Note: in the tensor the corresponding dims are called user_dims
        self.tensor_coords = {}

        # coords describing the field dimensions
        self.field_coords = {}

        from .grid import TensorGrid

        self.grid = grid
        if self.grid is None:
            self.grid = TensorGrid(self.ds[0], self.flatten_values)

        if self.profile.add_geo_coords:
            self.field_coords = self._make_field_coords()

    def coords(self):
        r = {k: v.to_xr_var(self.profile) for k, v in self.tensor_coords.items()}
        r.update(self.field_coords)
        return r

    def _make_field_coords(self):
        r = {}
        for k, v in self.grid.coords.items():
            dims = {x: self.grid.dims[x] for x in self.grid.coords_dim[k]}
            r[k] = xarray.Variable(dims, v, self.profile.add_coord_attrs(k))
        return r

    def collect_date_coords(self, tensor):
        if (
            self.profile.add_valid_time_coord
            and "valid_time" not in tensor.user_dims
            and "valid_datetime" not in tensor.user_coords
            and "valid_time" not in self.tensor_coords
        ):
            from .coord import Coord

            _dims, _vals = tensor.make_valid_datetime()
            if _dims is not None and _vals is not None:
                # if _dims is None or _vals is None:
                #     raise ValueError("valid_time coord could not be created")
                self.tensor_coords["valid_time"] = Coord.make("valid_time", _vals, dims=_dims)

    def build(self):
        t_vars = {}
        # we assume each variable forms a full cube
        for variable in self.profile.variables:
            t_vars[variable] = self.make_variable(self.ds, self.dims, self.profile.variable_key, variable)

        # build variable and global attributes
        xr_attrs = self.profile.attrs.builder.build(self.ds, t_vars, rename=True)

        xr_coords = self.profile.rename_coords(self.coords())
        xr_vars = {self.profile.rename_variable(k): v.build() for k, v in t_vars.items()}

        dataset = xarray.Dataset(xr_vars, coords=xr_coords, attrs=xr_attrs)
        return dataset

    def make_variable(self, ds, dims, key, name):
        ds_var = ds.sel(**{key: name})

        tensor_dims, tensor_coords, extra_tensor_attrs = self.prepare_tensor(ds_var, dims, name)
        tensor_dim_keys = [d.key for d in tensor_dims]

        # print("tensor_dims", tensor_dims)

        tensor = ds_var.to_tensor(
            *tensor_dim_keys,
            sort=False,
            progress_bar=False,
            user_dims_and_coords=tensor_coords,
            field_dims_and_coords=(self.grid.dims, self.grid.coords),
            flatten_values=self.flatten_values,
        )

        var_dims = []
        for d in tensor_dims:
            k, c = d.as_coord(d.key, tensor.user_coords[d.key], tensor)
            if k not in self.tensor_coords:
                self.tensor_coords[k] = c
            var_dims.append(k)
        var_dims.extend(tensor.field_dims)

        self.collect_date_coords(tensor)

        # print(f" full_dims={tensor.full_dims}")
        # print(f" full_shape={tensor.full_shape}")

        # self.collect_coords(tensor)
        # var_dims = self.var_dims(tensor)
        # var_dims = [d.key for d in tensor_dims]
        # var_dims = self.profile.rename_dims(var_dims)
        # print(f"var_dims={var_dims}")

        backend_array = TensorBackendArray(
            tensor,
            var_dims,
            tensor.full_shape,
            self.array_module,
            name,
        )

        data = indexing.LazilyIndexedArray(backend_array)

        # Get metadata keys which are common for all fields, and not listed in dataset attrs
        # kk = [k for k in self.profile.index_keys if k not in self.attributes]
        # var_attrs = ds.common_attributes_other(ds_var, kk)

        # var_attrs = {
        #     k: ds_var.index(k)[0] for k in self.profile.var_attributes() if len(ds_var.index(k)) >= 1
        # }
        # var_attrs.update(tensor_attrs)

        # var_attrs = self.profile.remap(var_attrs)

        var = VariableBuilder(var_dims, data, extra_tensor_attrs, tensor)
        # var = xarray.Variable(var_dims, data, attrs=var_attrs)
        return var

    def prepare_tensor(self, ds, dims, name):
        tensor_dims = []
        tensor_coords = {}
        extra_tensor_attrs = []

        # print(f"prepare_tensor: {name=} {dims=}")
        # First check if the dims/coords are consistent with the tensors of the previous variables

        from .fieldlist import unique_values

        vals = unique_values(ds, [d.key for d in dims])

        # print("ensure_dims", self.profile.dims.ensure_dims)

        for d in dims:
            # num = len(ds.index(d.key))
            num = len(vals[d.key])
            # print(f"  {d.key=} {vals[d.key]}")
            if num == 0:
                continue
                if d.name not in self.profile.dims.ensure_dims:
                    raise ValueError(f"Dimension {d} has no valid values")
            else:
                if num == 1 and d.name in self.profile.dims.dims_as_attrs:
                    extra_tensor_attrs.append(d.key)

                elif num > 1 or not self.profile.dims.squeeze or d.name in self.profile.dims.ensure_dims:
                    tensor_dims.append(d)
                    # tensor_coords[d.key] = ds.index(d.key)
                    tensor_coords[d.key] = vals[d.key]
                    self.check_tensor_coords(name, d.key, tensor_coords)

        # TODO:  check if fieldlist forms a full hypercube with respect to the the dims/coordinate
        return tensor_dims, tensor_coords, extra_tensor_attrs

    def check_tensor_coords(self, var_name, coord_name, tensor_coords):
        if self.profile.strict:
            from .check import check_coords

            check_coords(var_name, coord_name, tensor_coords, self.tensor_coords)


class DatasetBuilder:
    def __init__(
        self,
        ds,
        flatten_values=False,
        profile="mars",
        errors=None,
        array_module=numpy,
        **kwargs,
    ):
        """
        auto_split: bool
            When it is True and the data does not form a complete hypercube automatically
            tries to split it into multiple hypercubes and returns a list of datasets (one
            dataset per hypercube). When it is False and the data does not form a complete hypercube
            rases an error. Default is False.
        split_dims: str, or iterable of str, None
            Dimension or list of dimensions to use for splitting the data into multiple hypercubes.
            Default is None.
        """
        self.ds = ds
        self.kwargs = kwargs

        self.flatten_values = flatten_values
        self.profile = profile
        self.errors = errors
        self.array_module = array_module
        self.grids = {}

    def parse(self):
        assert not hasattr(self.ds, "_ek_builder")
        from .fieldlist import WrappedFieldList
        from .profile import Profile

        profile = Profile.make(self.profile, **self.kwargs)

        remapping = profile.remapping.build()
        # print(f"{remapping=}")
        # print(f"{profile.remapping=}")

        # create a new fieldlist and ensure all the required metadata is kept in memory
        ds = WrappedFieldList(self.ds, profile.index_keys, remapping=remapping)
        # print(f"{remapping=}")
        # print(f"ds: {ds.indices()}")

        # global attributes are keys which are the same for all the fields
        # attributes = {k: v[0] for k, v in ds_ori.indices().items() if len(v) == 1}
        # global_attrs = ds.common_indices()

        # LOG.info(f"{attributes=}")

        # if hasattr(ds, "path"):
        #     global_attrs["ekds_source"] = ds.path

        # print("parse dims", profile.dim_keys)

        profile.update(ds)

        # print("parse dims", profile.dim_keys)

        # the data is only sorted once
        ds_sorted = ds.order_by(profile.sort_keys)

        return ds, ds_sorted, profile

    def grid(self, ds):
        grids = ds.index("md5GridSection")
        if len(grids) != 1:
            raise ValueError(f"Expected one grid, got {len(grids)}")
        grid = grids[0]
        key = (grid, self.flatten_values)
        if key not in self.grids:
            from .grid import TensorGrid

            self.grids = {key: TensorGrid(ds[0], self.flatten_values)}
        return self.grids[key]


class SingleDatasetBuilder(DatasetBuilder):
    def __init__(self, *args, **kwargs):
        auto_split = kwargs.get("auto_split", False)
        split_dims = kwargs.get("split_dims", None)
        if auto_split or split_dims:
            raise ValueError("SingleDatasetMaker does not support splitting")

        super().__init__(*args, **kwargs)

    def build(self):
        ds, ds_sorted, profile = self.parse()
        dims = profile.dims.to_list()
        # print("SingleDatasetBuilder.build dims", dims)
        builder = TensorBackendBuilder(
            ds_sorted,
            profile,
            dims,
            grid=self.grid(ds),
            flatten_values=self.flatten_values,
            array_module=numpy,
        )

        return builder.build()


class SplitDatasetBuilder(DatasetBuilder):
    def __init__(self, *args, backend_kwargs=None, **kwargs):
        self.auto_split = backend_kwargs.pop("auto_split", False)
        self.split_dims = backend_kwargs.pop("split_dims", None)
        self.backend_kwargs = dict(**backend_kwargs)
        self.xr_open_dataset_kwargs = dict(**kwargs)

        if not self.auto_split and not self.split_dims:
            raise ValueError("SplitDatasetMaker requires split or split_dims")

        super().__init__(*args, split_dims=self.split_dims, **backend_kwargs)

    def build(self):
        from .splitter import Splitter

        _, ds_sorted, profile = self.parse()
        splitter = Splitter.make(self.auto_split, self.split_dims)
        datasets = []
        for s_dims, s_ds in splitter.split(ds_sorted, profile):
            # print(f"split_dims: {s_dims}   {type(s_ds)}")
            builder = TensorBackendBuilder(
                s_ds,
                profile,
                s_dims,
                grid=self.grid(s_ds),
                flatten_values=self.flatten_values,
                array_module=numpy,
            )

            s_ds._ek_builder = builder
            datasets.append(
                xarray.open_dataset(s_ds, backend_kwargs=self.backend_kwargs, **self.xr_open_dataset_kwargs)
            )
            s_ds._ek_builder = None

        return datasets[0] if len(datasets) == 1 else datasets

    def parse(self):
        assert not hasattr(self.ds, "_ek_builder")
        from .fieldlist import WrappedFieldList
        from .profile import Profile

        profile = Profile.make(self.profile, **self.kwargs)

        remapping = profile.remapping.build()

        # create a new fieldlist and ensure all the required metadata is kept in memory
        ds = WrappedFieldList(self.ds, profile.index_keys, remapping=remapping)

        # print("dims", profile.dim_keys)

        profile.update(ds)

        # print("dims", profile.dim_keys)

        # the data is only sorted once
        ds_sorted = ds.order_by(profile.sort_keys)

        return ds, ds_sorted, profile
