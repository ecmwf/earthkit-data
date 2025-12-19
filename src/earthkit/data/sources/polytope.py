# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

try:
    import polytope
except ImportError:
    raise ImportError("Polytope access requires 'polytope-client' to be installed")

from earthkit.data.utils.request import RequestBuilder

from . import Source
from .file import File
from .prompt import APIKeyPrompt
from .url import Url
from .url import download_to_target

LOG = logging.getLogger(__name__)


class PolytopeWebKeyPrompt(APIKeyPrompt):
    register_or_sign_in_url = ("",)
    retrieve_api_key_url = ("",)
    prompts = [
        dict(name="user_email", title="Your email"),
        dict(
            name="user_key",
            example="b295aad8af30332fad2fa8c963ab7900",
            title="API key",
            hidden=True,
            validate="[0-9a-z]{32}",
        ),
    ]

    rcfile = "~/.polytopeapirc"
    config_env = ("POLYTOPE_USER_EMAIL", "POLYTOPE_USER_KEY")


class Polytope(Source):
    """Retrieve data using the Polytope Web API.
    See polytope-client.readthedocs.io for more information.

    Parameters
    ----------
    dataset : str
        The name of the dataset to query.
    request: dict[str, str]
        A collection of key : value pairs specifying the dataset.

    Examples
    --------
    >>> src = earthkit.data.from_source("polytope", "ecmwf-mars", request)
    >>> src.to_pandas()  # if tabular data
    >>> src.to_xarray()  # if datacube
    """

    def __init__(
        self,
        dataset,
        *args,
        request=None,
        stream=True,
        **kwargs,
    ) -> None:
        super().__init__()
        assert isinstance(dataset, str)

        for k in ["group_by", "batch_size"]:
            if k in kwargs:
                raise ValueError(f"Invalid argument '{k}' for Polytope. Deprecated since 0.8.0.")

        self._stream_kwargs = dict()
        for k in ["read_all"]:
            if k in kwargs:
                self._stream_kwargs[k] = kwargs.pop(k)

        self.stream = stream
        self.dataset = dataset

        request_builder = RequestBuilder(self, *args, request=request)
        self.request = request_builder.requests

        # all the kwargs are passed to the client!
        self.client = polytope.api.Client(**kwargs)

    def __repr__(self) -> str:
        r = f"{self.__class__.__name__}({self.dataset}"
        if len(self.request) == 1:
            r += f", request={self.request[0]}"
        else:
            r += f", request={self.request}"
        r += ")"
        return r

    def mutate(self) -> Source:
        if self.stream:
            return self._mutate_stream()
        else:
            return self._retrieve()

    def _mutate_stream(self) -> Source:
        if len(self.request) != 1:
            raise ValueError("Polytope stream access only supports a single request at the moment")

        pointers = self.client.retrieve(
            self.dataset,
            self.request[0],
            pointer=True,
            asynchronous=False,
        )

        urls = [p["location"] for p in pointers]
        LOG.debug(f"{urls=}")

        return Url(
            urls,
            stream=True,
            **self._stream_kwargs,
        )

    def _retrieve(self) -> Source:
        from earthkit.data.utils.request import FileRequestRetriever

        def _retrieve_one(request, dataset):
            """Retrieve a single request and cache the result."""

            def retrieve(target, args):
                """
                Caching callback method to retrieve data into target file. Only called if
                the data is not already cached.
                """
                # get the pointer and the url to download
                pointers = self.client.retrieve(
                    args[0],
                    args[1],
                    pointer=True,
                    asynchronous=False,
                )

                url = pointers[0]["location"]

                # download the file and return the associated HTTP header info.
                # This might contain useful info such as content-type. It will be
                # stored in the cache database.
                return download_to_target(url, target)

            # The cache file path/data is constructed by using the request only. We cannot simply base
            # it on the URL since the URL may change every time we ask for the pointers.
            return self.cache_file(
                retrieve,
                (dataset, request),
            )

        # Download each request in parallel when the config allows it
        retriever = FileRequestRetriever(self, retriever=_retrieve_one)
        path = retriever.retrieve(self.request, self.dataset)

        # TODO: for simplicity we assume all retrieved files have the same content-type. Revisit if needed.
        content_type = None
        if path:
            from earthkit.data.core.caching import CACHE

            # fetch the content-type from the cache entry
            data = CACHE._get_entry(path[0])
            if data:
                content_type = data.get("owner_data", {}).get("content-type")

        src = File(path)
        src.content_type = content_type
        return src


source = Polytope
