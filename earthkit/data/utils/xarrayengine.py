import numpy
import xarray
import xarray.core.indexing as indexing
from xarray.backends import BackendEntrypoint
from itertools import product

from earthkit.data import from_source, from_object, FieldList
from earthkit.data.readers.netcdf import get_fields_from_ds
from earthkit.data.core import Base


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
    if tag =='describe':
        return metadata.describe_keys()
    
    if tag in DEFAULT_METADATA_KEYS:
        return DEFAULT_METADATA_KEYS[tag]
    
    print("Metadata tag not recognised, not adding any metadata to variables")
    return []


class EarthkitBackendArray(xarray.backends.common.BackendArray):
    def __init__(self, ekds, dims, shape, xp):
        super().__init__()
        self.ekds = ekds
        self.dims = dims
        self.shape = shape
        self.dtype = xp.float32
        self.xp = xp

    def __getitem__(self, key: xarray.core.indexing.ExplicitIndexer):
        indexing_support = indexing.IndexingSupport.BASIC
        raw_key, numpy_indices = indexing.decompose_indexer(
            key, self.shape, indexing_support
        )
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


def _get_common_attributes(metadata, keys):
    common_entries = {}
    if len(metadata) > 0:
        common_entries = {key: metadata[0][key] for key in keys if key in metadata[0]}
        for dictionary in metadata[1:]:
            common_entries = {
                key: value
                for key, value in common_entries.items()
                if key in dictionary and common_entries[key] == dictionary[key]
            }
    return common_entries


class EarthkitObjectBackendEntrypoint(BackendEntrypoint):
    def open_dataset(
            self, ekds, drop_variables=None, dims_order=None, array_module=numpy,
            variable_metadata_keys = None, variable_index = ["param", "variable"]
        ):

        if isinstance(variable_metadata_keys, str):
            variable_metadata_keys = get_metadata_keys(variable_metadata_keys, ekds[0].metadata())
            
        xp = array_module

        attributes = _get_common_attributes(ekds.metadata(), ekds._default_ls_keys())
        if hasattr(ekds, "path"):
            attributes["ekds_source"] = ekds.path

        vars = {}
        for var_index in variable_index:
            params = ekds.index(var_index)
            if len(params) > 0:
                var_key = var_index
                break

        ekds.index("step")  # have to access this to make it appear below in indices()
        if dims_order is None:
            other_dims = [
                key for key in ekds.indices(squeeze=True).keys() if key != "param"
            ]
        else:
            other_dims = dims_order

        for param in params:
            ekds_param = ekds.sel(**{var_key: param})
            ek_param = ekds_param.to_tensor(*other_dims)
            dims = [key for key in ek_param.coords.keys() if key != "param"]

            backend_array = EarthkitBackendArray(ek_param, dims, ek_param.shape, xp)
            data = indexing.LazilyIndexedArray(backend_array)
            
            # Get metadata keys which are common for all fields, and not listed in dataset attrs
            var_attrs = _get_common_attributes(
                ek_param.source.metadata(), [k for k in variable_metadata_keys if k not in attributes]
            )
            var_attrs = {"metadata": ekds[0].metadata()}
            var = xarray.Variable(dims, data, attrs=var_attrs)
            vars[param] = var

        dataset = xarray.Dataset(vars, coords=ek_param.coords, attrs=attributes)

        return dataset

    @classmethod
    def guess_can_open(cls, ek_object):
        return isinstance(ek_object, Base)


class EarthkitBackendEntrypoint(EarthkitObjectBackendEntrypoint):
    def open_dataset(
        self, filename_or_obj, drop_variables=None, dims_order=None, array_module=numpy,
        variable_metadata_keys = []
    ):
        if isinstance(filename_or_obj, Base):
            ekds = filename_or_obj
        elif isinstance(filename_or_obj, str):  # TODO: Add Path? or handle with try statement
            ekds = from_source("file", filename_or_obj)
        else:
            ekds = from_object(filename_or_obj)

        return EarthkitObjectBackendEntrypoint.open_dataset(
            self, ekds, drop_variables=drop_variables, dims_order=dims_order, array_module=array_module,
            variable_metadata_keys=variable_metadata_keys
        )
    
    @classmethod
    def guess_can_open(cls, filename_or_obj):
        return True #  filename_or_obj.endswith(".grib")


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
            raise ValueError("Earthkit attribute not found in DataArray. Required for conversion to FieldList!")
        
        metadata = metadata.override(**local_coords)
        data_list.append(xa_field.values)
        metadata_list.append(metadata)
    return data_list, metadata_list


class XarrayEarthkit():
    def to_grib(self, filename):
        fl = self.to_fieldlist()
        fl.save(filename)


@xarray.register_dataarray_accessor("earthkit")
class XarrayEarthkitDataArray(XarrayEarthkit):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    @property
    def metadata(self):
        return self._obj.attrs.get("metadata", None)

    @metadata.setter
    def metadata(self, value):
        self._obj.attrs["metadata"] = value

    @metadata.deleter
    def metadata(self):
        self._obj.attrs.pop("metadata", None)

    def to_fieldlist(self):
        data_list, metadata_list = data_array_to_list(self._obj)
        field_list = FieldList.from_numpy(numpy.array(data_list), metadata_list)
        return field_list


@xarray.register_dataset_accessor("earthkit")
class XarrayEarthkitDataSet(XarrayEarthkit):
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

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
