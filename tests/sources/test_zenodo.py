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

from earthkit.data import config, from_source
from earthkit.data.sources import _from_source_internal, get_source
from earthkit.data.sources import zenodo as zenodo_module

# Test up to the point where the Zenodo source mutates into a MultiURL source.
# Create a fake Zenodo API and verify the generated URLs.

RECORD_ID = 123
CONCEPT_ID = 678
FILES = ["b.grib", "a.grib", "c.nc"]


def DOI(id):
    """The DOI for a given Zenodo record ID."""
    return f"10.5281/zenodo.{id}"  # as per https://support.zenodo.org/help/en-gb/18-general/216-what-is-a-doi


def download_url(name, record_id=RECORD_ID):
    """The download URL as the Zenodo API reports it in files[*].links.self."""
    return f"https://zenodo.org/api/records/{record_id}/files/{name}/content"


def assert_selected(zenodo, names=FILES, record_id=RECORD_ID):
    """Compare selections ignoring order, which is not part of the source's contract."""
    assert set(zenodo.urls) == set(download_url(name, record_id) for name in names)


BAD_JSON = object()
UNSET = object()


class FakeResponse:
    def __init__(self, url, status_code=200, payload=None):
        self.url = url
        self.status_code = status_code
        self._payload = payload

    def raise_for_status(self):
        if self.status_code >= 400:
            raise requests.HTTPError(f"HTTP {self.status_code} for {self.url}", response=self)

    def json(self):
        if self._payload is BAD_JSON:
            raise ValueError("not valid JSON")
        return self._payload


class FakeZenodo:
    """Stand-in for the Zenodo REST API, and for the url source handover."""

    def __init__(self):
        self.records = {}
        self.api_failure = None
        self.api_payload = UNSET
        # Observed behaviour
        self.requested = []
        self.urls = None
        self.kwargs = None

    # -- configuration ------------------------------------------------------

    def record(self, record_id, files, resolves_to=None):
        """Register a record. ``resolves_to`` mimics a concept record, which the API
        redirects to the latest version, reporting that version's ID and file links.
        """
        self.records[int(record_id)] = (list(files), int(resolves_to or record_id))

    def fail_api(self, failure):
        """Make the Zenodo API fail, either with an exception instance or an HTTP status code."""
        self.api_failure = failure

    def api_returns(self, payload):
        """Make the Zenodo API return an arbitrary payload (or ``BAD_JSON``)."""
        self.api_payload = payload

    # -- the fake requests.get ----------------------------------------------

    def get(self, url, timeout=None):
        self.requested.append(url)
        if url.startswith("https://zenodo.org/api/records/"):
            return self._api_response(url)
        raise AssertionError(f"unexpected request to {url}")

    def _api_response(self, url):
        if self.api_failure is not None:
            return self._failure(url, self.api_failure)
        if self.api_payload is not UNSET:
            return FakeResponse(url, payload=self.api_payload)
        record_id = int(url.rsplit("/", 1)[-1])
        if record_id not in self.records:
            return FakeResponse(url, status_code=404)
        names, resolved_id = self.records[record_id]
        files = [{"key": name, "links": {"self": download_url(name, resolved_id)}} for name in names]
        return FakeResponse(url, payload={"id": resolved_id, "files": files})

    @staticmethod
    def _failure(url, failure):
        if isinstance(failure, int):
            return FakeResponse(url, status_code=failure)
        raise failure


class FakeRequests:
    """Minimal stand-in for the ``requests`` module as used by the zenodo source."""

    ConnectionError = requests.ConnectionError
    Timeout = requests.Timeout
    HTTPError = requests.HTTPError

    def __init__(self, api):
        self.get = api.get


class TestZenodoSourceOffline:
    @pytest.fixture
    def zenodo(self, monkeypatch):
        api = FakeZenodo()
        api.record(RECORD_ID, FILES)
        api.record(CONCEPT_ID, FILES, resolves_to=RECORD_ID)

        def capture(urls, **kwargs):
            api.urls = list(urls)
            api.kwargs = kwargs
            return _from_source_internal("empty")

        # Patch the names bound in the zenodo module only
        monkeypatch.setattr(zenodo_module, "requests", FakeRequests(api))
        monkeypatch.setattr(zenodo_module, "MultiUrl", capture)
        return api

    def test_zenodo_source_is_registered(self):
        assert get_source._lookup("zenodo") is not None

    @pytest.mark.parametrize("identifier", [RECORD_ID, CONCEPT_ID])
    def test_int_identifier(self, zenodo, identifier):
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
    def test_str_identifiers_valid(self, zenodo, identifier, url):
        from_source("zenodo", url.format(id=identifier))
        assert_selected(zenodo)

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
    def test_identifiers_invalid(self, zenodo, identifier):
        with pytest.raises(ValueError, match="unable to determine record ID"):
            from_source("zenodo", identifier)

    def test_zenodo_unknown_record(self, zenodo):
        with pytest.raises(RuntimeError, match="Zenodo API returned HTTP 404"):
            from_source("zenodo", 999)

    @pytest.mark.parametrize(
        "failure,message",
        [
            (requests.ConnectionError("no route to host"), "could not connect to zenodo.org"),
            (requests.ReadTimeout("too slow"), "request to zenodo.org timed out after"),
            (403, "Zenodo API returned HTTP 403"),
            (404, "Zenodo API returned HTTP 404"),
            (500, "Zenodo API returned HTTP 500"),
            (503, "Zenodo API returned HTTP 503"),
        ],
    )
    def test_zenodo_api_failure(self, zenodo, failure, message):
        zenodo.fail_api(failure)
        with pytest.raises(RuntimeError, match=message):
            from_source("zenodo", RECORD_ID)

    def test_zenodo_api_invalid_json(self, zenodo):
        zenodo.api_returns(BAD_JSON)
        with pytest.raises(RuntimeError, match="failed to parse Zenodo API response"):
            from_source("zenodo", RECORD_ID)

    @pytest.mark.parametrize("payload", [{}, {"files": []}, {"files": None}, {"metadata": {}}])
    def test_zenodo_record_without_files(self, zenodo, payload):
        zenodo.api_returns(payload)
        with pytest.raises(RuntimeError, match="no accessible files"):
            from_source("zenodo", RECORD_ID)

    @pytest.mark.parametrize("timeout,expected", [(7, "7s"), ("20s", "20s")])
    def test_zenodo_timeout_message_reports_configured_timeout(self, zenodo, timeout, expected):
        zenodo.fail_api(requests.ReadTimeout("too slow"))
        with config.temporary("url-download-timeout", timeout):
            with pytest.raises(RuntimeError, match=f"timed out after {expected}"):
                from_source("zenodo", RECORD_ID)

    def test_zenodo_download_url_comes_from_the_api(self, zenodo):
        # The URL is whatever the API reports, not something the source builds
        zenodo.api_returns({"files": [{"key": "a.grib", "links": {"self": "https://example.com/elsewhere"}}]})
        from_source("zenodo", RECORD_ID, filenames="a.grib")
        assert zenodo.urls == ["https://example.com/elsewhere"]

    @pytest.mark.parametrize(
        "files",
        [
            [{"key": "a.grib"}],
            [{"key": "a.grib", "links": {}}],
            [{"links": {"self": "https://example.com/a.grib"}}],
            ["a.grib"],
        ],
    )
    def test_zenodo_malformed_file_entry(self, zenodo, files):
        zenodo.api_returns({"files": files})
        with pytest.raises(RuntimeError, match="unexpected file entry"):
            from_source("zenodo", RECORD_ID)

    def test_zenodo_all_files_selected(self, zenodo):
        from_source("zenodo", RECORD_ID)
        assert_selected(zenodo, FILES)

    @pytest.mark.parametrize(
        "pattern,expected",
        [
            ("*", ["a.grib", "b.grib", "c.nc"]),
            ("*.grib", ["a.grib", "b.grib"]),
            ("*.nc", ["c.nc"]),
            ("?.grib", ["a.grib", "b.grib"]),
            ("[ab].grib", ["a.grib", "b.grib"]),
            ("a.grib", ["a.grib"]),
        ],
    )
    def test_zenodo_filenames_pattern(self, zenodo, pattern, expected):
        from_source("zenodo", RECORD_ID, filenames=pattern)
        assert_selected(zenodo, expected)

    @pytest.mark.parametrize("pattern", ["*.zip", "d.grib", "", "grib", "a.gri"])
    def test_zenodo_filenames_pattern_no_match(self, zenodo, pattern):
        with pytest.raises(FileNotFoundError, match="match the pattern"):
            from_source("zenodo", RECORD_ID, filenames=pattern)

    @pytest.mark.parametrize(
        "filenames,expected",
        [
            (["a.grib"], ["a.grib"]),
            (["a.grib", "c.nc"], ["a.grib", "c.nc"]),
            # The caller's order must be honoured: unlike the all-files case, which has no
            # defined order, an explicit list is used exactly as given.
            (["c.nc", "a.grib"], ["c.nc", "a.grib"]),
            (("b.grib", "a.grib"), ["b.grib", "a.grib"]),
            (FILES, FILES),
            # A repeated name is requested once, keeping its first position
            (["a.grib", "c.nc", "a.grib"], ["a.grib", "c.nc"]),
            (["c.nc", "c.nc"], ["c.nc"]),
        ],
    )
    def test_zenodo_filenames_list(self, zenodo, filenames, expected):
        from_source("zenodo", RECORD_ID, filenames=filenames)
        assert zenodo.urls == [download_url(name) for name in expected]

    @pytest.mark.parametrize(
        "filenames,missing",
        [
            (["d.grib"], ["d.grib"]),
            (["a.grib", "d.grib"], ["d.grib"]),
            # Matching is case sensitive, and a list entry is a name rather than a pattern
            (["A.GRIB"], ["A.GRIB"]),
            (["*.grib"], ["*.grib"]),
            # Every unknown name is reported at once, so a caller does not have to fix them
            # one API request at a time
            (["d.grib", "e.nc"], ["d.grib", "e.nc"]),
            (["d.grib", "a.grib", "e.nc"], ["d.grib", "e.nc"]),
            (["e.nc", "d.grib"], ["e.nc", "d.grib"]),
            # A repeated unknown name is reported once
            (["d.grib", "d.grib"], ["d.grib"]),
        ],
    )
    def test_zenodo_filenames_list_unknown_file(self, zenodo, filenames, missing):
        with pytest.raises(FileNotFoundError, match=f"not found in record {RECORD_ID}"):
            from_source("zenodo", RECORD_ID, filenames=filenames)

    @pytest.mark.parametrize("filenames", [[], ()])
    def test_zenodo_filenames_empty(self, zenodo, filenames):
        with pytest.raises(FileNotFoundError, match="no files selected"):
            from_source("zenodo", RECORD_ID, filenames=filenames)

    def test_zenodo_no_kwargs_forwarded(self, zenodo):
        from_source("zenodo", RECORD_ID)
        assert zenodo.kwargs == {}

    def test_zenodo_kwargs_forwarded(self, zenodo):
        from_source("zenodo", RECORD_ID, filenames="a.grib", parts=[(0, 4)], stream=False)
        assert zenodo.kwargs == {"parts": [(0, 4)], "stream": False}


# --------------------------------------------------------------------------------------------
# Live test against the real Zenodo API.
#
# The offline tests above encode two assumptions about Zenodo that no Zenodo documentation
# states: that files[*].links.self carries the download URL, and that the API redirects a
# concept record to its latest version. Only a real request can confirm those still hold.
#
# Deliberately commented out. To enable it, replace the placeholders below with a small,
# permanent record and uncomment. Adapt the assertion to what that record holds; to_fieldlist
# assumes field data such as GRIB or NetCDF. The markers keep it out of the default -E short
# profile, so it runs only with -E long or -E release.
#
# _LIVE_CONCEPT_DOI = "10.5281/zenodo.<concept record ID>"  # all versions, resolves to latest
# _LIVE_VERSION_DOI = "10.5281/zenodo.<version record ID>"  # one specific version
# _LIVE_RECORD_ID = <version record ID>
# _LIVE_FILENAME = "<a file name in that record>"
# _LIVE_FIELD_COUNT = <number of fields in that file>
#
#
# @pytest.mark.long_test
# @pytest.mark.download
# @pytest.mark.parametrize("identifier", [_LIVE_CONCEPT_DOI, _LIVE_VERSION_DOI, _LIVE_RECORD_ID])
# def test_zenodo_live(identifier):
#     ds = from_source("zenodo", identifier, filenames=_LIVE_FILENAME)
#     assert len(ds.to_fieldlist()) == _LIVE_FIELD_COUNT


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
