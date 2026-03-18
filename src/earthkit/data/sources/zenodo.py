# (C) Copyright 2026- ECMWF and individual contributors.

# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.

import fnmatch
import re

import requests

from earthkit.data.sources import Source
from earthkit.data.sources import from_source_internal

_DOI_PATTERN = re.compile(r"^(?:doi:\s*)?(10\.5281/zenodo\.\d+)$", flags=re.IGNORECASE)
_URL_PATTERN = re.compile(r"^(?:https?:\/\/)?zenodo\.org\/records\/(\d+)\/?$")


def _resolve_doi(doi):
    r = requests.get(f"https://doi.org/{doi}")
    r.raise_for_status()
    return r.url


def _get_file_list(record_id):
    r = requests.get(f"https://zenodo.org/api/records/{record_id}")
    r.raise_for_status()
    return {f["key"] for f in r.json()["files"]}


class Zenodo(Source):

    def __init__(self, identifier, file="*", **kwargs):
        super().__init__()
        self.kwargs = kwargs

        if match := _DOI_PATTERN.match(identifier):
            identifier = _resolve_doi(match.group(1))

        if isinstance(identifier, int):
            self.record_id = identifier
        elif match := _URL_PATTERN.match(identifier):
            self.record_id = int(match.group(1))
        elif identifier.isnumeric():
            self.record_id = int(identifier)
        else:
            raise ValueError(f"unable to determine record ID from identifier {identifier}")

        # Obtain the list of files in the record and match against provided pattern
        record_files = _get_file_list(self.record_id)
        if file is None:
            self.files = record_files
        else:
            self.files = fnmatch.filter(record_files, file)
            if not self.files:
                raise FileNotFoundError(file)  # TODO

    def mutate(self):
        urls = [f"https://zenodo.org/records/{self.record_id}/files/{file}?download=1" for file in self.files]
        return from_source_internal("url", urls, **self.kwargs)


source = Zenodo
