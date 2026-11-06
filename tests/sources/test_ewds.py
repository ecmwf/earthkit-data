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
from unittest.mock import MagicMock

import pytest
import yaml

from earthkit.data import config, from_source
from earthkit.data.sources import ewds as ewds_module
from earthkit.data.sources.ewds import EWDSAPIKeyPrompt, EWDSRetriever, client

NO_EWDS = not os.path.exists(os.path.expanduser("~/.ewdsapirc"))

RC_CONTENT = {
    "url": "https://ewds.climate.copernicus.eu/api",
    "key": "abcdef01-0000-1111-2222-0123456789ab",
}


@pytest.fixture
def tmp_rcfile(monkeypatch, tmp_path):
    """Point EWDSAPIKeyPrompt.rcfile at a (non-existing) temporary file.

    Ensures the offline tests never read or write the real ~/.ewdsapirc.
    """
    rcfile = tmp_path / ".ewdsapirc"
    monkeypatch.setattr(EWDSAPIKeyPrompt, "rcfile", str(rcfile))
    return rcfile


def test_ewds_positional_request_rejected(tmp_rcfile):
    with pytest.raises(TypeError):
        EWDSRetriever("cems-fire-seasonal", {"variable": "fire_weather_index"})
    with pytest.raises(TypeError):
        from_source("ewds", "cems-fire-seasonal", {"variable": "fire_weather_index"})


def test_ewds_request_as_kwargs_rejected(tmp_rcfile):
    with pytest.raises(TypeError):
        EWDSRetriever("cems-fire-seasonal", variable="fire_weather_index")
    with pytest.raises(TypeError):
        from_source("ewds", "cems-fire-seasonal", variable="fire_weather_index")


def test_ewds_missing_request_rejected(tmp_rcfile):
    with pytest.raises(TypeError):
        EWDSRetriever("cems-fire-seasonal")
    with pytest.raises(TypeError):
        from_source("ewds", "cems-fire-seasonal")


def test_ewds_client_prompt_false_without_rcfile(tmp_rcfile, monkeypatch):
    # prompt=False must never ask the user and raise an error naming the rc file
    assert not tmp_rcfile.exists()
    ask = MagicMock(name="ask_user_and_save")
    monkeypatch.setattr(EWDSAPIKeyPrompt, "ask_user_and_save", ask)
    fake_client = MagicMock(name="cdsapi.Client")
    monkeypatch.setattr(ewds_module.cdsapi, "Client", fake_client)

    with pytest.raises(FileNotFoundError) as ei:
        client(False)

    assert str(tmp_rcfile) in str(ei.value)
    assert "ewdsapirc" in str(ei.value)
    ask.assert_not_called()
    fake_client.assert_not_called()


def test_ewds_client_prompt_true_without_rcfile_asks(tmp_rcfile, monkeypatch):
    def write_rc():
        with open(tmp_rcfile, "w") as f:
            yaml.dump(RC_CONTENT, f)

    ask = MagicMock(name="ask_user_and_save", side_effect=write_rc)
    monkeypatch.setattr(EWDSAPIKeyPrompt, "ask_user_and_save", ask)
    fake_client = MagicMock(name="cdsapi.Client")
    monkeypatch.setattr(ewds_module.cdsapi, "Client", fake_client)

    c = client(True)

    ask.assert_called_once_with()
    fake_client.assert_called_once_with(url=RC_CONTENT["url"], key=RC_CONTENT["key"])
    assert c is fake_client.return_value


@pytest.mark.parametrize("use_prompt", [True, False])
def test_ewds_client_with_rcfile(tmp_rcfile, monkeypatch, use_prompt):
    with open(tmp_rcfile, "w") as f:
        yaml.dump(RC_CONTENT, f)

    ask = MagicMock(name="ask_user_and_save")
    monkeypatch.setattr(EWDSAPIKeyPrompt, "ask_user_and_save", ask)
    fake_client = MagicMock(name="cdsapi.Client")
    monkeypatch.setattr(ewds_module.cdsapi, "Client", fake_client)

    c = client(use_prompt)

    fake_client.assert_called_once_with(url=RC_CONTENT["url"], key=RC_CONTENT["key"])
    ask.assert_not_called()
    assert c is fake_client.return_value


def test_ewds_retriever_client_forwards_prompt(monkeypatch):
    seen = []
    monkeypatch.setattr(ewds_module, "client", lambda use_prompt: seen.append(use_prompt) or "client")

    # constructed with __new__ to avoid triggering a retrieval; the test only
    # checks that client() forwards self.prompt to the module level client()
    for prompt in (True, False):
        s = EWDSRetriever.__new__(EWDSRetriever)
        s.prompt = prompt
        assert s.client() == "client"

    assert seen == [True, False]


class FakeCDSResult:
    location = "https://ewds.climate.copernicus.eu/api/v2/resources/abcdef01-0000-1111-2222-0123456789ab"

    def download(self, target=None):
        with open(target, "wb") as f:
            f.write(b"fake ewds payload")


class FakeCDSClient:
    def __init__(self):
        self.retrievals = []

    def retrieve(self, dataset, request):
        self.retrievals.append((dataset, dict(request)))
        return FakeCDSResult()


@pytest.mark.parametrize(
    "request_arg,expected",
    [
        (dict(variable="fire_weather_index", year="1991"), [dict(variable="fire_weather_index", year="1991")]),
        (
            [dict(variable="fire_weather_index", year="1991"), dict(variable="burn_burn_days", year="1991")],
            [dict(variable="fire_weather_index", year="1991"), dict(variable="burn_burn_days", year="1991")],
        ),
        (
            (dict(variable="fire_weather_index", year="1991"), dict(variable="burn_burn_days", year="1991")),
            [dict(variable="fire_weather_index", year="1991"), dict(variable="burn_burn_days", year="1991")],
        ),
        (
            dict(variable="fire_weather_index", leadtime_hour=["12", "36"], split_on="leadtime_hour"),
            [
                # RequestBuilder wraps each split value in a tuple (itertools.product)
                dict(variable="fire_weather_index", leadtime_hour=("12",)),
                dict(variable="fire_weather_index", leadtime_hour=("36",)),
            ],
        ),
    ],
    ids=["dict", "list", "tuple", "split_on"],
)
def test_ewds_request_shapes(tmp_rcfile, monkeypatch, tmp_path, request_arg, expected):
    # Offline test: the cdsapi client is mocked so no credentials or network
    # access are needed. The cache is isolated in a temporary directory.
    fake_client = FakeCDSClient()
    monkeypatch.setattr(EWDSRetriever, "client", lambda self: fake_client)

    with config.temporary({"cache-policy": "user", "user-cache-directory": str(tmp_path / "cache")}):
        s = EWDSRetriever("cems-fire-seasonal", request=request_arg)

    assert [r for _, r in fake_client.retrievals] == expected
    assert all(dataset == "cems-fire-seasonal" for dataset, _ in fake_client.retrievals)
    paths = s.path if isinstance(s.path, (list, tuple)) else [s.path]
    assert len(paths) == len(expected)


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_EWDS, reason="No access to EWDS")
@pytest.mark.parametrize("prompt", [True, False])
def test_ewds_grib_prompt(prompt):
    s = from_source(
        "ewds",
        "cems-fire-seasonal",
        request=dict(
            variable="fire_weather_index",
            release_version="5",
            year="1991",
            month="09",
            day="01",
            leadtime_hour="12",
            data_format="grib",
        ),
        prompt=prompt,
    ).to_fieldlist()
    assert len(s) == 25


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_EWDS, reason="No access to EWDS")
def test_ewds_netcdf():
    s = from_source(
        "ewds",
        "cems-fire-seasonal",
        request=dict(
            variable="fire_weather_index",
            release_version="5",
            year="1991",
            month="09",
            day="01",
            leadtime_hour="12",
            data_format="netcdf",
        ),
    ).to_xarray()
    assert "fwinx" in s.data_vars
    assert dict(s["fwinx"].sizes) == {"number": 25, "latitude": 181, "longitude": 360}


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_EWDS, reason="No access to EWDS")
def test_ewds_split_on():
    s = from_source(
        "ewds",
        "cems-fire-seasonal",
        request=dict(
            variable="fire_weather_index",
            release_version="5",
            year="1991",
            month="09",
            day="01",
            leadtime_hour=["12", "36"],
            data_format="grib",
            split_on="leadtime_hour",
        ),
    ).to_fieldlist()
    assert len(s) == 50


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
