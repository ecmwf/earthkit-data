# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from .. import Reader
from .fieldlist import NetCDFFieldListFromFile
from .fieldlist import NetCDFFieldListFromURL


class NetCDFFieldListReader(NetCDFFieldListFromFile, Reader):
    def __init__(self, source, path):
        Reader.__init__(self, source, path)
        NetCDFFieldListFromFile.__init__(self, path)

    def __repr__(self):
        return "NetCDFFieldListReader(%s)" % (self.path,)

    # def mutate_source(self):
    #     # A NetCDFReader is a source itself
    #     return self


class NetCDFFieldListUrlReader(NetCDFFieldListFromURL, Reader):
    def __init__(self, source, url):
        Reader.__init__(self, source, url)
        NetCDFFieldListFromURL.__init__(self, url)

    def __repr__(self):
        return "NetCDFFieldListUrlReader(%s)" % (self.path,)

    # def mutate_source(self):
    #     # A NetCDFReader is a source itself
    #     return self


class NetCDFReader(Reader):
    def __init__(self, source, path):
        Reader.__init__(self, source, path)

    def __repr__(self):
        return "NetCDFReader(%s)" % (self.path,)

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
    def to_xarray_multi_from_paths(cls, paths, **kwargs):
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


def _match_magic(magic, deeper_check):
    if magic is not None:
        type_id = (b"\x89HDF", b"CDF\x01", b"CDF\x02")
        return len(magic) >= 4 and magic[:4] in type_id
    return False


def reader(source, path, *, magic=None, deeper_check=False, **kwargs):
    if _match_magic(magic, deeper_check):
        fs = NetCDFFieldListReader(source, path)
        if fs.has_fields():
            return fs
        else:
            return NetCDFReader(source, path)
