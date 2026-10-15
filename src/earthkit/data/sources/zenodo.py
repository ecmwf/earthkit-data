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
from earthkit.data.sources import Source
from earthkit.data.sources.multi_url import MultiUrl

LOG = logging.getLogger(__name__)

_DOI_PATTERN = re.compile(
    r"^(?:doi:\s*|(?:https?:\/\/)?(?:dx\.)?doi\.org\/)?10\.5281/zenodo\.(\d+)\/?$",
    flags=re.IGNORECASE,
)
_URL_PATTERN = re.compile(r"^(?:https?:\/\/)?zenodo\.org\/records?\/(\d+)\/?(?:\?.*)?$", flags=re.IGNORECASE)


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

    if not isinstance(data, dict) or "files" not in data:
        raise RuntimeError(f"unexpected Zenodo API response for record {record_id}")
    if not data["files"]:
        raise RuntimeError(f"Record {record_id} has no accessible files. The record may be restricted or embargoed.")

    try:
        # URLs from API response, works for record and concept IDs
        file_urls = {f["key"]: f["links"]["self"] for f in data["files"]}
    except (KeyError, TypeError) as e:
        raise RuntimeError(f"unexpected file entry in the Zenodo API response for record {record_id}") from e

    LOG.debug(f"Record {record_id} contains {len(file_urls)} file(s): {list(file_urls)!r}")
    return file_urls


class Zenodo(Source):
    """Source for downloading files from Zenodo records.

    Parameters
    ----------
    identifier : int | str
        Record ID, Zenodo URL or DOI. A DOI may also be given as a doi.org URL.
    only : str | Sequence[str] | None, optional
        File selection with a glob string or an explicit list of file names.
        By default, all files are selected.
    **kwargs
        Additional keyword arguments forwarded to the URL source.
    """

    def __init__(self, identifier, only=None, **kwargs):
        super().__init__()
        self._kwargs = kwargs

        if isinstance(identifier, str):
            identifier = identifier.strip()

        # A Zenodo DOI is 10.5281/zenodo.<record ID>, so no lookup via doi.org is needed.
        # For a concept DOI this is the concept record's ID, which the API redirects to the
        # latest version, and the file URLs then refer to that version.
        if isinstance(identifier, str) and (match := _DOI_PATTERN.match(identifier)):
            self.record_id = int(match.group(1))
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
        if only is None:
            self._file_urls = record_files
        # Match filenames with provided pattern
        elif isinstance(only, str):
            matched = fnmatch.filter(record_files.keys(), only)
            if not matched:
                raise ValueError(f"no files in record {self.record_id} match the pattern: {only!r}")
            self._file_urls = {name: record_files[name] for name in matched}
        # Select filenames based on provided list
        else:
            only = list(dict.fromkeys(only))  # deduplicate while preserving order
            if not only:
                raise ValueError(f"no files selected from record {self.record_id}")
            self._file_urls = {name: record_files[name] for name in only if name in record_files}
            if len(self._file_urls) != len(only):
                missing = ", ".join(repr(name) for name in only if name not in record_files)
                raise ValueError(f"file(s) not found in record {self.record_id}: " + missing)

        selected = ", ".join(self._file_urls.keys())
        LOG.info(f"Selected {len(self._file_urls)} file(s) from record {self.record_id}: {selected}")

    def mutate(self):
        urls = list(self._file_urls.values())
        return MultiUrl(urls, **self._kwargs)


source = Zenodo
