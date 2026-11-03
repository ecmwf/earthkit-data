#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import datetime
import inspect
import os
import types

import pytest

from earthkit.data import config, from_source
from earthkit.data.utils.testing import NO_EOD

try:
    import ecmwf.opendata
except ImportError:
    ecmwf = None

YESTERDAY = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%Y%m%d")

REQ_1 = dict(
    param="t",
    levelist=500,
    date=YESTERDAY,
)

REQ_2 = dict(
    param="r",
    levelist=500,
    date=YESTERDAY,
)


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_EOD, reason="No access to EOD")
def test_eod_single_1():
    ds = from_source(
        "ecmwf-open-data",
        param=["2t", "msl"],
        levtype="sfc",
    ).to_fieldlist()
    assert len(ds) == 2
    assert ds.metadata("param") == ["2t", "msl"]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_EOD, reason="No access to EOD")
@pytest.mark.parametrize(
    "_args,req,_kwargs",
    [
        ((REQ_1,), None, {}),
        (([REQ_1]), None, {}),
        ((), REQ_1, {}),
        ((), [REQ_1], {}),
        ((), None, REQ_1),
    ],
)
def test_eod_single_2(_args, req, _kwargs):
    ds = from_source(
        "ecmwf-open-data",
        *_args,
        request=req,
        **_kwargs,
    ).to_fieldlist()
    assert len(ds) == 1
    assert ds[0].metadata(["param", "level"]) == ["t", 500]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.parametrize("_args,req,_kwargs", [((REQ_1, REQ_2), None, {}), ((), [REQ_1, REQ_2], {})])
@pytest.mark.skipif(NO_EOD, reason="No access to EOD")
def test_eod_multi_1(_args, req, _kwargs):
    ds = from_source(
        "ecmwf-open-data",
        *_args,
        request=req,
        **_kwargs,
    ).to_fieldlist()
    assert len(ds) == 2
    assert ds.metadata("param") == ["t", "r"]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_EOD, reason="No access to EOD")
@pytest.mark.parametrize("model", ["ifs"])  # "aifs" does not seem to work
def test_eod_model(model):
    ds = from_source(
        "ecmwf-open-data",
        model=model,
        param="t",
        date=YESTERDAY,
        levelist=500,
    ).to_fieldlist()
    assert len(ds) == 1
    assert ds[0].metadata(["param", "level"]) == ["t", 500]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_EOD, reason="No access to EOD")
def test_eod_client_options():
    ds = from_source(
        "ecmwf-open-data",
        request=dict(param="2t", step=0, levtype="sfc"),
        maximum_retries=3,
        retry_after=10,
    ).to_fieldlist()
    assert len(ds) == 1
    assert ds.metadata("param") == ["2t"]


# ---------------------------------------------------------------------------
# Offline tests using a fake ecmwf.opendata.Client
# ---------------------------------------------------------------------------


class FakeClient:
    """Fake ecmwf.opendata.Client recording its init arguments and the retrieved requests."""

    instances = []

    def __init__(self, **kwargs):
        self.init_kwargs = kwargs
        self.model = kwargs.get("model", "ifs")
        self.resol = kwargs.get("resol", "0p25")
        self.source = types.SimpleNamespace(url=f"https://fake.example.com/{kwargs.get('source', 'ecmwf')}")
        self.beta = kwargs.get("beta", False)
        self.infer_stream_keyword = kwargs.get("infer_stream_keyword", True)
        self.preserve_request_order = kwargs.get("preserve_request_order", False)
        self.requests = []
        FakeClient.instances.append(self)

    def retrieve(self, request, target):
        self.requests.append(dict(request))
        with open(target, "wb") as f:
            f.write(b"GRIB")


@pytest.fixture
def fake_client(monkeypatch, tmp_path):
    if ecmwf is None:
        pytest.skip("ecmwf-opendata is not installed")

    # the source determines the client options from the signature of the real client
    FakeClient.__init__.__signature__ = inspect.signature(ecmwf.opendata.Client.__init__)
    FakeClient.instances = []
    monkeypatch.setattr(ecmwf.opendata, "Client", FakeClient)

    # the cache must be empty so that the fake client is always used
    with config.temporary({"cache-policy": "user", "user-cache-directory": str(tmp_path / "cache")}):
        yield FakeClient


def _eod(*args, **kwargs):
    ds = from_source("ecmwf-open-data", *args, **kwargs)
    client = FakeClient.instances[-1]
    return ds, client


@pytest.mark.parametrize(
    "_args,req,_kwargs",
    [
        ((), dict(param="2t", step=0), {}),
        ((), None, dict(param="2t", step=0)),
        ((dict(param="2t", step=0),), None, {}),
    ],
)
def test_eod_offline_client_options(fake_client, _args, req, _kwargs):
    ds, client = _eod(
        *_args,
        request=req,
        maximum_retries=3,
        retry_after=10,
        use_server_retry_after=False,
        **_kwargs,
    )

    assert client.init_kwargs["maximum_retries"] == 3
    assert client.init_kwargs["retry_after"] == 10
    assert client.init_kwargs["use_server_retry_after"] is False
    assert client.requests == [dict(param="2t", step=0)]
    assert os.path.isfile(ds.path)


def test_eod_offline_client_option_names():
    if ecmwf is None:
        pytest.skip("ecmwf-opendata is not installed")

    from earthkit.data.sources.ecmwf_open_data import _client_option_names

    params = inspect.signature(ecmwf.opendata.Client.__init__).parameters
    expected = set(params) - {"self", "source", "model", "resol"}
    assert _client_option_names() == expected
    assert {"maximum_retries", "retry_after", "use_server_retry_after", "beta"} <= expected


def test_eod_offline_model_source(fake_client):
    _, client = _eod(request=dict(param="2t", step=0), model="aifs-single", source="azure")
    assert client.init_kwargs["model"] == "aifs-single"
    assert client.init_kwargs["source"] == "azure"
    assert client.requests == [dict(param="2t", step=0)]


def test_eod_offline_resol_argument(fake_client):
    # given at top level: passed to the client and not in the request
    _, client = _eod(request=dict(param="2t", step=0), resol="0p5")
    assert client.init_kwargs["resol"] == "0p5"
    assert client.resol == "0p5"
    assert client.requests == [dict(param="2t", step=0)]

    # also when the request is given as top level keywords
    _, client = _eod(param="2t", step=0, resol="0p25")
    assert client.init_kwargs["resol"] == "0p25"
    assert client.requests == [dict(param="2t", step=0)]


def test_eod_offline_resol_default(fake_client):
    # not given: the client is created with the default resol
    _, client = _eod(request=dict(param="2t", step=0))
    assert client.init_kwargs["resol"] == "0p25"
    assert client.resol == "0p25"
    assert client.requests == [dict(param="2t", step=0)]


def test_eod_offline_resol_in_request_stays_in_request(fake_client):
    # request= dict
    _, client = _eod(request=dict(param="2t", step=0, resol="0p5"))
    assert client.init_kwargs["resol"] == "0p25"
    assert client.requests == [dict(param="2t", step=0, resol="0p5")]

    # positional dict
    _, client = _eod(dict(param="msl", step=0, resol="0p5"))
    assert client.init_kwargs["resol"] == "0p25"
    assert client.requests == [dict(param="msl", step=0, resol="0p5")]

    # the request value coexists with the client argument
    _, client = _eod(request=dict(param="2t", step=0, resol="0p25"), resol="0p5")
    assert client.init_kwargs["resol"] == "0p5"
    assert client.requests == [dict(param="2t", step=0, resol="0p25")]


@pytest.mark.parametrize("name", ["maximum_retries", "retry_after", "beta", "preserve_request_order"])
def test_eod_offline_option_names_in_request_stay_in_request(fake_client, name):
    # request= dict
    _, client = _eod(request=dict(param="2t", step=0, **{name: 7}))
    assert client.init_kwargs.get(name) != 7
    assert client.init_kwargs["preserve_request_order"] is True
    assert client.requests == [dict(param="2t", step=0, **{name: 7})]

    # positional dict
    _, client = _eod(dict(param="msl", step=0, **{name: 7}))
    assert client.init_kwargs.get(name) != 7
    assert client.init_kwargs["preserve_request_order"] is True
    assert client.requests == [dict(param="msl", step=0, **{name: 7})]


def test_eod_offline_preserve_request_order(fake_client):
    # default
    _, client = _eod(request=dict(param="2t", step=0))
    assert client.init_kwargs["preserve_request_order"] is True

    # user value
    _, client = _eod(request=dict(param="2t", step=0), preserve_request_order=False)
    assert client.init_kwargs["preserve_request_order"] is False
    assert client.requests == [dict(param="2t", step=0)]


def test_eod_offline_cache_key(fake_client):
    req = dict(param="2t", step=0)

    def path(**kwargs):
        ds, _ = _eod(request=req, **kwargs)
        return ds.path

    ref = path()

    # transport-only options do not change the cache path
    assert path(maximum_retries=3) == ref
    assert path(retry_after=10, use_server_retry_after=False) == ref
    assert path(maximum_retries=1, retry_after=1, verify=False, debug=True) == ref

    # options changing the data change the cache path
    paths = {
        ref,
        path(beta=True),
        path(infer_stream_keyword=False),
        path(preserve_request_order=False),
        path(model="aifs-single"),
        path(source="azure"),
        path(resol="0p5"),
    }
    assert len(paths) == 7


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
