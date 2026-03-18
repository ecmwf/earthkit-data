# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


try:
    import ecmwf.opendata
except ImportError:
    raise ImportError("ECMWF Open Data access requires 'ecmwf-opendata' to be installed")

from earthkit.data.utils.request import FileRequestRetriever
from earthkit.data.utils.request import RequestBuilder

from .file import FileSource


class EODRetriever(FileSource):
    sphinxdoc = """
    EODRetriever
    """

    def __init__(self, *args, source="ecmwf", model="ifs", request=None, **kwargs):
        super().__init__()

        request_builder = RequestBuilder(self, *args, request=request, **kwargs)
        self.request = request_builder.requests

        # self.source_kwargs = self.request(**kwargs)

        self.client = ecmwf.opendata.Client(source=source, model=model, preserve_request_order=True)

        # Download each request in parallel when the config allows it
        retriever = FileRequestRetriever(self, retriever=self._retrieve_one)
        self.path = retriever.retrieve(self.request)

    def connect_to_mirror(self, mirror):
        return mirror.connection_for_eod(self)

    def _retrieve_one(self, request, *args):
        def retrieve(target, request):
            self.client.retrieve(request, target)

        return self.cache_file(
            retrieve,
            request,
        )


source = EODRetriever
