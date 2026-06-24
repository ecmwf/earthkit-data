# (C) Copyright 2026- ECMWF and individual contributors.

# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation nor
# does it submit to any jurisdiction.

import fnmatch
import logging
import re

import requests

from earthkit.data.core.config import CONFIG
from earthkit.data.sources import Source, from_source_internal

LOG = logging.getLogger(__name__)

_DOI_PATTERN = re.compile(r"^(?:doi:\s*)?(10\.5281/zenodo\.\d+)$", flags=re.IGNORECASE)
_URL_PATTERN = re.compile(r"^(?:https?:\/\/)?zenodo\.org\/records?\/(\d+)\/?(?:\?.*)?$")


def _resolve_doi(doi):
    timeout = CONFIG.get("url-download-timeout")

    LOG.debug("Resolving DOI %s", doi)
    try:
        r = requests.get(f"https://doi.org/{doi}", timeout=timeout)
        r.raise_for_status()
    except requests.ConnectionError as e:
        raise RuntimeError("Could not connect to doi.org") from e
    except requests.Timeout as e:
        raise RuntimeError(f"request to doi.org timed out after {timeout}s") from e
    except requests.HTTPError as e:
        raise RuntimeError(f"doi.org returned HTTP {r.status_code}") from e

    resolved_url = r.url
    LOG.debug(f"DOI {doi} resolved to {resolved_url}")

    match = _URL_PATTERN.match(resolved_url)
    if not match:
        raise ValueError(f"DOI '{doi}' resolved to an unexpected URL: {resolved_url}. Expected a Zenodo record URL.")
    return int(match.group(1))


def _get_record_files(record_id):
    timeout = CONFIG.get("url-download-timeout")

    api_url = f"https://zenodo.org/api/records/{record_id}"
    LOG.debug(f"Fetching file list for record {record_id} from {api_url}")
    try:
        r = requests.get(api_url, timeout=timeout)
        r.raise_for_status()
    except requests.ConnectionError as e:
        raise RuntimeError("could not connect to zenodo.org") from e
    except requests.Timeout as e:
        raise RuntimeError(f"request to zenodo.org timed out after {timeout}s.") from e
    except requests.HTTPError as e:
        raise RuntimeError(f"Zenodo API returned HTTP {r.status_code}") from e

    try:
        data = r.json()
    except ValueError as e:
        raise RuntimeError("failed to parse Zenodo API response") from e

    if "files" not in data or not data["files"]:
        raise RuntimeError(f"Record {record_id} has no accessible files. The record may be restricted or embargoed.")

    files = [f["key"] for f in data["files"]]
    LOG.debug(f"Record {record_id} contains {len(files)} file(s): {files!r}")

    # Map of file name to its download URL, sorted by file name
    return {name: f"https://zenodo.org/records/{record_id}/files/{name}?download=1" for name in sorted(files)}


class Zenodo(Source):
    """Source for downloading files from Zenodo records.

    Parameters
    ----------
    identifier : int | str
        Record ID, Zenodo URL or DOI.
    filenames : str | Sequence[str] | None, optional
        File selection with a glob string or an explicit list of file names.
        By default, all files are selected.
    **kwargs
        Additional keyword arguments forwarded to the  URL source.
    """

    def __init__(self, identifier, filenames=None, **kwargs):
        super().__init__()
        self._kwargs = kwargs

        if isinstance(identifier, str):
            identifier = identifier.strip()

        # Resolve DOI to record ID
        if isinstance(identifier, str) and (match := _DOI_PATTERN.match(identifier)):
            doi = match.group(1)
            self.record_id = _resolve_doi(doi)
        # Treat everything else as a record ID
        elif isinstance(identifier, int):
            self.record_id = identifier
        elif isinstance(identifier, str) and (match := _URL_PATTERN.match(identifier)):
            self.record_id = int(match.group(1))
        elif isinstance(identifier, str) and identifier.isnumeric():
            self.record_id = int(identifier)
        else:
            raise ValueError(f"unable to determine record ID from identifier: {identifier!r}")

        LOG.info(f"Zenodo record ID: {self.record_id}")

        # Fetch file metadata from the Zenodo API
        record_files = _get_record_files(self.record_id)

        # No filenames specified -> select all
        if filenames is None:
            self._file_urls = record_files
        # Match filenames with provided pattern
        elif isinstance(filenames, str):
            matched = fnmatch.filter(record_files.keys(), filenames)
            if not matched:
                raise FileNotFoundError(f"no files in record {self.record_id} matched the pattern: {filenames!r}")
            self._file_urls = {name: record_files[name] for name in matched}
        # Select filenames based on provided list
        else:
            for name in filenames:
                if name not in record_files:
                    raise FileNotFoundError(f"file {name!r} not found in record {self.record_id}")
            self._file_urls = {name: record_files[name] for name in filenames}

        LOG.info(
            f"Selected {len(self._file_urls)} file(s) from record {self.record_id}:, ".join(self._file_urls.keys())
        )

    def mutate(self):
        urls = list(self._file_urls.values())
        return from_source_internal("url", urls, **self._kwargs)


source = Zenodo
