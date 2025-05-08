# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os
import shutil

try:
    import pyfdb
except ImportError:
    raise ImportError("FDB access requires 'pyfdb' to be installed")

from earthkit.data.sources.file import FileSource
from earthkit.data.sources.stream import StreamSource
from earthkit.data.utils.request import RequestMapper

from . import Source

LOG = logging.getLogger(__name__)


class FDBSource(Source):
    def __init__(self, *args, stream=True, config=None, userconfig=None, lazy=False, **kwargs):
        super().__init__()

        for k in ["group_by", "batch_size"]:
            if k in kwargs:
                raise ValueError(f"Invalid argument '{k}' for FDBSource. Deprecated since 0.8.0.")

        self.lazy = lazy
        self._fdb_kwargs = {}
        if config is not None:
            self._fdb_kwargs["config"] = config
        if userconfig is not None:
            self._fdb_kwargs["userconfig"] = userconfig

        self._stream_kwargs = dict()
        for k in ["read_all"]:
            if k in kwargs:
                self._stream_kwargs[k] = kwargs.pop(k)

        self.stream = stream

        self.request = {}
        for a in args:
            self.request.update(a)
        self.request.update(kwargs)

        if not (config or userconfig):
            self._check_env()

    def _check_env(self):
        fdb_home = os.environ.get("FDB_HOME", None)
        fdb_conf = os.environ.get("FDB5_CONFIG", None)
        if fdb_home is None and fdb_conf is None:
            raise ValueError(
                """Neither FDB_HOME nor FDB5_CONFIG environment variable
                was set! Please define either one to access FDB.
                See: https://fields-database.readthedocs.io for details about FDB."""
            )

    def mutate(self):
        if not self.lazy:
            fdb = pyfdb.FDB(**self._fdb_kwargs)
            if self.stream:
                stream = fdb.retrieve(self.request)
                return StreamSource(stream, **self._stream_kwargs)
            else:
                return FDBFileSource(fdb, self.request)
        else:
            mapper = FDBRequestMapper(self.request, fdb_kwargs=self._fdb_kwargs)
            retriever = FDBRetriever(self._fdb_kwargs)
            from earthkit.data.readers.grib.virtual import VirtualGribFieldList

            return VirtualGribFieldList(mapper, retriever)


class FDBFileSource(FileSource):
    def __init__(self, fdb, request):
        super().__init__()
        self.fdb = fdb
        self.path = self._retrieve(request)

    def _retrieve(self, request):
        def retrieve(target, request):
            with open(target, "wb") as o, self.fdb.retrieve(request) as i:
                shutil.copyfileobj(i, o)

        return self.cache_file(
            retrieve,
            request,
        )


class FDBRetriever:
    def __init__(self, fdb_kwargs):
        self.fdb_kwargs = fdb_kwargs

    def get(self, request):
        from . import from_source

        return from_source("fdb", request, stream=True, read_all=True, **self.fdb_kwargs)


class FDBRequestMapper(RequestMapper):
    def __init__(self, request, fdb_kwargs=None, **kwargs):
        super().__init__(request, **kwargs)
        self.fdb_kwargs = fdb_kwargs or {}
        self.metadata_alias = {
            "stepRange": "step",
            "typeOfLevel": "leveltype",
            "level": "levelist",
            "dataDate": "date",
            "dataTime": "time",
        }

    def _build(self):
        r = []
        fdb = pyfdb.FDB(**self.fdb_kwargs)
        for el in fdb.list(self.request, True, True):
            r.append(el["keys"])
        return r


source = FDBSource
