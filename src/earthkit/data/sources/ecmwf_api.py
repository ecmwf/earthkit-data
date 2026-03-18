# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.decorators import normalize
from earthkit.data.utils.request import FileRequestRetriever
from earthkit.data.utils.request import RequestBuilder

from .file import FileSource
from .prompt import APIKeyPrompt

LOG = logging.getLogger(__name__)


class MARSAPIKeyPrompt(APIKeyPrompt):
    register_or_sign_in_url = "https://www.ecmwf.int/user/login/sso"
    retrieve_api_key_url = "https://api.ecmwf.int/v1/key/"

    prompts = [
        dict(
            name="url",
            default="https://api.ecmwf.int/v1",
            title="API url",
            validate=r"http.?://.*",
        ),
        dict(
            name="key",
            example="b295aad8af30332fad2fa8c963ab7900",
            title="API key",
            hidden=True,
            validate="[0-9a-z]{32}",
        ),
        dict(name="email", title="Your email", env="ECMWF_API_EMAIL"),
    ]

    rcfile = "~/.ecmwfapirc"
    rcfile_env = "ECMWF_API_RC_FILE"
    config_env = ("ECMWF_API_KEY", "ECMWF_API_URL")


class ECMWFApi(FileSource):
    def __init__(self, *args, request=None, prompt=True, log="default", **kwargs):
        super().__init__()

        self.prompt = prompt
        self.log = log

        request_builder = RequestBuilder(
            self,
            *args,
            request=request,
            normaliser=self._normalise_request,
            **kwargs,
        )

        self.request = request_builder.requests

        if len(self.request) == 0:
            raise ValueError("ECMWFApi: no requests to process")

        self.expect_any = False
        for k, v in self.request[0].items():
            if k.lower() == "expect" and isinstance(v, str) and v.lower() == "any":
                self.expect_any = True
                break

        self.service()  # Trigger password prompt before threading

        # Download each request in parallel when the config allows it
        retriever = FileRequestRetriever(self, retriever=self._retrieve_one)
        self.path = retriever.retrieve(self.request)

    def _retrieve_one(self, request, *args):
        def retrieve(target, request):
            self.service().execute(request, target)

        return self.cache_file(
            retrieve,
            request,
        )

    @normalize("param", "variable-list(mars)")
    @normalize("date", "date-list(%Y-%m-%d)")
    @normalize("area", "bounding-box(list)")
    def _normalise_request(self, **kwargs):
        kwargs.pop("accumulation_period", None)
        return kwargs

    def to_pandas(self, **kwargs):
        pandas_read_csv_kwargs = dict(
            sep="\t",
            skipinitialspace=True,
        )

        pandas_read_csv_kwargs.update(kwargs.get("pandas_read_csv_kwargs", {}))

        # odc_read_odb_kwargs = dict(
        #     # TODO
        # )
        # odc_read_odb_kwargs.update(kwargs.get("odc_read_odb_kwargs", {}))

        return super().to_pandas(
            pandas_read_csv_kwargs=pandas_read_csv_kwargs,
            # odc_read_odb_kwargs=odc_read_odb_kwargs,
            **kwargs,
        )

    def empty_reader(self, *args, **kwargs):
        if self.expect_any:
            from .empty import EmptySource

            return EmptySource()
