# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.readers import Reader
from earthkit.data.sources import Source


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


class CovjsonReader(XarrayMixIn, GeojsonMixIn, Reader):
    def __init__(self, source, path):
        super().__init__(source, path)

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


class CovjsonStreamReader(Source, Reader):
    def __init__(self, stream):
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


class CovjsonMemoryReader(Reader):
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


class CovjsonInMemory(Source, XarrayMixIn, Reader):
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
