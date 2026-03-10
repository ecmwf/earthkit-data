# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

from earthkit.data.sources import Source

from .core import NetCDFReaderBase
from .fieldlist import NetCDFFieldListFromFile
from .fieldlist import NetCDFFieldListFromURL


class NetCDFReader(Source, NetCDFReaderBase):
    def __init__(self, source, path):
        self._ori_source = source
        NetCDFReaderBase.__init__(self, source, path)

    def __repr__(self):
        return "NetCDFReader(%s)" % (self.path,)

    @abstractmethod
    def to_fieldlist(self):
        """Convert into a field list"""
        # return NetCDFFieldListFromFile(self._ori_source, self.path)
        pass

    def to_numpy(self, flatten=False):
        arr = self.to_xarray().to_array().to_numpy()
        if flatten:
            arr = arr.flatten()
        return arr

    def to_pandas(self):
        return self.to_xarray().to_pandas()

    def to_xarray(self, **kwargs):
        return type(self).to_xarray_multi_from_paths([self.path], **kwargs)

    @classmethod
    def to_xarray_multi_from_paths(cls, paths, *args, **kwargs):
        import xarray as xr

        if not isinstance(paths, list):
            paths = [paths]

        options = dict()
        options.update(kwargs.get("xarray_open_mfdataset_kwargs", {}))
        if not options:
            options = dict(**kwargs)

        return xr.open_mfdataset(
            paths,
            **options,
        )

    def to_data_object(self):
        from earthkit.data.data.netcdf import NetCDFData

        return NetCDFData(self)

    def mutate(self):
        return self

    def mutate_source(self):
        return self

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(s, NetCDFReader) for s in sources)
        return MultiNetCDFReader(sources)

    def _encode_default(self, encoder, **kwargs):
        return encoder._encode_xarray(self.to_xarray(), **kwargs)


class NetCDFFileReader(NetCDFReader):
    def __init__(self, source, path):
        self._ori_source = source
        # self.path = path
        super().__init__(source, path)

    def to_fieldlist(self):
        """Convert into a field list"""
        return NetCDFFieldListFromFile(self.path)

    def __repr__(self):
        return "NetCDFFileReader(%s)" % (self.path,)


class NetCDFUrlReader(NetCDFReader):
    def __init__(self, source, url):
        self._ori_source = source
        self.url = url
        super().__init__(source, "")

    def to_fieldlist(self):
        """Convert into a field list"""
        return NetCDFFieldListFromURL(self.url)

    def __repr__(self):
        return "NetCDFUrlReader(%s)" % (self.url,)

    # def to_fieldlist(self):
    #     """Convert into a field list"""
    #     return NetCDFFieldListFromURL(self.path)


class MultiNetCDFReader(NetCDFReader):
    def __init__(self, sources):
        self.sources = sources

    def to_fieldlist(self):
        from earthkit.data.mergers import make_merger

        merged = make_merger(None, self.sources).to_fieldlist()
        if merged is not None:
            return merged.mutate()

        # fs = [s.to_fieldlist() for s in self.sources]
        # from earthkit.data.mergers import merge_by_class

        # merged = merge_by_class(fs)
        # if merged is not None:
        #     return merged.mutate()

        raise NotImplementedError("Conversion of MultiNetCDFReader to fieldlist is not implemented")

    def to_xarray(self, *args, **kwargs):
        return MultiNetCDFReader.to_xarray_multi_from_paths([s.path for s in self.sources], *args, **kwargs)

    def __repr__(self):
        return "MultiNetCDFReader(%s)" % (self.sources,)

    def to_data_object(self):
        from earthkit.data.data.netcdf import NetCDFData

        return NetCDFData(self)
