# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.core import Encodable
from earthkit.data.sources import Source

from .core import CovJsonReaderBase


class XarrayMixIn:
    def to_xarray(self, **kwargs):
        try:
            from covjsonkit.api import Covjsonkit
        except ImportError:
            raise ImportError("covjson handling requires 'covjsonkit' to be installed")

        decoder = Covjsonkit().decode(self._json())
        return decoder.to_xarray()


class GeojsonMixIn:
    def to_geojson(self, **kwargs):
        try:
            from covjsonkit.api import Covjsonkit
        except ImportError:
            raise ImportError("covjson handling requires 'covjsonkit' to be installed")

        decoder = Covjsonkit().decode(self._json())
        return decoder.to_geojson()


class CovjsonReader(XarrayMixIn, GeojsonMixIn, CovJsonReaderBase):
    def __init__(self, source, path):
        CovJsonReaderBase.__init__(self, source, path)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path})"

    # def mutate_source(self):
    #     # A Covjson is a source itself
    #     return self

    def _json(self):
        import json

        with open(self.path, "r") as f:
            d = json.load(f)
            return d

    def is_streamable_file(self):
        return True

    def to_data_object(self):
        from earthkit.data.data.covjson import CovjsonData

        return CovjsonData(self)

    def _encode_default(self, encoder, **kwargs):
        return encoder._encode_xarray(self.to_xarray(), **kwargs)


class CovjsonStreamReader(Source, CovJsonReaderBase):
    def __init__(self, stream):
        CovJsonReaderBase.__init__(self, self, "")
        self._stream = stream

    def __iter__(self):
        return self

    def __next__(self):
        import json

        d = self._stream.read()
        if d:
            return CovjsonInMemory(json.loads(d))
        else:
            raise StopIteration

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def mutate_source(self):
        # A Covjson is a source itself
        return self

    def to_data_object(self):
        from earthkit.data.data.stream import StreamIteratorData

        return StreamIteratorData(self, "covjson")

    def is_stream(self):
        return True

    def _encode_default(self, encoder, **kwargs):
        return encoder._encode_xarray(self.to_xarray(), **kwargs)


class CovjsonMemoryReader(Source):
    def __init__(self, buf):
        self.buf = buf

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def mutate_source(self):
        import json

        return CovjsonInMemory(json.loads(self.buf))

    @staticmethod
    def _from_stream(stream):
        d = stream.read()
        return CovjsonMemoryReader(d)

    def to_data_object(self):
        from earthkit.data.data.covjson import CovjsonData

        return CovjsonData(self)

    # def _encode_default(self, encoder, **kwargs):
    #     return encoder._encode_xarray(self.to_xarray(), **kwargs)


class CovjsonInMemory(Source, XarrayMixIn, Encodable):
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return f"{self.__class__.__name__}"

    # def mutate_source(self):
    #     # A Covjson is a source itself
    #     return self

    def _json(self):
        return self.data

    def to_data_object(self):
        from earthkit.data.data.covjson import CovjsonData

        return CovjsonData(self)

    def to_target(self, target, *args, **kwargs):
        from earthkit.data.targets import to_target

        to_target(target, *args, data=self, **kwargs)

    def _default_encoder(self):
        return "covjson"

    def _encode(self, encoder, *, hints=None, **kwargs):
        return encoder._encode_xarray(self.to_xarray(), **kwargs)

    def _encode_default(self, encoder, **kwargs):
        return encoder._encode_xarray(self.to_xarray(), **kwargs)
