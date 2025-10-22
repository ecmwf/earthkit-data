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
    from hda.api import DataOrderRequest  # noqa
except ImportError:
    raise ImportError("WEkEO access requires 'hda' to be installed")

from earthkit.data.decorators import normalize
from earthkit.data.utils.request import FileRequestRetriever
from earthkit.data.utils.request import RequestBuilder

from .file import FileSource
from .wekeo import EXTENSIONS
from .wekeo import ApiClient as WekeoClient
from .wekeo import HDAAPIKeyPrompt

LOG = logging.getLogger(__name__)


class ApiClient(WekeoClient):
    name = "wekeocds"

    def __int__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    def retrieve(self, name, request, target=None):
        rq = {"dataset_id": name}
        rq.update(
            {
                _name: (
                    _value
                    if isinstance(_value, list) or _name in ("data_format", "download_format")
                    else [_value]
                )
                for _name, _value in request.items()
            }
        )

        if "area" in request:
            rq.update({"bbox": request["area"]})

        request["request"] = rq

        return super().retrieve(name, request, target)


class WekeoCdsRetriever(FileSource):
    sphinxdoc = """
    WekeoCdsRetriever
    """

    def __init__(self, dataset, *args, request=None, prompt=True, **kwargs):
        super().__init__()

        self.prompt = prompt

        request_builder = RequestBuilder(
            self, *args, request=request, normaliser=self._normalise_request, **kwargs
        )
        self.request = request_builder.requests

        self.client(self.prompt)  # Trigger password prompt before threading

        # Download each request in parallel when the config allows it
        retriever = FileRequestRetriever(self, retriever=self._retrieve_one)
        self.path = retriever.retrieve(self.request, dataset)

    def _retrieve_one(self, request, dataset):
        def retrieve(target, args):
            self.client(self.prompt).retrieve(args[0], args[1], target)

        return self.cache_file(
            retrieve,
            (dataset, request),
            extension=EXTENSIONS.get(request.get("format"), ".cache"),
        )

    @normalize("date", "date-list(%Y-%m-%d)")
    @normalize("area", "bounding-box(list)")
    def _normalise_request(self, **kwargs):
        return kwargs

    @staticmethod
    def client(use_prompt):
        if use_prompt:
            prompt = HDAAPIKeyPrompt()
            prompt.check()

            try:
                return ApiClient()
            except Exception as e:
                # if no rc file is available hda throws
                # ConfigurationError: Missing or incomplete configuration
                if ".hdarc" in str(e) or not prompt.has_config_env():
                    LOG.warning(e)
                    LOG.exception(f"Could not load hda client. {e}")
                    prompt.ask_user_and_save()
                    return ApiClient()
                raise
        else:
            return ApiClient()


source = WekeoCdsRetriever
