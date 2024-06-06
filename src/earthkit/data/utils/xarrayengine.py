# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
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
from earthkit.data.indexing.fieldlist import FieldArray
from earthkit.data.utils.diag import MemoryDiag

LOG = logging.getLogger(__name__)


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

mem = MemoryDiag("E")


class WrappedFieldList(FieldArray):
    def __init__(self, fieldlist, keys):
        super().__init__()
        self.ds = fieldlist
        self.keys = keys
        self.db = []
        self._parse()

    def _parse(self):
        for i, f in enumerate(self.ds):
            r = f._attributes(self.keys)
            self.db.append(r)
            self.append(WrappedField(None, r, self.ds, i))

    def common_attributes(self):
        if self.db:
            return {
                k: v for k, v in self.db[0].items() if all([d[k] is not None and v == d[k] for d in self.db])
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


# class FieldArray(FieldArray):
#     def __init__(self, fields=None):
#         self.fields = fields if fields is not None else []

#     def append(self, field):
#         self.fields.append(field)

#     def _getitem(self, n):
#         return self.fields[n]

#     def __len__(self):
#         return len(self.fields)

#     def __repr__(self) -> str:
#         return f"FieldArray({len(self.fields)})"


def get_metadata_keys(tag, metadata):
    if tag == "describe":
        return metadata.describe_keys()
    elif tag in DEFAULT_METADATA_KEYS:
        return DEFAULT_METADATA_KEYS[tag]
    elif tag == "":
        return []

    raise ValueError(f"Unsupported metadata tag={tag}")


class EarthkitBackendArray(xarray.backends.common.BackendArray):
    def __init__(self, ekds, dims, shape, xp):
        super().__init__()
        self.ekds = ekds
        self.dims = dims
        self.shape = shape
        self.dtype = xp.dtype(xp.float32)
        self.xp = xp

    def nbytes(self):
        from math import prod

        return prod(self.shape) * self.dtype.itemsize

    def __getitem__(self, key: xarray.core.indexing.ExplicitIndexer):
        indexing_support = indexing.IndexingSupport.BASIC
        raw_key, numpy_indices = indexing.decompose_indexer(key, self.shape, indexing_support)
        result = self._raw_indexing_method(raw_key.tuple)
        if numpy_indices.tuple:
            # index the loaded np.ndarray
            result = indexing.NdArrayLikeIndexingAdapter(result)[numpy_indices]
        return result
        # return indexing.explicit_indexing_adapter(
        #     key,
        #     self.shape,
        #     indexing.IndexingSupport.BASIC,
        #     self._raw_indexing_method,
        # )
        # bug in xarray here? tries to create a NumpyIndexingAdapter instead of NdArrayLikeIndexingAdapter
        # patched in local copy for now, but could construct this ourself

    def _raw_indexing_method(self, key: tuple):
        # must be threadsafe
        isels = dict(zip(self.dims, key))
        result = self.ekds.isel(**isels).to_numpy()
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


class EarthkitObjectBackendEntrypoint(BackendEntrypoint):
    def open_dataset(
        self,
        ekds,
        drop_variables=None,
        dims_order=None,
        array_module=numpy,
        variable_metadata_keys="describe",
        variable_index=["param", "variable"],
    ):

        mem("0")

        # get first field
        first = ekds[0]

        index_keys = first.metadata().index_keys()
        mandatory_keys = ["step"]
        for k in mandatory_keys:
            if k not in index_keys:
                index_keys.append(k)

        mem("1")
        if isinstance(variable_metadata_keys, str):
            variable_metadata_keys = get_metadata_keys(variable_metadata_keys, first.metadata())

        index_keys += [key for key in variable_metadata_keys if key not in index_keys]

        # release first field
        first = None

        # create new fieldlist and ensures all the required metadata is kept in memory
        ds = WrappedFieldList(ekds, index_keys)

        # print("meta size=", sys.getsizeof(ds[0]._meta))

        mem("2")
        # print(f"variable_metadata_keys: {variable_metadata_keys}")
        attributes = ds.common_attributes()

        mem("3")
        LOG.info(f"{attributes=}")

        if hasattr(ekds, "path"):
            attributes["ekds_source"] = ekds.path

        # print(f"attributes: {attributes}")

        vars = {}
        for var_index in variable_index:
            variables = ekds.index(var_index)
            if len(variables) > 0:
                var_key = var_index
                break
        if drop_variables is not None:
            variables = [var for var in variables if var not in drop_variables]

        mem("4")

        # print(f"variables: {variables}")
        ekds.index("step")  # have to access this to make it appear below in indices()
        if dims_order is None:
            other_dims = [key for key in ekds.indices(squeeze=True).keys() if key != var_key]
        else:
            other_dims = dims_order

        mem("5")

        # print(f"other_dims: {other_dims} var_key: {var_key}")

        for variable in variables:
            mem(f"{variable}->")
            ekds_variable = ds.sel(**{var_key: variable})
            ek_variable = ekds_variable.to_tensor(*other_dims)
            dims = [key for key in ek_variable.coords.keys() if key != var_key]
            mem(" A ")
            # print(f"variable: {variable} dims: {dims}")

            backend_array = EarthkitBackendArray(ek_variable, dims, ek_variable.shape, array_module)
            mem(" B ")
            data = indexing.LazilyIndexedArray(backend_array)
            mem(" C ")

            # Get metadata keys which are common for all fields, and not listed in dataset attrs

            kk = [k for k in variable_metadata_keys if k not in attributes]
            var_attrs = ds.common_attributes_other(ek_variable.source, kk)

            # var_attrs = _get_common_attributes(
            #     ek_variable.source,
            #     [k for k in variable_metadata_keys if k not in attributes],
            # )

            mem(" D ")
            # print(f"var_attrs: {var_attrs}")

            # if hasattr(ekds_variable[0], "_offset") and hasattr(ekds, "path"):
            #     var_attrs["metadata"] = (
            #         "grib_handle",
            #         ekds.path,
            #         ekds_variable[0]._offset,
            #     )
            # else:
            #     var_attrs["metadata"] = ("id", id(ekds_variable[0].metadata()))

            # print(f" -> var_attrs: {var_attrs}")

            # Corentin method:
            # var_attrs["metadata"] = ekds_variable[0].metadata()
            var = xarray.Variable(dims, data, attrs=var_attrs)
            vars[variable] = var

            mem(f"{variable} <-")

        # print(f"coords: {ek_variable.coords} attributes: {attributes}")
        dataset = xarray.Dataset(vars, coords=ek_variable.coords, attrs=attributes)

        return dataset

    @classmethod
    def guess_can_open(cls, ek_object):
        return isinstance(ek_object, Base)


class EarthkitBackendEntrypoint(EarthkitObjectBackendEntrypoint):
    def open_dataset(
        self,
        filename_or_obj,
        drop_variables=None,
        dims_order=None,
        array_module=numpy,
        variable_metadata_keys=[],
    ):
        if isinstance(filename_or_obj, Base):
            ekds = filename_or_obj
        elif isinstance(filename_or_obj, str):  # TODO: Add Path? or handle with try statement
            ekds = from_source("file", filename_or_obj)
        else:
            ekds = from_object(filename_or_obj)

        return EarthkitObjectBackendEntrypoint.open_dataset(
            self,
            ekds,
            drop_variables=drop_variables,
            dims_order=dims_order,
            array_module=array_module,
            variable_metadata_keys=variable_metadata_keys,
        )

    @classmethod
    def guess_can_open(cls, filename_or_obj):
        return True  # filename_or_obj.endswith(".grib")


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
