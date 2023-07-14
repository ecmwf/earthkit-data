#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import sys

import pytest

from earthkit.data import from_source

NO_POLYTOPE = not os.path.exists(os.path.expanduser("~/.polytopeapirc"))


def test_no_polytope_client(monkeypatch):
    "Check that a useful message is given in the absence of the polytope-client library"
    monkeypatch.setitem(sys.modules, "polytope", None)
    with pytest.raises(ImportError) as excinfo:
        from_source("polytope", None, None)
        assert "pip install polytope-client" in str(excinfo.value)


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_POLYTOPE, reason="No access to Polytope Web API")
def test_polytope_odb():
    request = {
        "database": "fdbdev",
        "class": "rd",
        "type": "oai",
        "stream": "lwda",
        "expver": "xxxx",
        "obsgroup": "CONV",
        "reportype": 16001,
        "obstype": 15,
        "date": [20150601, 20150602],
        "time": "0/to/23/by/1",
        "filter": "'select * where stationid=\"Ams01\"'",
        "domain": "off",
    }

    src = from_source("polytope", "ichange", request)
    df = src.to_pandas()
    assert len(df) == 52
