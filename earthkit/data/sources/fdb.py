# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import shutil

import pyfdb

from earthkit.data.sources.file import FileSource
from earthkit.data.sources.stream import StreamSource

from . import Source

LOG = logging.getLogger(__name__)


class FDBSource(Source):
    def __init__(self, *args, stream=True, **kwargs):
        super().__init__()

        self._stream_kwargs = kwargs.pop("batch_size", 1)
        self.stream = stream

        self.request = {}
        for a in args:
            self.request.update(a)
        self.request.update(kwargs)

    def mutate(self):
        if self.stream:
            stream = pyfdb.retrieve(self.request)
            return StreamSource(stream, self._stream_kwargs)
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
