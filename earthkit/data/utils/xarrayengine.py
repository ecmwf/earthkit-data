import numpy
import xarray
import xarray.core.indexing as indexing
from xarray.backends import BackendEntrypoint

from earthkit.data import from_source, from_object
from earthkit.data.readers.netcdf import get_fields_from_ds, XArrayField
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
        print(f"Loaded {self.xp.__name__} with shape: {result.shape}")

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
            variable_metadata_keys = None
        ):

        if variable_metadata_keys is None:
            variable_metadata_keys = ekds[0].metadata().describe_keys()
        elif isinstance(variable_metadata_keys, str):
            variable_metadata_keys = DEFAULT_METADATA_KEYS[variable_metadata_keys]
            
        xp = array_module
        print(xp)

        attributes = _get_common_attributes(ekds.metadata(), ekds._default_ls_keys())
        if hasattr(ekds, "path"):
            attributes["ekds_source"] = ekds.path

        vars = {}
        params = ekds.index("param")

        ekds.index("step")  # have to access this to make it appear below in indices()
        if dims_order is None:
            other_dims = [
                key for key in ekds.indices(squeeze=True).keys() if key != "param"
            ]
        else:
            other_dims = dims_order

        for param in params:
            ekds_param = ekds.sel(param=param)

            ek_param = ekds_param.to_tensor(*other_dims)
            dims = [key for key in ek_param.coords.keys() if key != "param"]

            backend_array = EarthkitBackendArray(ek_param, dims, ek_param.shape, xp)
            data = indexing.LazilyIndexedArray(backend_array)
            
            var_attrs = _get_common_attributes(
                ek_param.source.metadata(), [k for k in variable_metadata_keys if k not in attributes]
            )
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
        variable_metadata_keys = None
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


@xarray.register_dataset_accessor("to_grib")
class GribSaver:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def __call__(self, filename):
        assert "ekds" in self._obj.attrs, "Dataset was not opened with earthkit backend"
        ekds = self._obj.attrs["ekds"]
        ekds.save(filename)

from itertools import product


@xarray.register_dataset_accessor("to_fieldlist")
class FieldListMutator:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def __call__(self, metadata=None):
        field_list = get_fields_from_ds(self._obj, XArrayField)
        print(field_list)

        ds = self._obj 

        field_list = []
        for var in ds.variables:
            da = ds[var]
            print(da)
            print(da.attrs)
            if "metadata" not in da.attrs:
                raise ValueError("Metadata object not found in variable. Required for conversion to field list!")
            metadata = da.attrs.get("metadata", {})
            dims = [dim for dim in da.dims if dim not in ["values", "X", "Y", "lat", "lon"]]
            coords = {key: value for key, value in da.coords.items() if key in dims}

            print(coords)
            for values in product(coords):
                print(values)
                # slices = []
                # for value, coordinate in zip(values, coordinates):
                #     slices.append(coordinate.make_slice(value))

                # if check_only:
                #     return True

                # fields.append(field_type(ds, name, slices, non_dim_coords))