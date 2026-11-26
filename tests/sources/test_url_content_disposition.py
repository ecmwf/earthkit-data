#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

# Offline reproduction of https://github.com/ecmwf/earthkit-data/issues/1205
#
# The ECPDS server serves GRIB data from an extensionless URL, requires basic
# authentication and answers with "Content-Disposition: inline; filename=...".
# This is mimicked here with a local HTTP server.

import base64
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

import pytest
import requests

from earthkit.data import config, from_source
from earthkit.data.core.temporary import temp_directory
from earthkit.data.utils.testing import earthkit_test_data_file

USER = "USER"
PASSWORD = "PASSWORD"
PATH = "/ecpds/data/file/20261021/AND10210000102100001"
FILENAME = "AND10210000102100001"

INLINE = f'inline; filename="{FILENAME}"'
ATTACHMENT = f'attachment; filename="{FILENAME}"'

EXPECTED_AUTH = "Basic " + base64.b64encode(f"{USER}:{PASSWORD}".encode()).decode()


class _Handler(BaseHTTPRequestHandler):
    protocol_version = "HTTP/1.1"

    def log_message(self, format, *args):
        # silence the request logging
        pass

    def _send_headers(self, status, headers):
        self.send_response(status)
        for k, v in headers.items():
            self.send_header(k, v)
        self.end_headers()

    def _handle(self, send_body):
        if self.headers.get("Authorization") != EXPECTED_AUTH:
            body = b"Unauthorized"
            self._send_headers(
                401,
                {
                    "WWW-Authenticate": 'Basic realm="ecpds"',
                    "Content-Type": "text/plain",
                    "Content-Length": str(len(body)),
                },
            )
            if send_body:
                self.wfile.write(body)
            return

        if self.path != PATH:
            body = b"Not found"
            self._send_headers(404, {"Content-Type": "text/plain", "Content-Length": str(len(body))})
            if send_body:
                self.wfile.write(body)
            return

        data = self.server.data
        self._send_headers(
            200,
            {
                "Content-Length": str(len(data)),
                "Content-Type": "application/octet-stream",
                "Content-Disposition": self.server.content_disposition,
            },
        )
        if send_body:
            self.wfile.write(data)

    def do_HEAD(self):
        self._handle(False)

    def do_GET(self):
        self._handle(True)


@pytest.fixture
def grib_path():
    return earthkit_test_data_file("test_single.grib")


@pytest.fixture
def mock_server(grib_path, monkeypatch):
    """Local mock of the ECPDS server. The Content-Disposition header can be set through the
    ``content_disposition`` attribute of the yielded server.
    """
    # make sure no proxy is used to reach the local server
    monkeypatch.setenv("no_proxy", "127.0.0.1")
    monkeypatch.setenv("NO_PROXY", "127.0.0.1")

    with open(grib_path, "rb") as f:
        data = f.read()

    server = ThreadingHTTPServer(("127.0.0.1", 0), _Handler)
    server.daemon_threads = True
    server.data = data
    server.content_disposition = ATTACHMENT

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield server
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


def _url(server):
    host, port = server.server_address[:2]
    return f"http://{host}:{port}{PATH}"


def _shortnames(ds):
    return [f.get("metadata.shortName") for f in ds]


@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("content_disposition", [INLINE, ATTACHMENT], ids=["inline", "attachment"])
def test_url_content_disposition_auth(mock_server, grib_path, content_disposition, stream):
    mock_server.content_disposition = content_disposition

    ref = from_source("file", grib_path).to_fieldlist()
    ref_names = _shortnames(ref)
    assert len(ref) > 0

    with temp_directory() as tmpdir:
        with config.temporary({"cache-policy": "off", "temporary-cache-directory-root": tmpdir}):
            ds = from_source("url", _url(mock_server), auth=(USER, PASSWORD), stream=stream).to_fieldlist()

            if stream:
                names = _shortnames(ds)
                count = len(names)
            else:
                count = len(ds)
                names = _shortnames(ds)

            assert count == len(ref)
            assert names == ref_names


@pytest.mark.parametrize("stream", [False, True])
@pytest.mark.parametrize("content_disposition", [INLINE, ATTACHMENT], ids=["inline", "attachment"])
def test_url_content_disposition_no_auth(mock_server, content_disposition, stream):
    mock_server.content_disposition = content_disposition

    with temp_directory() as tmpdir:
        with config.temporary({"cache-policy": "off", "temporary-cache-directory-root": tmpdir}):
            with pytest.raises(requests.HTTPError) as exc_info:
                ds = from_source("url", _url(mock_server), stream=stream).to_fieldlist()
                # no data must be returned
                _shortnames(ds)

            assert exc_info.value.response.status_code == 401
