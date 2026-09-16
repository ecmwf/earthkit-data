# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import warnings

from earthkit.data.readers.xarray.fieldlist import XArrayFieldList

from .core import ZarrReaderBase


class ZarrReader(XArrayFieldList, ZarrReaderBase):
    def __init__(self, source, path, **kwargs):
        if kwargs:
            names = ", ".join(repr(name) for name in kwargs)
            warnings.warn(
                f"Arguments {names} have no effect for the Zarr reader.",
                UserWarning,
                stacklevel=2,
            )

        ZarrReaderBase.__init__(self, source, path)

    def mutate_source(self):
        return self

    def to_fieldlist(self, *args, **kwargs):
        from .fieldlist import ZarrFieldList

        return ZarrFieldList(self, self.path, **kwargs)

    def to_xarray(self, **kwargs):
        return self._open_zarr(**kwargs)

    def __repr__(self):
        return f"ZarrReader({self.path})"

    def to_data_object(self):
        from earthkit.data.data.zarr import ZarrData

        return ZarrData(self)

    @classmethod
    def merge(cls, sources):
        raise NotImplementedError

    def _encode_default(self, encoder, *args, **kwargs):
        return encoder._encode_xarray(self.to_xarray(), *args, **kwargs)
