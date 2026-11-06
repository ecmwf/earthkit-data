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
    raise ImportError("ADS access requires 'cdsapi' to be installed")

import yaml

from .cds import CDSRetriever
from .prompt import APIKeyPrompt


class ADSAPIKeyPrompt(APIKeyPrompt):
    register_or_sign_in_url = "https://ads.atmosphere.copernicus.eu/"
    retrieve_api_key_url = "https://ads.atmosphere.copernicus.eu/how-to-api"

    prompts = [
        dict(
            name="url",
            default="https://ads.atmosphere.copernicus.eu/api",
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

    rcfile = "~/.adsapirc"
    rc_message_base = """You have to store the credentials in {rcfile}; if you follow the
           instructions below it will be automatically done for you.
    """

    def save(self, input, file):
        yaml.dump(input, file, default_flow_style=False)

    def load(self, file):
        return yaml.safe_load(file.read())


def client(use_prompt):
    prompt = ADSAPIKeyPrompt()
    if use_prompt:
        rc = prompt.check(load=True)
    else:
        rcfile = prompt.existing_rcfile_path()
        if rcfile is None:
            raise FileNotFoundError(
                f"Cannot find the ADS credentials file '{prompt.rcfile}'. Create it with your "
                "API url and key, or call the source with prompt=True to be guided "
                "through the process."
            )
        with open(rcfile) as f:
            rc = prompt.load(f)
    return cdsapi.Client(**rc)


EXTENSIONS = {
    "grib": ".grib",
    "netcdf": ".nc",
}


class ADSRetriever(CDSRetriever):
    """Retrieve data from the Copernicus Atmosphere Data Store (ADS).

    Parameters
    ----------
    prompt : bool
        When True (default) and ``~/.adsapirc`` is missing, the user is asked
        for the credentials and they are saved to that file. When False no
        prompt is issued and a ``FileNotFoundError`` is raised if
        ``~/.adsapirc`` does not exist.
    """

    sphinxdoc = """
    ADSRetriever
    """

    def client(self):
        return client(self.prompt)
