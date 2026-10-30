# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import inspect

try:
    import ecmwf.opendata
except ImportError:
    raise ImportError("ECMWF Open Data access requires 'ecmwf-opendata' to be installed")

from earthkit.data.utils.request import FileRequestRetriever, RequestBuilder

from .file import FileSource

# Parameters of ecmwf.opendata.Client that are not treated as generic client options: "source",
# "model" and "resol" are explicit arguments of the retriever.
_NON_CLIENT_OPTIONS = ("self", "source", "model", "resol")


def _client_option_names():
    """Return the names of the ``ecmwf.opendata.Client`` options accepted as keyword arguments."""
    sig = inspect.signature(ecmwf.opendata.Client.__init__)
    return {
        name
        for name, p in sig.parameters.items()
        if name not in _NON_CLIENT_OPTIONS and p.kind not in (p.VAR_POSITIONAL, p.VAR_KEYWORD)
    }


class EODRetriever(FileSource):
    sphinxdoc = """
    EODRetriever
    """

    def __init__(self, *args, source="ecmwf", model="ifs", resol="0p25", request=None, **kwargs):
        super().__init__()

        # Top level keyword arguments matching an ecmwf.opendata.Client option are passed
        # to the client and are not part of the request.
        option_names = _client_option_names()
        client_kwargs = {k: kwargs.pop(k) for k in list(kwargs) if k in option_names}
        client_kwargs.setdefault("preserve_request_order", True)

        request_builder = RequestBuilder(self, *args, request=request, **kwargs)
        self.request = request_builder.requests

        self.client = ecmwf.opendata.Client(source=source, model=model, resol=resol, **client_kwargs)

        # Download each request in parallel when the config allows it
        retriever = FileRequestRetriever(self, retriever=self._retrieve_one)
        self.path = retriever.retrieve(self.request)

    def _retrieve_one(self, request, *args):
        def retrieve(target, request):
            self.client.retrieve(request, target)

        # we use hash_extra here to ensure that two ecmwf-open-data requests that differ only by model,
        # source, resolution or by a client option changing the retrieved data resolve to different cache files.
        # Transport-only client options (retries, verify, etc.) are deliberately not included.
        hash_extra = {
            "model": self.client.model,
            "resol": self.client.resol,
            "source_url": self.client.source.url,
            "beta": self.client.beta,
            "infer_stream_keyword": self.client.infer_stream_keyword,
            "preserve_request_order": self.client.preserve_request_order,
        }
        return self._cache_file(retrieve, request, hash_extra=hash_extra)


source = EODRetriever
