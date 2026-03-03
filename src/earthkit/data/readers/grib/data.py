from earthkit.data.core.data import Data


class GribData(Data):
    _TYPE_NAME = "GRIB"

    def __init__(self, reader):
        self._reader = reader

    @property
    def available_types(self):
        return ["fieldlist", "xarray", "pandas", "numpy", "array"]

    def describe(self):
        return f"GRIB data from {self._reader.path}"

    def to_fieldlist(self, *args, **kwargs):
        return self._reader.to_fieldlist(*args, **kwargs)

    def to_pandas(self, **kwargs):
        return self._reader.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self._reader.to_xarray(**kwargs)

    def to_geojson(self, **kwargs):
        return self._reader.to_geojson(**kwargs)

    def to_geopandas(self, **kwargs):
        return self._conversion_not_implemented()

    def to_featurelist(self, *args, **kwargs):
        self._conversion_not_implemented()

    def to_numpy(self, *args, **kwargs):
        self._conversion_not_implemented()

    def to_array(self, *args, **kwargs):
        self._conversion_not_implemented()


class GribData1(Data):
    def __init__(self, reader, *args, **kwargs):
        self._reader = reader
        self._args = args
        self._kwargs = kwargs

    @property
    def available_types(self):
        return ["fieldlist", "xarray", "pandas", "numpy", "array"]

    def describe(self):
        pass

    def to_fieldlist(self):
        """Convert into a field list"""
        return self._reader

    def to_xarray(self, *args, **kwargs):
        """Convert into an xarray dataset"""
        self._reader.to_xarray(*args, **kwargs)

    def to_pandas(self, *args, **kwargs):
        """Convert into a pandas dataframe"""
        self._reader.to_pandas(*args, **kwargs)

    def to_geopandas(self, *args, **kwargs):
        raise NotImplementedError("Conversion of GRIB data to geopandas is not implemented")

    def to_numpy(self, *args, **kwargs):
        """Convert into a numpy array"""
        self._reader.to_numpy(*args, **kwargs)

    def to_array(self, *args, **kwargs):
        """Convert into an array (other than numpy)"""
        self._reader.to_array(*args, **kwargs)
