# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import mimetypes
import pathlib

from earthkit.data.core.data import Data
from earthkit.data.readers import Reader


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

    def mutate_source(self):
        # A Covjson is a source itself
        return self

    def _json(self):
        import json

        with open(self.path, "r") as f:
            d = json.load(f)
            return d

    def is_streamable_file(self):
        return True

    def _to_data_object(self):
        return CovjsonData(self)


class CovjsonStreamReader(Reader):
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

    def _to_data_object(self):
        return CovjsonData(self)

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

    def _to_data_object(self):
        return CovjsonData(self)


class CovjsonInMemory(XarrayMixIn, Reader):
    def __init__(self, data):
        self.data = data

    def __repr__(self):
        return f"{self.__class__.__name__}"

    def mutate_source(self):
        # A Covjson is a source itself
        return self

    def _json(self):
        return self.data

    def _to_data_object(self):
        return CovjsonData(self)


class CovjsonData(Data):
    _TYPE_NAME = "Covjson"

    def __init__(self, reader):
        self._reader = reader

    @property
    def available_types(self):
        return ["xarray", "geojson"]

    def describe(self):
        return f"Covjson data from {self._reader.path}"

    def to_fieldlist(self, *args, **kwargs):
        return self._conversion_not_implemented()

    def to_pandas(self, **kwargs):
        return self._conversion_not_implemented()

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


def _match_content_type(content_type):
    return content_type is not None and content_type == "application/prs.coverage+json"


def _match_magic(magic, deeper_check):
    if magic is not None:
        type_id = b'{"type": "CoverageCollection"'
        if not deeper_check:
            return magic.startswith(type_id)
        else:
            return type_id in magic
    return False


def reader(source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    def _reader():
        return CovjsonReader(source, path)

    if _match_content_type(content_type) or _match_magic(magic, deeper_check):
        return _reader()

    extension = pathlib.Path(path).suffix
    if extension in [".covjson"]:
        return _reader()

    kind, _ = mimetypes.guess_type(path)
    if kind in ["application/prs.cov+json"]:
        return _reader()


def memory_reader(source, buffer, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    if _match_content_type(content_type) or _match_magic(magic, deeper_check):
        return CovjsonMemoryReader(buffer)


def stream_reader(
    source,
    stream,
    *,
    magic=None,
    deeper_check=False,
    content_type=None,
    memory=False,
    **kwargs,
):
    if _match_content_type(content_type) or _match_magic(magic, deeper_check):
        if memory:
            return CovjsonMemoryReader._from_stream(stream)
        return CovjsonStreamReader(stream)
