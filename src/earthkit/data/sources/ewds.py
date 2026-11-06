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

from .cds import CDSRetriever
from .prompt import APIKeyPrompt


class EWDSAPIKeyPrompt(APIKeyPrompt):
    register_or_sign_in_url = "https://ewds.climate.copernicus.eu/"
    retrieve_api_key_url = "https://ewds.climate.copernicus.eu/profile"

    prompts = [
        dict(
            name="url",
            default="https://ewds.climate.copernicus.eu/api",
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

    rcfile = "~/.ewdsapirc"
    rc_message_base = """You have to store the credentials in {rcfile}; if you follow the
           instructions below it will be automatically done for you.
    """

    def save(self, input, file):
        yaml.dump(input, file, default_flow_style=False)

    def load(self, file):
        return yaml.safe_load(file.read())


def client(use_prompt):
    prompt = EWDSAPIKeyPrompt()
    if use_prompt:
        rc = prompt.check(load=True)
    else:
        rcfile = prompt.existing_rcfile_path()
        if rcfile is None:
            raise FileNotFoundError(
                f"Cannot find the EWDS credentials file '{prompt.rcfile}'. Create it with your "
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


class EWDSRetriever(CDSRetriever):
    """Retrieve data from the CEMS Early Warning Data Store (EWDS).

    Signature::

        EWDSRetriever(dataset, *, request, prompt=True)

    Parameters
    ----------
    dataset : str
        The dataset name.
    request : dict or list/tuple of dict
        A single request dictionary or a list/tuple of request dictionaries.
        Required, keyword-only. May contain the ``split_on`` key.
    prompt : bool
        When True (default) and ``~/.ewdsapirc`` is missing, the user is asked
        for the credentials and they are saved to that file. When False no
        prompt is issued and a ``FileNotFoundError`` is raised if
        ``~/.ewdsapirc`` does not exist.
    """

    sphinxdoc = """
    EWDSRetriever

    Signature::

        from_source("ewds", dataset, *, request, prompt=True)
    """

    def __init__(self, dataset, *, request, prompt=True):
        super().__init__(dataset, request=request, prompt=prompt)

    def client(self):
        return client(self.prompt)
