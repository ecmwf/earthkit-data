import numpy
import xarray
import xarray.core.indexing as indexing
from xarray.backends import BackendEntrypoint

from earthkit.data import from_source


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
        common_entries = {key: metadata[0][key] for key in keys}
        for dictionary in metadata[1:]:
            common_entries = {
                key: value
                for key, value in common_entries.items()
                if key in dictionary and common_entries[key] == dictionary[key]
            }
    return common_entries


class EarthkitBackendEntrypoint(BackendEntrypoint):
    def open_dataset(self, filename_or_obj, drop_variables=None, array_module=numpy):
        xp = array_module

        ekds = from_source("file", filename_or_obj)
        attributes = _get_common_attributes(ekds.metadata(), ekds._default_ls_keys())
        attributes["ekds"] = ekds

        vars = {}
        params = ekds.index("param")

        ekds.index("step")  # have to access this to make it appear below in indices()
        other_dims = [
            key for key in ekds.indices(squeeze=True).keys() if key != "param"
        ]

        for param in params:
            ekds_param = ekds.sel(param=param)

            ek_param = ekds_param.to_tensor(*other_dims)
            dims = [key for key in ek_param.coords.keys() if key != "param"]

            backend_array = EarthkitBackendArray(ek_param, dims, ek_param.shape, xp)
            data = indexing.LazilyIndexedArray(backend_array)

            attrs = {"metadata": ek_param.source.metadata()[0]}
            var = xarray.Variable(dims, data, attrs=attrs)
            vars[param] = var

        dataset = xarray.Dataset(vars, coords=ek_param.coords, attrs=attributes)

        return dataset

    @classmethod
    def guess_can_open(cls, filename_or_obj):
        return filename_or_obj.endswith(".grib")


@xarray.register_dataset_accessor("to_grib")
class GribSaver:
    def __init__(self, xarray_obj):
        self._obj = xarray_obj

    def __call__(self, filename):
        assert "ekds" in self._obj.attrs, "Dataset was not opened with earthkit backend"
        ekds = self._obj.attrs["ekds"]
        ekds.save(filename)
