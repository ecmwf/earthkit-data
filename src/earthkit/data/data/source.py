# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from . import SimpleData


class SourceData(SimpleData):
    def __init__(self, source_or_reader):
        from earthkit.data.readers import Reader
        from earthkit.data.sources import Source

        self._source = None
        self._reader = None

        if isinstance(source_or_reader, Source):
            self._source = source_or_reader
            if isinstance(source_or_reader, Reader):
                self._reader = source_or_reader
            elif hasattr(source_or_reader, "_reader") and isinstance(source_or_reader._reader, Reader):
                self._reader = source_or_reader._reader
            else:
                self._reader = self._source
        elif isinstance(source_or_reader, Reader):
            self._reader = source_or_reader
            self._source = source_or_reader.source
        else:
            raise TypeError(f"Invalid type={type(source_or_reader)}. Must be a Source or Reader")

        if self._reader is None:
            raise ValueError(f"SourceData no Source or Reader found in {source_or_reader=}")


class DefaultSourceData(SourceData):
    def __init__(self, source_or_reader):
        super().__init__(source_or_reader)
        self._types = []
        for name in [
            self._XARRAY,
            self._FIELDLIST,
            self._PANDAS,
            self._GEOPANDAS,
            self._FEATURELIST,
            self._NUMPY,
            self._ARRAY,
        ]:
            if hasattr(self._reader, f"to_{name}"):
                self._types.append(name)

    def describe(self):
        pass

    @property
    def available_types(self):
        return self._types

    def to_fieldlist(self, *args, **kwargs):
        if self._FIELDLIST in self._types:
            return getattr(self._reader, f"to_{self._FIELDLIST}")(*args, **kwargs)
        else:
            self._conversion_not_implemented()

    def to_xarray(self, *args, **kwargs):
        if self._XARRAY in self._types:
            return getattr(self._reader, f"to_{self._XARRAY}")(*args, **kwargs)
        else:
            self._conversion_not_implemented()

    def to_pandas(self, *args, **kwargs):
        if self._PANDAS in self._types:
            return getattr(self._reader, f"to_{self._PANDAS}")(*args, **kwargs)
        else:
            self._conversion_not_implemented()

    def to_geopandas(self, **kwargs):
        if self._GEOPANDAS in self._types:
            return getattr(self._reader, f"to_{self._GEOPANDAS}")(**kwargs)
        else:
            self._conversion_not_implemented()

    def to_featurelist(self, *args, **kwargs):
        if self._FEATURELIST in self._types:
            return getattr(self._reader, f"to_{self._FEATURELIST}")(*args, **kwargs)
        else:
            self._conversion_not_implemented()

    def to_numpy(self, *args, **kwargs):
        if self._NUMPY in self._types:
            return getattr(self._reader, f"to_{self._NUMPY}")(*args, **kwargs)
        else:
            self._conversion_not_implemented()

    def to_array(self, *args, **kwargs):
        if self._ARRAY in self._types:
            return getattr(self._reader, f"to_{self._ARRAY}")(*args, **kwargs)
        else:
            self._conversion_not_implemented()
