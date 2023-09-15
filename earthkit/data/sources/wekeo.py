# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os

import hda
import yaml
from hda.api import DataOrderRequest

from earthkit.data.core.thread import SoftThreadPool
from earthkit.data.decorators import normalize
from earthkit.data.utils import tqdm

from .file import FileSource
from .prompt import APIKeyPrompt


class HDAAPIKeyPrompt(APIKeyPrompt):
    register_or_sign_in_url = "https://www.wekeo.eu"
    retrieve_api_key_url = "https://www.wekeo.eu"

    prompts = [
        dict(
            name="url",
            default="https://wekeo-broker.apps.mercator.dpi.wekeo.eu/databroker",
            title="API url",
            validate=r"http.?://.*",
        ),
        dict(
            name="user",
            example="name",
            title="User name",
            hidden=False,
            validate=r"[\-0-9a-z]+",
        ),
        dict(
            name="password",
            example="secretpassword",
            title="Password",
            hidden=False,
            validate=r"[\-0-9a-z\!\@\#\$\%\&\*]{5,30}",
        ),
    ]

    rcfile = "~/.hdarc"

    def save(self, input, file):
        yaml.dump(input, file, default_flow_style=False)


class ApiClient(hda.Client):
    name = "wekeo"

    def __int__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    def retrieve(self, name, request, target=None):
        matches = self.search(request["request"])
        out = []
        for result in matches.results:
            query = {"jobId": matches.job_id, "uri": result["url"]}
            url = DataOrderRequest(self).run(query)
            out.append(
                os.path.abspath(
                    self.stream(
                        result.get("filename"), result.get("size"), target, *url
                    )
                )
            )
        print(out, ">" * 20)
        return out

    def download(self, download_dir: str = "."):
        for result in self.results:
            query = {"jobId": self.jobId, "uri": result["url"]}
            self.debug(result)
            url = DataOrderRequest(self.client).run(query)
            self.stream(result.get("filename"), result.get("size"), download_dir, *url)


def client():
    prompt = HDAAPIKeyPrompt()
    prompt.check()

    try:
        return ApiClient()
    except Exception as e:
        if ".hdarc" in str(e):
            prompt.ask_user_and_save()
            return ApiClient()

        raise


EXTENSIONS = {
    "grib": ".grib",
    "netcdf": ".nc",
}


class WekeoRetriever(FileSource):
    sphinxdoc = """
    CdsRetriever
    """

    def client(self):
        return client()

    def __init__(self, dataset, *args, **kwargs):
        super().__init__()

        assert isinstance(dataset, str)
        if len(args):
            assert len(args) == 1
            assert isinstance(args[0], dict)
            assert not kwargs
            kwargs = args[0]

        requests = self.requests(**kwargs)

        self.client()  # Trigger password prompt before thraeding

        nthreads = min(self.settings("number-of-download-threads"), len(requests))

        if nthreads < 2:
            self.path = [self._retrieve(dataset, r) for r in requests]
        else:
            with SoftThreadPool(nthreads=nthreads) as pool:
                futures = [pool.submit(self._retrieve, dataset, r) for r in requests]

                iterator = (f.result() for f in futures)
                self.path = list(tqdm(iterator, leave=True, total=len(requests)))

    def _retrieve(self, dataset, request):
        def retrieve(target, args):
            self.client().retrieve(args[0], args[1], target)

        return self.cache_file(
            retrieve,
            (dataset, request),
            extension=EXTENSIONS.get(request.get("format"), ".cache"),
        )

    @normalize("date", "date-list(%Y-%m-%d)")
    @normalize("area", "bounding-box(list)")
    def requests(self, **kwargs):
        if "year" in kwargs:
            if "month" not in kwargs:
                kwargs["month"] = [f"{i+1:02}" for i in range(0, 12)]
            if "day" not in kwargs:
                kwargs["day"] = [f"{i+1:02}" for i in range(0, 31)]

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
            comment="#",
            parse_dates=["report_timestamp"],
            skip_blank_lines=True,
            compression="zip",
        )

        pandas_read_csv_kwargs.update(kwargs.get("pandas_read_csv_kwargs", {}))

        odc_read_odb_kwargs = dict(
            # TODO
        )

        odc_read_odb_kwargs.update(kwargs.get("odc_read_odb_kwargs", {}))

        return super().to_pandas(
            pandas_read_csv_kwargs=pandas_read_csv_kwargs,
            odc_read_odb_kwargs=odc_read_odb_kwargs,
            **kwargs,
        )


source = WekeoRetriever
