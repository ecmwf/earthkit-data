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

from . import Source

LOG = logging.getLogger(__name__)


class FDBSource(Source):
    def __init__(self, *args, stream=True, **kwargs):
        super().__init__()

        for k in ["group_by", "batch_size"]:
            if k in kwargs:
                raise ValueError(f"Invalid argument '{k}' for FDBSource. Deprecated since 0.8.0.")

        self._stream_kwargs = dict()
        for k in ["read_all"]:
            if k in kwargs:
                self._stream_kwargs[k] = kwargs.pop(k)

        self.stream = stream

        self.request = {}
        for a in args:
            self.request.update(a)
        self.request.update(kwargs)

        fdb5_home = os.environ.get("FDB5_HOME", None)
        fdb5_conf = os.environ.get("FDB5_CONFIG", None)
        fdb5_config_file = os.environ.get("FDB5_CONFIG_FILE", None)
        if fdb5_home is None and (fdb5_conf is None and fdb5_config_file is None):
            raise ValueError(
                """FDB5_HOME and either FDB5_CONFIG or FDB5_CONFIG_FILE need to be set.
                See: https://fields-database.readthedocs.io for details about FDB."""
            )

    def mutate(self):
        if self.stream:
            stream = pyfdb.retrieve(self.request)
            return StreamSource(stream, **self._stream_kwargs)
        else:
            return FDBFileSource(self.request)


class FDBFileSource(FileSource):
    def __init__(self, request):
        super().__init__()
        self.path = self._retrieve(request)

    def _retrieve(self, request):
        def retrieve(target, request):
            with open(target, "wb") as o, pyfdb.retrieve(request) as i:
                shutil.copyfileobj(i, o)

        return self.cache_file(
            retrieve,
            request,
        )


source = FDBSource
