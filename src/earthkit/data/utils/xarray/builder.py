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

import xarray
import xarray.core.indexing as indexing

from earthkit.data.utils import ensure_dict
from earthkit.data.utils import ensure_iterable

from .attrs import AttrList
from .profile import Profile

LOG = logging.getLogger(__name__)

# These backend_kwargs are also direct xarray.open_dataset kwargs
BACKEND_AND_XR_OPEN_DS_KWARGS = ["decode_times", "decode_timedelta", "drop_variables"]

# These kwargs cannot be passed to xarray.open_dataset (not even inside backend_kwargs)
NON_XR_OPEN_DS_KWARGS = ["split_dims", "direct_backend"]


class VariableBuilder:
    def __init__(
        self,
        name,
        var_dims,
        data_maker,
        tensor,
        remapping,
        local_attr_keys=None,
        fixed_local_attrs=None,
    ):
        """
        Create a builder for a single variable in the dataset.

        Parameters
        ----------
        name: str
            The name of the variable.
        var_dims: list
            The dimensions of the variable.
        data_maker: callable
            A function that generates the data object stored in the xarray variable.
        tensor: Tensor
            The tensor object that contains the data.
        remapping: Remapping
            The remapping object that contains the remapping information.
        local_attr_keys: list, optional
            A list of metadata keys that are used to collect local attributes. These attributes
            are not taken into account by the attribute policies.
        fixed_local_attrs: dict, optional
            A dictionary of fixed local attributes that are added to the variable. These attributes
            are not taken into account by the attribute policies.
        """
        self.name = name
        self.var_dims = var_dims
        self.data_maker = data_maker
        self._attrs = {}
        self.local_keys = ensure_iterable(local_attr_keys)
        self.fixed_local_attrs = ensure_dict(fixed_local_attrs)
        self.tensor = tensor
        self.remapping = remapping

    def build(self, add_earthkit_attrs=True):
        if add_earthkit_attrs:
            if hasattr(self.tensor.source[0], "handle"):
                md = self.tensor.source[0].metadata().override()
                attrs = {
                    "message": md._handle.get_buffer(),
                    "bitsPerValue": md.get("bitsPerValue", 0),
                }
                self._attrs["_earthkit"] = attrs

        self._attrs.update(self.fixed_local_attrs)
        data = self.data_maker(self.tensor, self.var_dims, self.name)
        return xarray.Variable(self.var_dims, data, attrs=self._attrs)

    def collect_attrs(self, attrs, strict=True, extra_attrs=None):
        """Load the attributes for the variable.

        Parameters
        ----------
        attrs: list
            A list of attributes to be collected.
        strict: bool, optional
            If True, perform a strict check on the attributes.
        collect: list, optional
            A list of attributes that are collected but not added to the variable attributes.
        """
        attrs = attrs + AttrList(self.local_keys)

        res = {}
        keys_strict = []
        fixed_attrs = {}

        first = None

        def _metadata():
            nonlocal first
            return self.tensor.source[0].metadata() if not first else first

        for a in attrs:
            if a.name not in self.var_dims and a.name not in res and a.name not in self.fixed_local_attrs:
                if a.fixed():
                    fixed_attrs[a.name] = a.value()
                elif callable(a):
                    res.update(a(_metadata()))
                else:
                    if strict:
                        keys_strict.append(a.name)
                    else:
                        res.update(a.get(_metadata()))

        res = {k: v for k, v in res.items() if v is not None}

        # TODO: do we need a strict mode here? The extra cost has to be justified
        if keys_strict:
            assert strict
            v, _ = self.tensor.source.unique_values(keys_strict)
            res.update(v)

        self._attrs = res
        self._attrs.update(fixed_attrs)

        # extra attributes to be collected but not added to the variable
        collected_attrs = {}
        if extra_attrs:
            res = {}
            fixed_attrs = {}
            for a in extra_attrs:
                if a.fixed():
                    fixed_attrs[a.name] = a.value()
                elif callable(a):
                    res.update(a(_metadata()))
                else:
                    res.update(a.get(_metadata()))

            res = {k: v for k, v in res.items() if v is not None}
            collected_attrs = res
            collected_attrs.update(fixed_attrs)

        return {k: v for k, v in self._attrs.items() if k not in self.local_keys}, collected_attrs

    def adjust_attrs(self, drop_keys=None, rename=None):
        drop_keys = ensure_iterable(drop_keys)
        drop_keys = [k for k in drop_keys if k not in self.local_keys]
        r = {}
        for k, v in self._attrs.items():
            if k not in drop_keys:
                if isinstance(v, list) and len(v) == 1:
                    r[k] = v[0]
                else:
                    r[k] = v
        self._attrs = r
        # self._attrs = {k: v[0] for k, v in self._attrs.items() if k not in drop_keys and len(v) == 1}
        if callable(rename):
            self._attrs = rename(self._attrs)

    @property
    def attrs(self):
        return self._attrs


class TensorBackendArray(xarray.backends.common.BackendArray):
    def __init__(self, tensor, dims, shape, xp, dtype, var_name):
        super().__init__()
        self.tensor = tensor
        self.dims = dims
        self.shape = shape
        self._var_name = var_name
        self.dtype = dtype
        self.xp = xp

        from dask.utils import SerializableLock

        self.lock = SerializableLock()

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
        with self.lock:
            # LOG.debug(f"TensorBackendArray._raw_indexing_method var={self._var_name}")
            # LOG.debug(f"   dims={self.dims} key={key} shape={self.shape}")
            # LOG.debug(f"   tensor.user_coords={self.tensor.user_coords}")

            r = self.tensor[key]
            # LOG.debug(f"   cubelet user_shape={r.user_shape}")

            # LOG.debug(f"   {r.user_shape=}")
            field_index = r.field_indexes(key)
            if self.tensor.is_full_field(field_index):
                field_index = None

            # LOG.debug(f"   {field_index=}")

            try:
                result = r.to_array(index=field_index, array_backend=self.xp, dtype=self.dtype)
            except Exception as e:
                LOG.exception("Error in to_array:", e)
                raise

            # LOG.debug(f"   {result.shape=}"

            # ensure axes are squeezed when needed
            singles = [i for i in list(range(len(r.user_shape))) if isinstance(key[i], int)]
            if singles:
                result = result.squeeze(axis=tuple(singles))

            return result


class BackendDataBuilder(metaclass=ABCMeta):
    def __init__(self, ds, profile, dims, grid=None, fixed_local_attrs=None):
        self.ds = ds
        self.profile = profile
        self.dims = dims

        self.flatten_values = profile.flatten_values

        # Array backend/namespace
        array_backend = profile.array_backend
        if array_backend is None:
            array_backend = "numpy"

        from earthkit.utils.array import get_backend

        self.array_backend = get_backend(array_backend)
        assert self.array_backend is not None, f"Unsupported array_backend : {array_backend}"

        dtype = profile.dtype
        if dtype is None:
            dtype = "float64"
        self.dtype = self.array_backend.make_dtype(dtype)

        # Note: these coords inside the tensor are called user_coords and
        # the corresponding dims are called user_dims
        self.tensor_coords = {}

        # coords describing the field dimensions
        self.field_coords = {}

        self.fixed_local_attrs = ensure_dict(fixed_local_attrs)

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

            _dims, _vals = tensor.make_valid_datetime(self.dims)
            if _dims is not None and _vals is not None:
                self.tensor_coords["valid_time"] = Coord.make("valid_time", _vals, dims=_dims)

    def build(self):
        # we assume each variable forms a full cube
        var_builders = self.pre_build_variables()

        # build variable and global attributes
        xr_attrs = self.profile.attrs.builder.build(self.ds, var_builders, rename=True)
        xr_coords = self.coords()

        # build variables
        xr_vars = {
            self.profile.variable.rename(k): v.build(add_earthkit_attrs=self.profile.add_earthkit_attrs)
            for k, v in var_builders.items()
        }

        # build dataset
        dataset = xarray.Dataset(xr_vars, coords=xr_coords, attrs=xr_attrs)

        dataset = self.profile.rename_dataset_dims(dataset)

        # dim_map = self.profile.rename_dims_map()
        # if dim_map:
        #     d = {k: v for k, v in dim_map.items() if k in dataset.dims}
        #     if d:
        #         dataset = dataset.rename(d)

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
        tensor_dims, tensor_coords, tensor_coords_component, tensor_extra_attrs = self.prepare_tensor(
            ds_var, dims, name
        )

        tensor_dim_keys = [d.key for d in tensor_dims]

        # LOG.debug(f"{tensor_dims=} {tensor_coords=} {tensor_coords_component=} {tensor_extra_attrs=}")
        # LOG.debug(f"{tensor_dim_keys=}")

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
                d.key, tensor.user_coords[d.key], tensor_coords_component.get(d.key, None), tensor.source
            )
            if k not in self.tensor_coords:
                self.tensor_coords[k] = c
            var_dims.append(k)
        var_dims.extend(tensor.field_dims)

        self.collect_date_coords(tensor)
        data_maker = self.build_values
        remapping = self.profile.remapping.build()

        var_builder = VariableBuilder(
            name,
            var_dims,
            data_maker,
            tensor,
            remapping,
            local_attr_keys=tensor_extra_attrs,
            fixed_local_attrs=self.fixed_local_attrs,
        )

        return var_builder

    def prepare_tensor(self, ds, dims, name):
        tensor_dims = []
        tensor_coords = {}
        tensor_coords_component = {}
        tensor_extra_attrs = []

        # LOG.debug(f"{name=} {dims=}")

        vals, component_vals = ds.unique_values(
            [d.key for d in dims], component=self.profile.add_earthkit_attrs
        )

        # LOG.debug(f"unique_values={vals}")
        # LOG.debug(f"ensure_dims={self.profile.dims.ensure_dims}")
        # LOG.debug(f"dims_as_attrs={self.profile.dims.dims_as_attrs}")

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
                        f"Dimension '{d.name}' of variable '{name}' cannot have multiple values={vals[d.key]}"
                    )
                elif num == 1 and d.name in self.profile.dims.dims_as_attrs:
                    tensor_extra_attrs.append(d.key)
                elif num > 1 or not self.profile.dims.squeeze or d.name in self.profile.dims.ensure_dims:
                    tensor_dims.append(d)
                    tensor_coords[d.key] = vals[d.key]
                    if component_vals and d.key in component_vals:
                        tensor_coords_component[d.key] = component_vals[d.key]

                    # check if the dims/coords are consistent with the tensors of
                    # the previous variables
                    self.check_tensor_coords(name, d.key, tensor_coords)

        # TODO:  check if fieldlist forms a full hypercube with respect to the the dims/coordinates
        return tensor_dims, tensor_coords, tensor_coords_component, tensor_extra_attrs

    def check_tensor_coords(self, var_name, coord_name, tensor_coords):
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

        if self.profile.variable.is_mono:
            name = self.profile.variable.name
            builders[name] = self.pre_build_variable(self.ds, self.dims, name)
        else:
            # we assume each variable forms a full cube
            key = self.profile.variable.key
            for name in self.profile.variable.variables:
                ds_var = self.ds.sel(**{key: name})
                builders[name] = self.pre_build_variable(ds_var, self.dims, name)

        return builders

    def build_values(self, tensor, var_dims, name):
        """Generate the data object stored in the xarray variable"""
        # There is no need for the extra structures in the wrapped source in the
        # tensor any longer. It is replaced by the original unwrapped fieldlist.
        tensor.source = tensor.source.unwrap()

        backend_array = TensorBackendArray(
            tensor,
            var_dims,
            tensor.full_shape,
            self.array_backend.namespace,
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

        if self.profile.variable.is_mono:
            name = self.profile.variable.name
            builders[name] = self.pre_build_variable(self.ds, self.dims, name)
        else:
            groups = self.ds.group(self.profile.variable.key, self.profile.variable.variables)

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

        return tensor.to_array(dtype=self.dtype, array_backend=self.array_backend)


class DatasetBuilder:
    def __init__(
        self,
        ds,
        profile,
        backend_kwargs=None,
    ):
        self.ds = ds
        backend_kwargs = ensure_dict(backend_kwargs)
        assert "profile" not in backend_kwargs

        if isinstance(profile, Profile):
            self.profile = profile
        else:
            self.profile = Profile.make(profile, **backend_kwargs)

        backend_kwargs = ensure_dict(backend_kwargs)
        self.profile_kwargs = dict(**backend_kwargs)

        # LOG.debug(f"{self.profile.name=}")
        # LOG.debug(f"{backend_kwargs=}")
        if self.profile.lazy_load:
            self.builder = TensorBackendDataBuilder
        else:
            self.builder = MemoryBackendDataBuilder

        self.split_dims = self.profile.dims.split_dims
        self.direct_backend = self.profile.direct_backend

        self.grids = {}

    def parse(self, ds, profile=None, full=False):
        assert not hasattr(ds, "_ek_builder")
        from .fieldlist import XArrayInputFieldList

        if profile is None:
            profile = self.profile.copy()

        remapping = profile.remapping.build()

        # LOG.debug(f"{remapping=}")
        # LOG.debug(f"{profile.remapping=}")
        LOG.debug(f"{profile.index_keys=}")

        # create a new fieldlist for optimised access to unique values
        ds_xr = XArrayInputFieldList(
            ds, keys=profile.index_keys, remapping=remapping, component=profile.add_earthkit_attrs
        )
        # LOG.debug(f"{ds.db=}")

        # LOG.debug(f"before update: {profile.dim_keys=}")
        profile.update(ds_xr)
        # LOG.debug(f"after update: {profile.dim_keys=}")

        # LOG.debug(f"{profile.sort_keys=}")
        # the data is only sorted once
        ds_xr = ds_xr.order_by(profile.sort_keys)

        if not profile.lazy_load and profile.release_source:
            ds_xr.make_releasable()

        return ds_xr, profile

    def grid(self, ds):
        grids = ds.index("md5GridSection")

        if not grids:
            grid = "_custom_" + str(id(ds))
        else:
            # if len(grids) != 1:
            #     raise ValueError(f"Expected one grid, got {len(grids)}")
            grid = grids[0]

        key = (grid, self.profile.flatten_values)

        if key not in self.grids:
            from .grid import TensorGrid

            self.grids[key] = TensorGrid(ds[0], self.profile.flatten_values)
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
    def __init__(self, *args, backend_kwargs=None, other_kwargs=None):
        """
        split_dims: str, or iterable of str, None
            Dimension or list of dimensions to use for splitting the data into multiple hypercubes.
            Default is None.
        """
        super().__init__(*args, backend_kwargs=backend_kwargs)

        if not self.direct_backend:
            self.xr_open_dataset_kwargs = ensure_dict(other_kwargs)
            backend_kwargs = {}
            backend_kwargs["profile"] = self.profile
            self.xr_open_dataset_kwargs["backend_kwargs"] = backend_kwargs

        if not self.split_dims:
            raise ValueError("SplitDatasetMaker requires split_dims")

    def prepare(self, keys):
        from .fieldlist import XArrayInputFieldList

        remapping = self.profile.remapping.build()

        # LOG.debug(f"split_dims={self.split_dims}")
        ds_xr = XArrayInputFieldList(self.ds, keys=self.profile.index_keys, remapping=remapping)

        vals, _ = ds_xr.unique_values(keys)
        LOG.debug(f"{keys=}, {vals=}")

        return ds_xr, vals

    def build(self):
        from .splitter import Splitter

        splitter = Splitter.make(self.split_dims)
        datasets = []
        split_coords_list = []
        for ds, profile, split_coords in splitter.split(self):
            dims = profile.dims.to_list()
            split_coords_list.append(dict(split_coords))
            LOG.debug(f"splitting {dims=} type of s_ds={type(ds)} {split_coords=}")
            split_coords.pop(profile.variable.key, None)
            builder = self.builder(ds, profile, dims, grid=self.grid(ds), fixed_local_attrs=split_coords)

            ds._ek_builder = builder
            if self.direct_backend:
                datasets.append(builder.build())
            else:
                ds._ek_builder = builder
                datasets.append(xarray.open_dataset(ds, **self.xr_open_dataset_kwargs))
                ds._ek_builder = None

        return datasets, split_coords_list


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

    # certain kwargs are both backend_kwargs and other_kwargs. We need all of
    # these for the profile
    profile_kwargs = dict(**backend_kwargs)
    for k in BACKEND_AND_XR_OPEN_DS_KWARGS:
        if k in other_kwargs:
            profile_kwargs[k] = other_kwargs[k]

    # to create the profile we need all the possible backend_kwargs (bar profile)
    profile = profile_kwargs.pop("profile", Profile.DEFAULT_PROFILE_NAME)
    profile = Profile.make(profile, **profile_kwargs)

    # the backend builder is directly called bypassing xarray.open_dataset
    if profile.direct_backend:
        if not profile.dims.split_dims:
            return SingleDatasetBuilder(ds, profile).build()
        else:
            return SplitDatasetBuilder(ds, profile).build()
    # xarray.open_dataset is called
    else:
        # LOG.debug(f"from_earthkit {backend_kwargs=} {profile_kwargs=}")
        assert other_kwargs["engine"] == "earthkit"
        if not profile.dims.split_dims:
            backend_kwargs["profile"] = profile
            # certain kwargs are not allowed in xarray.open_dataset
            for k in NON_XR_OPEN_DS_KWARGS:
                backend_kwargs.pop(k, None)
            return xarray.open_dataset(ds, backend_kwargs=backend_kwargs, **other_kwargs)
        else:
            return SplitDatasetBuilder(ds, profile, other_kwargs=other_kwargs).build()
