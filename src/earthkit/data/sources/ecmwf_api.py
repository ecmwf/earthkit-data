# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from earthkit.data.core.thread import SoftThreadPool
from earthkit.data.decorators import normalize

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
    def __init__(self, *args, prompt=True, **kwargs):
        super().__init__()

        self.prompt = prompt

        request = {}
        for a in args:
            request.update(a)
        request.update(kwargs)

        requests = self.requests(**request)

        self.expect_any = False
        for k, v in requests[0].items():
            if k.lower() == "expect" and isinstance(v, str) and v.lower() == "any":
                self.expect_any = True
                break

        self.service()  # Trigger password prompt before threading

        nthreads = min(self.settings("number-of-download-threads"), len(requests))

        if nthreads < 2:
            self.path = [self._retrieve(r) for r in requests]
        else:
            from earthkit.data.utils.progbar import tqdm

            with SoftThreadPool(nthreads=nthreads) as pool:
                futures = [pool.submit(self._retrieve, r) for r in requests]

                iterator = (f.result() for f in futures)
                self.path = list(tqdm(iterator, leave=True, total=len(requests)))

    def _retrieve(self, request):
        def retrieve(target, request):
            self.service().execute(request, target)

        return self.cache_file(
            retrieve,
            request,
        )

    @normalize("param", "variable-list(mars)")
    @normalize("date", "date-list(%Y-%m-%d)")
    @normalize("area", "bounding-box(list)")
    def requests(self, **kwargs):
        kwargs.pop("accumulation_period", None)
        split_on = kwargs.pop("split_on", None)
        if split_on is None or not isinstance(kwargs.get(split_on), (list, tuple)):
            return [kwargs]

        result = []

        for v in kwargs[split_on]:
            r = dict(**kwargs)
            r[split_on] = v
            result.append(r)

        return result

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
