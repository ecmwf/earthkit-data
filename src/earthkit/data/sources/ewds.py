# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


try:
    import cdsapi
except ImportError:
    raise ImportError("EWDS access requires 'cdsapi' to be installed")

import yaml

from .cds import CdsRetriever
from .prompt import APIKeyPrompt


class EWDSAPIKeyPrompt(APIKeyPrompt):
    register_or_sign_in_url = "https://ewds.atmosphere.copernicus.eu/"
    retrieve_api_key_url = "https://ewds.atmosphere.copernicus.eu/how-to-api"

    prompts = [
        dict(
            name="url",
            default="https://ewds.atmosphere.copernicus.eu/api",
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
    rc_message_base = """You have to store the credentials in {rcfile}; if you follow the
           instructions below it will be automatically done for you.
    """

    def save(self, input, file):
        yaml.dump(input, file, default_flow_style=False)

    def load(self, file):
        return yaml.safe_load(file.read())


def client():
    prompt = EWDSAPIKeyPrompt()
    rc = prompt.check(load=True)
    return cdsapi.Client(**rc)


EXTENSIONS = {
    "grib": ".grib",
    "netcdf": ".nc",
}


class EwdsRetriever(CdsRetriever):
    sphinxdoc = """
    EwdsRetriever
    """

    def client(self):
        return client()


source = EwdsRetriever
