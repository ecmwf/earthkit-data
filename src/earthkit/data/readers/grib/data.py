from earthkit.data.data import SimpleData


class GribData(SimpleData):
    _TYPE_NAME = "GRIB"

    def __init__(self, reader):
        self._reader = reader

    @property
    def available_types(self):
        return [self._FIELDLIST, self._PANDAS, self._XARRAY, self._NUMPY, self._ARRAY]

    def describe(self):
        return f"GRIB data from {self._reader.path}"

    def to_fieldlist(self, *args, **kwargs):
        return self._reader.to_fieldlist(*args, **kwargs)

    def to_pandas(self, **kwargs):
        return self._reader.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self._reader.to_xarray(**kwargs)

    def to_numpy(self, *args, **kwargs):
        return self._reader.to_numpy(*args, **kwargs)

    def to_array(self, *args, **kwargs):
        return self._reader.to_array(*args, **kwargs)
