# (C) Copyright 2025- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.sources import Source

from .core import PPReaderBase


class PPReader(Source, PPReaderBase):
    def __init__(self, source, path, **kwargs):
        PPReaderBase.__init__(self, source, path)

    def mutate_source(self):
        return self

    def to_fieldlist(self, *args, **kwargs):
        from .fieldlist import PPFieldList

        return PPFieldList(self, self.path, **kwargs)

    def to_xarray(self, **kwargs):
        return self._open_pp(**kwargs)

    def __repr__(self):
        return f"PPReader({self.path})"

    def to_data_object(self):
        from earthkit.data.data.pp import PPData

        return PPData(self)

    @classmethod
    def merge(cls, sources):
        raise NotImplementedError

    def _encode_default(self, encoder, *args, **kwargs):
        return encoder._encode_xarray(self.to_xarray(), *args, **kwargs)
