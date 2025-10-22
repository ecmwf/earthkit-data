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
    import cdsapi
except ImportError:
    raise ImportError("CDS access requires 'cdsapi' to be installed")

import yaml

from earthkit.data.decorators import normalize
from earthkit.data.utils.request import FileRequestRetriever
from earthkit.data.utils.request import RequestBuilder

from .file import FileSource
from .prompt import APIKeyPrompt

LOG = logging.getLogger(__name__)


class CDSAPIKeyPrompt(APIKeyPrompt):
    register_or_sign_in_url = "https://cds.climate.copernicus.eu/"
    retrieve_api_key_url = "https://cds.climate.copernicus.eu/how-to-api"

    prompts = [
        dict(
            name="url",
            default="https://cds.climate.copernicus.eu/api",
            title="API url",
            validate=r"http.?://.*",
        ),
        dict(
            name="key",
            example="abcdef01-0000-1111-2222-0123456789ab",
            title="API key",
            hidden=True,
            validate=r"[\-0-9a-f]+",
        ),
    ]

    rcfile = "~/.cdsapirc"
    rcfile_env = "CDSAPI_RC"
    config_env = ("CDSAPI_URL", "CDSAPI_KEY")

    def save(self, input, file):
        yaml.dump(input, file, default_flow_style=False)

    def load(self, file):
        return yaml.safe_load(file.read())


def client(use_prompt):
    if use_prompt:
        prompt = CDSAPIKeyPrompt()
        prompt.check()

        try:
            return cdsapi.Client()
        except Exception as e:
            if ".cdsapirc" in str(e) or not prompt.has_config_env():
                LOG.warning(e)
                LOG.exception(f"Could not load cds api client. {e}")
                prompt.ask_user_and_save()
                return cdsapi.Client()

            raise
    else:
        return cdsapi.Client()


EXTENSIONS = {
    "grib": ".grib",
    "netcdf": ".nc",
}


class CdsRetriever(FileSource):
    sphinxdoc = """
    CdsRetriever
    """

    def __init__(self, dataset, *args, request=None, prompt=True, **kwargs):
        super().__init__()

        self.prompt = prompt
        assert isinstance(dataset, str)

        self.dataset = dataset

        request_builder = RequestBuilder(
            self, *args, request=request, normaliser=self._normalise_request, **kwargs
        )
        self.request = request_builder.requests

        self.client()  # Trigger password prompt before threading

        # Download each request in parallel when the config allows it
        retriever = FileRequestRetriever(self, retriever=self._retrieve_one)
        self.path = retriever.retrieve(self.request, self.dataset)

    def _retrieve_one(self, request, dataset):
        def retrieve(target, args):
            cds_result = self.client().retrieve(args[0], args[1])
            self.source_filename = cds_result.location.split("/")[-1]
            cds_result.download(target=target)

        return_object = self.cache_file(
            retrieve,
            (dataset, request),
            extension=EXTENSIONS.get(request.get("format"), ".cache"),
        )
        return return_object

    @staticmethod
    @normalize("area", "bounding-box(list)")
    def _normalise_request(**kwargs):
        return kwargs

    # TODO: review if we need this property
    @property
    def requests(self):
        return self.request

    def client(self):
        return client(self.prompt)


source = CdsRetriever
