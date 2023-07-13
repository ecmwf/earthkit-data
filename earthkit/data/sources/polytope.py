# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import polytope
import requests

from .prompt import APIKeyPrompt
from . import Source
from .multi import MultiSource
from .memory import MemorySource
from .multi_url import MultiUrl

LOG = logging.getLogger(__name__)

class PolytopeWebKeyPrompt(APIKeyPrompt):
    register_or_sign_in_url="",
    retrieve_api_key_url="",
    prompts = [
        dict(
            name="user_email",
            title="Your email",
        ),
        dict(
            name="user_key",
            example="b295aad8af30332fad2fa8c963ab7900",
            title="API key",
            hidden=True,
            validate="[0-9a-z]{32}",
        ),
    ]

    rcfile = "~/.polytopeapirc"


class Polytope(Source):
    def __init__(self, dataset, request):
        """
        Usage:
            earthkit.data.from_source("polytope", "iecmwf-mars", request)
        """
        super().__init__()
        assert isinstance(dataset, str)
        self.request = dict(dataset = dataset,
                            request = request)
        
        credentials = PolytopeWebKeyPrompt().check(load = True)
        self.client = polytope.api.Client(**credentials)

    def mutate(self):
        pointers = self.client.retrieve(self.request["dataset"],
                                        self.request["request"],
                                        pointer = True, asynchronous=False)
        
        urls = [p['location'] for p in pointers]
        file_sources = [MemorySource(requests.get(url).content) for url in urls]
        
        if len(file_sources) == 1:
            return file_sources[0]
        
        # This does not actually work, if gives 
        return MultiSource(file_sources)


source = Polytope