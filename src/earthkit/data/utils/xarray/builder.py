# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
from abc import ABCMeta
from abc import abstractmethod

import numpy
import xarray
import xarray.core.indexing as indexing

from earthkit.data.utils import ensure_dict
from earthkit.data.utils import ensure_iterable

from .profile import Profile

LOG = logging.getLogger(__name__)

# These backend_kwargs are also direct xarray.open_dataset kwargs
BACKEND_AND_XR_OPEN_DS_KWARGS = ["decode_times", "decode_timedelta", "drop_variables"]

# These kwargs cannot be passed to xarray.open_dataset (not even inside backend_kwargs)
NON_XR_OPEN_DS_KWARGS = ["split_dims", "direct_backend"]


class VariableBuilder:
    def __init__(self, name, var_dims, data_maker, local_attr_keys, tensor, remapping):
        self.name = name
        self.var_dims = var_dims
        self.data_maker = data_maker
        self._attrs = {}
        self.local_keys = ensure_iterable(local_attr_keys)
        self.tensor = tensor
        self.remapping = remapping

    def build(self):
        attrs = {
            "message": self.tensor.source[0].metadata().override()._handle.get_buffer(),
        }
        self._attrs["_earthkit"] = attrs
        data = self.data_maker(self.tensor, self.var_dims, self.name)
        return xarray.Variable(self.var_dims, data, attrs=self._attrs)

    def load_attrs(self, keys, strict=True):
        keys = keys + self.local_keys
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
            attrs = self.tensor.source.unique_values(attr_keys)
        else:
            first = self.tensor.source[0]
            attrs = {k: [v] for k, v in first._attributes(attr_keys, default=None).items()}

        if ns_keys:
            if not first:
                first = self.tensor.source[0]
            r = first.metadata(namespace=ns_keys)
            for k, v in r.items():
                attrs[k] = [v]

        self._attrs = attrs

        return {k: v for k, v in self._attrs.items() if k not in self.local_keys}

    def adjust_attrs(self, drop_keys=None, rename=None):
        drop_keys = ensure_iterable(drop_keys)
        drop_keys = [k for k in drop_keys if k not in self.local_keys]
        self._attrs = {k: v[0] for k, v in self._attrs.items() if k not in drop_keys and len(v) == 1}
        if callable(rename):
            self._attrs = rename(self._attrs)

    @property
    def attrs(self):
        return self._attrs


class TensorBackendArray(xarray.backends.common.BackendArray):
    def __init__(self, tensor, dims, shape, xp, dtype, variable):
        super().__init__()
        self.tensor = tensor
        self.dims = dims
        self.shape = shape

        # xp and dtype must be set for xarray
        self.xp = xp if xp is not None else numpy
        if dtype is None:
            dtype = numpy.dtype("float64")
        self.dtype = xp.dtype(dtype)

        self._var = variable

    @property
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
        result = r.to_numpy(index=field_index, dtype=self.dtype)

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
        if self.xp and self.xp != numpy:
            result = self.xp.asarray(result)

        return result


class BackendDataBuilder(metaclass=ABCMeta):
    def __init__(
        self,
        ds,
        profile,
        dims,
        grid=None,
    ):
        self.ds = ds
        self.profile = profile
        self.dims = dims

        self.flatten_values = profile.flatten_values
        self.dtype = profile.dtype
        self.array_module = profile.array_module

        # Note: these coords inside the tensor are called user_coords and
        # the corresponding dims are called user_dims
        self.tensor_coords = {}

        # coords describing the field dimensions
        self.field_coords = {}

        self.grid = self._ensure_grid(grid)
        if self.profile.add_geo_coords:
            self.field_coords = self._make_field_coords()

    def coords(self):
        r = {k: v.to_xr_var(self.profile) for k, v in self.tensor_coords.items()}
        r.update(self.field_coords)
        return r

    def _ensure_grid(self, grid):
        if grid is None:
            from .grid import TensorGrid

            grid = TensorGrid(self.ds[0], self.flatten_values)
        return grid

    def _make_field_coords(self):
        r = {}
        for k, v in self.grid.coords.items():
            dims = {x: self.grid.dims[x] for x in self.grid.coords_dim[k]}
            r[k] = xarray.Variable(dims, v, self.profile.attrs.coord_attrs.get(k, {}))
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
                self.tensor_coords["valid_time"] = Coord.make("valid_time", _vals, dims=_dims)

    def build(self):
        # we assume each variable forms a full cube
        var_builders = self.pre_build_variables()

        # build variable and global attributes
        xr_attrs = self.profile.attrs.builder.build(self.ds, var_builders, rename=True)
        xr_coords = self.coords()

        # build variables
        xr_vars = {self.profile.rename_variable(k): v.build() for k, v in var_builders.items()}

        # build dataset
        dataset = xarray.Dataset(xr_vars, coords=xr_coords, attrs=xr_attrs)

        if self.profile.rename_dims_map():
            dataset = dataset.rename(self.profile.rename_dims_map())

        if "source" not in dataset.encoding:
            dataset.encoding["source"] = None

        return dataset

    @abstractmethod
    def build_values(self, *args, **kwargs):
        pass

    @abstractmethod
    def pre_build_variables(self):
        pass

    def pre_build_variable(self, ds_var, dims, name):
        tensor_dims, tensor_coords, tensor_coords_component, extra_tensor_attrs = self.prepare_tensor(
            ds_var, dims, name
        )
        tensor_dim_keys = [d.key for d in tensor_dims]

        LOG.debug(f"{tensor_dims=} {tensor_coords=} {tensor_coords_component=} {extra_tensor_attrs=}")
        LOG.debug(f"{tensor_dim_keys=}")

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
            # Create coord for each dimension
            # Dimensions like "level_per_type" are templates and will be
            # added as multiple concrete dimensions to the dataset
            k, c = d.as_coord(
                d.key,
                values=tensor.user_coords[d.key],
                component=tensor_coords_component.get(d.key, None),
                tensor=tensor,
            )
            if k not in self.tensor_coords:
                self.tensor_coords[k] = c
            var_dims.append(k)
        var_dims.extend(tensor.field_dims)

        self.collect_date_coords(tensor)
        data_maker = self.build_values
        remapping = self.profile.remapping.build()

        var_builder = VariableBuilder(name, var_dims, data_maker, extra_tensor_attrs, tensor, remapping)

        return var_builder

    def prepare_tensor(self, ds, dims, name):
        tensor_dims = []
        tensor_coords = {}
        tensor_coords_component = {}
        extra_tensor_attrs = []

        LOG.debug(f"{name=} {dims=}")

        # First check if the dims/coords are consistent with the tensors of the previous variables
        vals, component_vals = ds.unique_values([d.key for d in dims], component=True)

        LOG.debug(f"unique_values={vals}")
        LOG.debug(f"ensure_dims={self.profile.dims.ensure_dims}")

        for d in dims:
            num = len(vals[d.key])
            # LOG.debug(f"  {d.key=} {vals[d.key]}")
            if num == 0:
                continue
                # if d.name not in self.profile.dims.ensure_dims:
                #     raise ValueError(f"Dimension {d} has no valid values for variable={name}")
            else:
                if num > 1 and d.enforce_unique:
                    raise ValueError(
                        f"Dimension '{d.name}' of variable '{name}' has multiple values={vals[d.key]}"
                    )
                elif num == 1 and d.name in self.profile.dims.dims_as_attrs:
                    extra_tensor_attrs.append(d.key)
                elif num > 1 or not self.profile.dims.squeeze or d.name in self.profile.dims.ensure_dims:
                    tensor_dims.append(d)
                    tensor_coords[d.key] = vals[d.key]
                    if d.key in component_vals:
                        tensor_coords_component[d.key] = component_vals[d.key]
                    self.check_tensor_coords(name, d.key, tensor_coords)

        # TODO:  check if fieldlist forms a full hypercube with respect to the the dims/coordinates
        return tensor_dims, tensor_coords, tensor_coords_component, extra_tensor_attrs

    def check_tensor_coords(self, var_name, coord_name, tensor_coords):
        if self.profile.strict:
            from .check import check_coords

            check_coords(var_name, coord_name, tensor_coords, self.tensor_coords)


class TensorBackendDataBuilder(BackendDataBuilder):
    """Build a dataset using memory backend.

    Each variable contain a TensorBackendArray object that loads the data on demand from
    the GRIB using the associated TensorFieldList. This solution can work bot for GRIB data
    stored in memory or on disk.
    """

    def pre_build_variables(self):
        """Generate a builder for each variable"""
        builders = {}

        # we assume each variable forms a full cube
        for name in self.profile.variables:
            ds_var = self.ds.sel(**{self.profile.variable_key: name})
            builders[name] = self.pre_build_variable(ds_var, self.dims, name)

        return builders

    def build_values(self, tensor, var_dims, name):
        """Generate the data object stored in the xarray variable"""
        backend_array = TensorBackendArray(
            tensor,
            var_dims,
            tensor.full_shape,
            self.array_module,
            self.dtype,
            name,
        )

        data = indexing.LazilyIndexedArray(backend_array)
        return data


class MemoryBackendDataBuilder(BackendDataBuilder):
    """Build a dataset using memory backend.

    Each variable contain data values in memory copied from the input fields. As soon as a
    field's values are copied, the field is immediately released and its memory is freed if the
    field supports this operation. Fields released in this way are not available for further access.
    """

    def pre_build_variables(self):
        """Generate a builder for each variable"""
        builders = {}
        groups = self.ds.group(self.profile.variable_key, self.profile.variables)

        # we assume each variable forms a full cube
        for name in groups:
            ds_var = groups[name]
            builders[name] = self.pre_build_variable(ds_var, self.dims, name)

        return builders

    def build_values(self, tensor, var_dims, name):
        """Generate the data object stored in the xarray variable"""

        # At this point all the fields must be a ReleasableField.
        # We mark the fields so that their data will be released on the next
        # values access.
        if self.profile.release_source:
            for f in tensor.source:
                f.keep = False

        return tensor.to_numpy(dtype=self.dtype)


class DatasetBuilder:
    def __init__(
        self,
        ds,
        backend_kwargs=None,
        other_kwargs=None,
    ):
        self.ds = ds
        self.backend_kwargs = dict(**backend_kwargs)
        self.xr_open_dataset_kwargs = ensure_dict(other_kwargs)
        self.profile_kwargs = dict(**backend_kwargs)

        # collect backend kwargs that can be passed to xarray.open_dataset
        for k in NON_XR_OPEN_DS_KWARGS:
            self.backend_kwargs.pop(k, None)

        self.profile = self.make_profile()
        if self.profile.lazy_load:
            self.builder = TensorBackendDataBuilder
        else:
            self.builder = MemoryBackendDataBuilder

        self.split_dims = self.profile.dims.split_dims
        self.direct_backend = self.profile.direct_backend

        self.grids = {}

    def make_profile(self, force=False):
        profile_kwargs = dict(**self.profile_kwargs)
        profile = profile_kwargs.pop("profile", Profile.DEFAULT_PROFILE_NAME)
        return Profile.make(profile, force=force, **profile_kwargs)

    def parse(self, ds, profile=None, full=False):
        assert not hasattr(ds, "_ek_builder")
        from .fieldlist import XArrayInputFieldList

        if profile is None:
            profile = self.make_profile(force=True)

        remapping = profile.remapping.build()

        LOG.debug(f"{remapping=}")
        LOG.debug(f"{profile.remapping=}")
        LOG.debug(f"{profile.index_keys=}")

        # create a new fieldlist for optimised access to unique values
        ds_xr = XArrayInputFieldList(ds, keys=profile.index_keys, remapping=remapping)
        # LOG.debug(f"{ds.db=}")

        LOG.debug(f"before update: {profile.dim_keys=}")
        profile.update(ds_xr)
        LOG.debug(f"after update: {profile.dim_keys=}")

        LOG.debug(f"{profile.sort_keys=}")
        # the data is only sorted once
        ds_xr = ds_xr.order_by(profile.sort_keys)

        if not profile.lazy_load and profile.release_source:
            ds_xr.make_releasable()

        return ds_xr, profile

    def grid(self, ds):
        grids = ds.index("md5GridSection")

        if len(grids) != 1:
            raise ValueError(f"Expected one grid, got {len(grids)}")
        grid = grids[0]
        key = (grid, self.profile.flatten_values)

        if key not in self.grids:
            from .grid import TensorGrid

            self.grids = {key: TensorGrid(ds[0], self.profile.flatten_values)}
        return self.grids[key]


class SingleDatasetBuilder(DatasetBuilder):
    def __init__(self, *args, from_xr=False, **kwargs):
        super().__init__(*args, **kwargs)

        if self.split_dims:
            raise ValueError("SingleDatasetMaker does not support splitting")

        if from_xr and self.direct_backend:
            raise ValueError(
                "SingleDatasetMaker does not support direct_backend=True when invoked from xarray"
            )

    def build(self):
        ds_sorted, _ = self.parse(self.ds, self.profile)
        dims = self.profile.dims.to_list()
        LOG.debug(f"{dims=}")
        builder = self.builder(
            ds_sorted,
            self.profile,
            dims,
            grid=self.grid(ds_sorted),
        )
        r = builder.build()
        return r


class SplitDatasetBuilder(DatasetBuilder):
    def __init__(self, *args, **kwargs):
        """
        split_dims: str, or iterable of str, None
            Dimension or list of dimensions to use for splitting the data into multiple hypercubes.
            Default is None.
        """
        super().__init__(*args, **kwargs)

        if not self.split_dims:
            raise ValueError("SplitDatasetMaker requires split_dims")

    def prepare(self, keys):
        from .fieldlist import XArrayInputFieldList

        remapping = self.profile.remapping.build()

        # LOG.debug(f"split_dims={self.split_dims}")
        ds_xr = XArrayInputFieldList(self.ds, keys=self.profile.index_keys, remapping=remapping)

        vals = ds_xr.unique_values(*keys)

        return ds_xr, vals

    def build(self):
        from .splitter import Splitter

        splitter = Splitter.make(self.split_dims)
        datasets = []
        for ds, profile in splitter.split(self):
            dims = profile.dims.to_list()
            print(f"splitting {dims=} type of s_ds={type(ds)}")
            # LOG.debug(f"splitting {dims=} type of s_ds={type(ds)}")
            builder = self.builder(
                ds,
                profile,
                dims,
                grid=self.grid(ds),
            )

            ds._ek_builder = builder
            if self.direct_backend:
                datasets.append(builder.build())
            else:
                ds._ek_builder = builder
                datasets.append(
                    xarray.open_dataset(ds, backend_kwargs=self.backend_kwargs, **self.xr_open_dataset_kwargs)
                )
                ds._ek_builder = None

        return datasets[0] if len(datasets) == 1 else datasets


def from_earthkit(ds, backend_kwargs=None, other_kwargs=None):
    """Create an xarray dataset from an earthkit fieldlist.

    Parameters
    ----------
    ds: FieldList
        The input fieldlist.
    backend_kwargs: dict, optional
        Backend kwargs that can be passed to
        :py:meth:`xarray.open_dataset` as "backend_kwargs".
    other_kwargs: dict, optional
        Additional kwargs passed to :py:meth:`xarray.open_dataset`. Cannot contain
        any of the keys in ``backend_kwargs``.
    """
    backend_kwargs = ensure_dict(backend_kwargs)
    other_kwargs = ensure_dict(other_kwargs)

    # certain kwargs are both backend_kwargs and other_kwargs. We copy them to
    # backend_kwargs_full
    backend_kwargs_full = dict(**backend_kwargs)
    for k in BACKEND_AND_XR_OPEN_DS_KWARGS:
        if k in other_kwargs:
            backend_kwargs_full[k] = other_kwargs[k]

    # to create the profile we need all the possible backend_kwargs (bar profile)
    profile = backend_kwargs_full.pop("profile", Profile.DEFAULT_PROFILE_NAME)
    profile = Profile.make(profile, **backend_kwargs_full)

    # the backend builder is directly called bypassing xarray.open_dataset
    if profile.direct_backend:
        backend_kwargs_full["profile"] = profile
        if not profile.dims.split_dims:
            return SingleDatasetBuilder(ds, backend_kwargs=backend_kwargs_full).build()
        else:
            return SplitDatasetBuilder(ds, backend_kwargs=backend_kwargs_full).build()
    # xarray.open_dataset is called
    else:
        assert other_kwargs["engine"] == "earthkit"
        backend_kwargs["profile"] = profile

        # certain kwargs are not allowed in xarray.open_dataset
        for k in NON_XR_OPEN_DS_KWARGS:
            backend_kwargs.pop(k, None)

        if not profile.dims.split_dims:
            return xarray.open_dataset(ds, backend_kwargs=backend_kwargs, **other_kwargs)
        else:
            return SplitDatasetBuilder(ds, backend_kwargs=backend_kwargs, other_kwargs=other_kwargs).build()
