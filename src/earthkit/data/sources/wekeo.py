# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os

try:
    import hda
except ImportError:
    raise ImportError("WEkEO access requires 'hda' to be installed")

import yaml

from earthkit.data.core.thread import SoftThreadPool

from .file import FileSource
from .prompt import APIKeyPrompt

LOG = logging.getLogger(__name__)


class HDAAPIKeyPrompt(APIKeyPrompt):
    register_or_sign_in_url = "https://www.wekeo.eu"
    retrieve_api_key_url = "https://www.wekeo.eu"

    prompts = [
        dict(
            name="user",
            example="name",
            title="User name",
            hidden=False,
            validate=r"[0-9a-z]+",
        ),
        dict(
            name="password",
            example="secretpassword",
            title="Password",
            hidden=True,
            validate=r"[0-9A-z\!\@\#\$\%\&\*]{5,30}",
        ),
    ]

    rcfile = "~/.hdarc"
    rcfile_env = "HDA_RC"
    config_env = ("HDA_USER", "HDA_PASSWORD")

    def save(self, input, file):
        yaml.dump(input, file, default_flow_style=False)

    def load(self, file):
        return yaml.safe_load(file.read())


class ApiClient(hda.Client):
    name = "wekeo"

    def __int__(self, *args, **kwargs):
        super().__init__(self, *args, **kwargs)

    def retrieve(self, name, request, target=None):
        matches = self.search(request["request"])
        out = []
        for result in matches.results:
            self.accept_tac(matches.dataset)
            download_id = matches._get_download_id(result)
            out.append(os.path.abspath(self.stream(download_id, result["properties"]["size"], target)))
        return out


EXTENSIONS = {
    "grib": ".grib",
    "netcdf": ".nc",
}


class WekeoRetriever(FileSource):
    sphinxdoc = """
    WekeoRetriever
    """

    def __init__(self, dataset, *args, prompt=True, **kwargs):
        super().__init__()

        self.prompt = prompt

        assert isinstance(dataset, str)
        if len(args):
            assert len(args) == 1
            assert isinstance(args[0], dict)
            assert not kwargs
            kwargs = args[0]

        requests = self.requests(**kwargs)

        self.client(self.prompt)  # Trigger password prompt before threading

        nthreads = min(self.config("number-of-download-threads"), len(requests))

        if nthreads < 2:
            self.path = [self._retrieve(dataset, r) for r in requests]
        else:
            from earthkit.data.utils.progbar import tqdm

            with SoftThreadPool(nthreads=nthreads) as pool:
                futures = [pool.submit(self._retrieve, dataset, r) for r in requests]

                iterator = (f.result() for f in futures)
                self.path = list(tqdm(iterator, leave=True, total=len(requests)))

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

    def _retrieve(self, dataset, request):
        def retrieve(target, args):
            self.client(self.prompt).retrieve(args[0], args[1], target)

        return self.cache_file(
            retrieve,
            (dataset, request),
            extension=EXTENSIONS.get(request.get("format"), ".cache"),
        )

    @staticmethod
    def requests(**kwargs):
        split_on = kwargs.pop("split_on", None)
        if split_on is None or not isinstance(kwargs.get(split_on), (list, tuple)):
            return [kwargs]

        result = []

        for v in kwargs[split_on]:
            r = dict(**kwargs)
            r[split_on] = v
            result.append(r)

        return result


source = WekeoRetriever
