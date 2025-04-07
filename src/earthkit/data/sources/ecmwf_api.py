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


class MarsFetcher:
    def __init__(self, service):
        self.service = service

    def get(self, request):
        def retrieve(target, request):
            self.service.execute(request, target)

        return self.cache_file(
            retrieve,
            request,
        )

    def cache_file(self, create, args, **kwargs):
        import re

        from earthkit.data.core.caching import cache_file

        owner = kwargs.pop("owner", None)
        if owner is None:
            owner = re.sub(r"(?!^)([A-Z]+)", r"-\1", self.__class__.__name__).lower()

        return cache_file(owner, create, args, **kwargs)


class RequestMappaper:
    defaults = {
        "class": "oper",
        "type": "an",
        "stream": "da",
        "expver": "1",
        "param": "z",
        "levtype": "pl",
        "levelist": [1000, 850, 700, 500, 400, 300],
        "time": 12,
        "step": 0,
    }
    mandatory = ["date", "area", "grid"]

    def __init__(self, *args, request, **kwargs):
        self.request = request
        coords = {}
        self.skipped = {}

        # res = []
        skip = ["grid", "area"]
        for r in request:
            # keys = []
            # vals = []
            for k, v in r.items():
                if k in skip:
                    self.skipped[k] = v
                else:
                    if not isinstance(v, (list, tuple)):
                        v = [v]
                    if k not in coords:
                        coords[k] = v
                    else:
                        coords[k].append(v)

        self.coords = coords
        self.shape = [len(v) for v in coords.values()]

    def coords_to_index(coords, shape) -> int:
        """
        Map user coords to field index"""
        index = 0
        n = 1
        for i in range(len(coords) - 1, -1, -1):
            index += coords[i] * n
            n *= shape[i]
        return index

    def index_to_coords(self, index: int, shape):
        assert isinstance(index, int), (index, type(index))

        result = [None] * len(shape)
        i = len(shape) - 1

        while i >= 0:
            result[i] = index % shape[i]
            index = index // shape[i]
            i -= 1

        result = tuple(result)

        assert len(result) == len(shape)
        return result

    def request_at(self, index):
        idx = self.index_to_coords(index, self.shape)
        r = {}
        for i, key in enumerate(self.coords):
            r[key] = self.coords[key][idx[i]]
        r.update(self.skipped)
        return r

    def __len__(self):
        import math

        return math.prod(self.shape)


class ECMWFApi(FileSource):
    def __init__(self, *args, prompt=True, log="default", lazy=False, **kwargs):
        super().__init__()

        self.prompt = prompt
        self.log = log
        self.lazy = lazy

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

        self.request = requests

        self.service()  # Trigger password prompt before threading

        if lazy:
            pass
        else:
            nthreads = min(self.config("number-of-download-threads"), len(requests))

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

    def request_per_field(self, requests):
        from itertools import product

        # print(requests)

        res = []
        skip = ["grid", "area"]
        for r in requests:
            keys = []
            vals = []
            skipped = {}
            for k, v in r.items():
                if k in skip:
                    skipped[k] = v
                else:
                    keys.append(k)
                    if isinstance(v, (list, tuple)):
                        vals.append(v)
                    else:
                        vals.append([v])

            for v in product(*vals):
                res.append(dict(zip(keys, v), **skipped))

        return res

    def mutate(self):
        if self.lazy:
            print("lazy")
            mapper = RequestMappaper(request=self.request)
            print("coords", mapper.coords)
            print("index[0]", mapper.index_to_coords(0, mapper.shape))
            print("index[0]", mapper.request_at(0))
            print("index[1]", mapper.request_at(1))
            from earthkit.data.readers.grib.virtual import VirtualGribFieldList

            return VirtualGribFieldList(mapper, MarsFetcher(self.service()))

        return self
        # ref = self.request[0]
        # ref_path = _retrieve(self, ref)
        # return VirtualGribFieldList(ref_path, requests, fetcher=MarsFetcher(self.service()))
