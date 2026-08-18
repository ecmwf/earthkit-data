#!/usr/bin/env python3

# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pytest
import requests

from earthkit.data import from_source
from earthkit.data.sources import _from_source_internal, get_source
from earthkit.data.sources import zenodo as zenodo_module

RECORD_ID = 123
CONCEPT_ID = 678
FILES = ["b.grib", "a.grib", "c.nc"]


def DOI(id):
    return f"10.5281/zenodo.{id}"  # as per https://support.zenodo.org/help/en-gb/18-general/216-what-is-a-doi


def download_url(name, record_id=RECORD_ID):
    """The download URL as the Zenodo API reports it in files[*].links.self."""
    return f"https://zenodo.org/api/records/{record_id}/files/{name}/content"


def assert_selected(zenodo, files=set(FILES), record_id=RECORD_ID):
    # Files ignores order of elements while list enforces it
    expected = type(files)(download_url(file, record_id) for file in files)
    assert type(files)(zenodo.urls) == expected


class MockResponse:
    """Stand-in for requests.Response."""

    def __init__(self, url=None, status_code=200, payload=None):
        self.url = url
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code} for {self.url}", response=self)

    def json(self):
        if self._payload is None:
            raise ValueError("invalid JSON")
        return self._payload


class MockRequests:
    """Stand-in for the requests module, pretending to be the Zenodo API."""

    ConnectionError = requests.ConnectionError
    Timeout = requests.Timeout
    HTTPError = requests.HTTPError

    def __init__(self):
        self.records = {}
        self.response = None
        # Observed behaviour
        self.urls = None
        self.kwargs = None

    def register_record(self, record_id, files, resolves_to=None):
        self.records[int(record_id)] = (list(files), int(resolves_to or record_id))

    def respond_with(self, response):
        self.response = response

    def get(self, url, **kwargs):
        assert url.startswith("https://zenodo.org/api/records/"), f"unexpected request to {url}"
        if self.response is None:
            record_id = int(url.rsplit("/", 1)[-1])
            if record_id not in self.records:
                return MockResponse(url, status_code=404)
            # Minimal valid response from the Zenodo API
            names, resolved_id = self.records[record_id]
            files = [{"key": name, "links": {"self": download_url(name, resolved_id)}} for name in names]
            return MockResponse(url, payload={"id": resolved_id, "files": files})
        if isinstance(self.response, Exception):
            raise self.response
        return self.response


class TestZenodoSourceOffline:
    """Offline test for the Zenodo source.

    Test up to the point where the Zenodo source mutates into a MultiURL source
    with a fake Zenodo API.
    """

    @pytest.fixture
    def zenodo(self, monkeypatch):
        api = MockRequests()
        api.register_record(RECORD_ID, FILES)
        api.register_record(CONCEPT_ID, FILES, resolves_to=RECORD_ID)

        def capture(urls, **kwargs):
            api.urls = list(urls)
            api.kwargs = kwargs
            return _from_source_internal("empty")

        # Patch the names bound in the zenodo module only
        monkeypatch.setattr(zenodo_module, "requests", api)
        monkeypatch.setattr(zenodo_module, "MultiUrl", capture)
        return api

    def test_zenodo_source_is_registered(self):
        assert get_source._lookup("zenodo") is not None

    @pytest.mark.parametrize("identifier", [RECORD_ID, CONCEPT_ID])
    def test_valid_identifier_int(self, zenodo, identifier):
        from_source("zenodo", identifier)
        assert_selected(zenodo)

    @pytest.mark.parametrize("identifier", [RECORD_ID, CONCEPT_ID])
    @pytest.mark.parametrize(
        "url",
        [
            "{id}",
            " {id}",
            "https://zenodo.org/record/{id}",
            "https://zenodo.org/records/{id}",
            "https://zenodo.org/records/{id}/",
            "https://zenodo.org/records/{id}?download=1",
            "  https://zenodo.org/records/{id}?download=1",
            "https://zenodo.org/records/{id}?download=1  ",
            "http://zenodo.org/record/{id}",
            "http://zenodo.org/records/{id}",
            "http://zenodo.org/records/{id}/",
            "zenodo.org/record/{id}",
            "zenodo.org/records/{id}",
            "zenodo.org/records/{id}/",
            "10.5281/zenodo.{id}",
            "doi:10.5281/zenodo.{id}",
            "https://doi.org/10.5281/zenodo.{id}",
            "https://doi.org/10.5281/zenodo.{id}/",
            "https://DOI.ORG/10.5281/zenodo.{id}",
            "http://doi.org/10.5281/zenodo.{id}",
            "http://doi.org/10.5281/zenodo.{id}/",
            "doi.org/10.5281/zenodo.{id}",
            "doi.org/10.5281/zenodo.{id}/",
            "https://dx.doi.org/10.5281/zenodo.{id}",
            "https://dx.doi.org/10.5281/zenodo.{id}/",
            "dx.doi.org/10.5281/zenodo.{id}",
        ],
    )
    @pytest.mark.parametrize(
        "only,expected",
        [
            (None, set(FILES)),
            ("c.nc", {"c.nc"}),
            ("*.grib", {"a.grib", "b.grib"}),
            (FILES, FILES),
            (FILES[::-1], FILES[::-1]),  # maintains order
            (["a.grib", "a.grib", "b.grib"], ["a.grib", "b.grib"]),  # ignores duplicates
        ],
    )
    def test_valid_identifier_str(self, zenodo, identifier, url, only, expected):
        from_source("zenodo", url.format(id=identifier), only=only)
        assert_selected(zenodo, files=expected)

    def test_without_kwargs(self, zenodo):
        from_source("zenodo", RECORD_ID)
        assert zenodo.kwargs == {}

    def test_kwargs_forwarded(self, zenodo):
        from_source("zenodo", RECORD_ID, only="a.grib", foo="bar", bar=False)
        assert zenodo.kwargs == {"foo": "bar", "bar": False}

    # ValueErrors for input validation problems and invalid file selection

    @pytest.mark.parametrize(
        "identifier",
        [
            None,
            "",
            "   ",
            "not-a-record",
            "10.1234/foo.567",
            "10.5281/foobar.12345",
            "https://example.com/records/12345",
            "https://zenodo.org/communities/abc",
            "https://zenodo.org/records/abc",
            "zenodo.org/records/12345/files/a.grib",
            # Near misses of the accepted doi.org URL forms
            "https://doi.org/10.1234/foo.567",
            "https://doi.org/10.5281/foobar.12345",
            "https://doi.org/",
            "https://doi.org",
            "https://example.com/10.5281/zenodo.12345",
            # The host must be matched, not merely found at the end of another one
            "https://mydoi.org/10.5281/zenodo.12345",
            # The doi: prefix and the URL form are alternatives, not combinable
            f"doi:https://doi.org/{DOI}",
        ],
    )
    def test_invalid_identifier(self, zenodo, identifier):
        with pytest.raises(ValueError):
            from_source("zenodo", identifier)

    @pytest.mark.parametrize(
        "only",
        [
            "",
            "*.zip",
            "d.grib",
            "grib",
            "a.gri",
            ["d.grib"],
            ["a.grib", "d.grib"],
            ["A.GRIB"],  # case sensitive
            ["*.grib"],  # list entry does not trigger pattern matching
            [],
        ],
    )
    def test_invalid_only(self, zenodo, only):
        with pytest.raises(ValueError):
            from_source("zenodo", RECORD_ID, only=only)

    # RuntimeErrors raised for problems with Zenodo API and response

    def test_zenodo_unknown_record(self, zenodo):
        with pytest.raises(RuntimeError):
            from_source("zenodo", 999)

    @pytest.mark.parametrize(
        "response",
        [
            requests.ConnectionError(),
            requests.ReadTimeout(),
            MockResponse(status_code=404),
            MockResponse(status_code=503),
            # Invalid JSON
            MockResponse(payload=None),
            # No files in records
            MockResponse(payload={}),
            MockResponse(payload={"files": []}),
            MockResponse(payload={"files": None}),
            MockResponse(payload={"metadata": {}}),
            # Malformed file entry
            MockResponse(payload={"files": [{"key": "a.grib"}]}),
            MockResponse(payload={"files": [{"key": "a.grib", "links": {}}]}),
            MockResponse(payload={"files": [{"links": {"self": "https://example.com/a.grib"}}]}),
            MockResponse(payload={"files": ["a.grib"]}),
        ],
    )
    def test_api_failure_runtime_errors(self, zenodo, response):
        zenodo.respond_with(response)
        with pytest.raises(RuntimeError):
            from_source("zenodo", RECORD_ID)


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
