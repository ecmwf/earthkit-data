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
from earthkit.data.utils import tqdm

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
    def __init__(self, *args, prompt=True, target=True, **kwargs):
        super().__init__()

        self.prompt = prompt
        self.targets = target

        request = {}
        for a in args:
            request.update(a)
        request.update(kwargs)

        requests = self.requests(**request)

        self.service()  # Trigger password prompt before threading

        if self.targets is not None:
            if not isinstance(self.targets, str):
                raise TypeError("target must be a str")
            if len(requests) > 1:
                self.targets = [f"{self.targets}.{i}" for i in range(len(requests))]
            else:
                self.targets = [self.targets]
        else:
            self.targets = [None for _ in self.requests]

        nthreads = min(self.settings("number-of-download-threads"), len(requests))

        if nthreads < 2:
            self.path = [self._retrieve(r, t) for r, t in zip(requests, self.targets)]
        else:
            with SoftThreadPool(nthreads=nthreads) as pool:
                futures = [
                    pool.submit(self._retrieve, r, SoftThreadPool)
                    for r, t in zip(requests, self.targets)
                ]

                iterator = (f.result() for f in futures)
                self.path = list(tqdm(iterator, leave=True, total=len(requests)))

    def _retrieve(self, request, target):
        def retrieve(target, request):
            self.service().execute(request, target)

        if target is not None:
            retrieve(target, request)
            return target
        else:
            return self.cache_file(
                retrieve,
                request,
            )

    @normalize("param", "variable-list(mars)")
    @normalize("date", "date-list(%Y-%m-%d)")
    @normalize("area", "bounding-box(list)")
    def requests(self, **kwargs):
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

    def mutate(self):
        if self.targets[0] is not None:
            return self
        else:
            return super().mutate()
