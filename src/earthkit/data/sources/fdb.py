# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import inspect
import logging
import os
import shutil
import warnings

try:
    import pyfdb
except ImportError:
    raise ImportError("FDB access requires 'pyfdb' to be installed")

from earthkit.data.sources.file import FileSource
from earthkit.data.sources.stream import StreamSource
from earthkit.data.utils.request import RequestBuilder, RequestMapper

from . import Source

LOG = logging.getLogger(__name__)


class FDBSource(Source):
    # pyfdb renamed the "userconfig" option of FDB() to "user_config". True when the
    # installed pyfdb uses the new name. Lazily determined by _use_user_config_option().
    _has_user_config_option = None

    def __init__(
        self, *args, request=None, stream=True, config=None, userconfig=None, user_config=None, lazy=False, **kwargs
    ):
        super().__init__()

        for k in ["group_by", "batch_size"]:
            if k in kwargs:
                raise ValueError(f"Invalid argument '{k}' for FDBSource. Deprecated since 0.8.0.")

        if userconfig is not None and user_config is not None:
            raise ValueError("Specify only one of 'userconfig' or 'user_config', not both.")

        if userconfig is not None:
            warnings.warn(
                "'userconfig' is deprecated, use 'user_config' instead",
                DeprecationWarning,
                stacklevel=2,  # Point the warning at the user's call site
            )
            user_config = userconfig

        self.lazy = lazy
        self._fdb_kwargs = {}
        if config is not None:
            self._fdb_kwargs["config"] = config
        if user_config is not None:
            self._fdb_kwargs["user_config" if self._use_user_config_option() else "userconfig"] = user_config

        self._stream_kwargs = dict()
        for k in ["read_all"]:
            if k in kwargs:
                raise ValueError(f"Invalid argument '{k}' for FDBSource. Removed since 1.0.0.")

        self.stream = stream

        request_builder = RequestBuilder(self, *args, request=request, **kwargs)
        self.request = request_builder.requests

        if len(self.request) == 0:
            raise ValueError("FDBSource: no requests to process")

        if len(self.request) > 1:
            raise ValueError("FDBSource: multiple requests are not supported")

        self.request = self.request[0]

        if not (config or user_config):
            self._check_env()

    @classmethod
    def _use_user_config_option(cls):
        """Tell whether pyfdb.FDB() takes the user config as "user_config" or as "userconfig".

        Returns
        -------
        bool
            True if pyfdb.FDB() accepts "user_config" (pyfdb >= 5), False if it only
            accepts the legacy "userconfig" option.
        """
        if cls._has_user_config_option is None:
            try:
                params = inspect.signature(pyfdb.FDB.__init__).parameters
                cls._has_user_config_option = "user_config" in params
            except (TypeError, ValueError):
                # the signature is not introspectable, assume the legacy option
                cls._has_user_config_option = False

        return cls._has_user_config_option

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
                if hasattr(stream, "open") and callable(stream.open):
                    stream.open()
                return StreamSource(stream, **self._stream_kwargs)
            else:
                return FDBFileSource(fdb, self.request)
        else:
            mapper = FDBRequestMapper(self.request, fdb_kwargs=self._fdb_kwargs)
            retriever = FDBRetriever(self._fdb_kwargs)
            from earthkit.data.field.grib.virtual import VirtualGribFieldList

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

        return self._cache_file(
            retrieve,
            request,
        )


class FDBRetriever:
    def __init__(self, fdb_kwargs):
        self.fdb_kwargs = fdb_kwargs

    def get(self, request):
        from . import from_source

        return from_source("fdb", request, stream=True, **self.fdb_kwargs).to_fieldlist(read_all=True)


class FDBRequestMapper(RequestMapper):
    _CONVERT_MAP = {
        "date": int,
        "time": int,
        "step": int,
        "levelist": int,
        "level": int,
    }

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
        # check for pyfdb >=5
        has_new_api = hasattr(pyfdb, "ListElement")
        fdb = pyfdb.FDB(**self.fdb_kwargs)
        if has_new_api:
            for el in fdb.list(self.request, level=3):
                data = el.combined_key()
                r.append(self._convert(data))
        else:
            for el in fdb.list(self.request, True, True):
                data = el["keys"]
                r.append(self._convert(data))

        return r

    @staticmethod
    def _convert(data):
        for k in data:
            c = FDBRequestMapper._CONVERT_MAP.get(k, None)
            if c:
                data[k] = c(data[k])

        return data


source = FDBSource
