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

from earthkit.data import from_source
from earthkit.data.sources import ads as ads_module
from earthkit.data.sources.ads import ADSAPIKeyPrompt, ADSRetriever, client

NO_ADS = not os.path.exists(os.path.expanduser("~/.adsapirc"))

RC_CONTENT = {
    "url": "https://ads.atmosphere.copernicus.eu/api",
    "key": "abcdef01-0000-1111-2222-0123456789ab",
}


@pytest.fixture
def tmp_rcfile(monkeypatch, tmp_path):
    """Point ADSAPIKeyPrompt.rcfile at a (non-existing) temporary file.

    Ensures the offline tests never read or write the real ~/.adsapirc.
    """
    rcfile = tmp_path / ".adsapirc"
    monkeypatch.setattr(ADSAPIKeyPrompt, "rcfile", str(rcfile))
    return rcfile


def test_ads_client_prompt_false_without_rcfile(tmp_rcfile, monkeypatch):
    # prompt=False must never ask the user and raise an error naming the rc file
    assert not tmp_rcfile.exists()
    ask = MagicMock(name="ask_user_and_save")
    monkeypatch.setattr(ADSAPIKeyPrompt, "ask_user_and_save", ask)
    fake_client = MagicMock(name="cdsapi.Client")
    monkeypatch.setattr(ads_module.cdsapi, "Client", fake_client)

    with pytest.raises(FileNotFoundError) as ei:
        client(False)

    assert str(tmp_rcfile) in str(ei.value)
    assert "adsapirc" in str(ei.value)
    ask.assert_not_called()
    fake_client.assert_not_called()


def test_ads_client_prompt_true_without_rcfile_asks(tmp_rcfile, monkeypatch):
    def write_rc():
        with open(tmp_rcfile, "w") as f:
            yaml.dump(RC_CONTENT, f)

    ask = MagicMock(name="ask_user_and_save", side_effect=write_rc)
    monkeypatch.setattr(ADSAPIKeyPrompt, "ask_user_and_save", ask)
    fake_client = MagicMock(name="cdsapi.Client")
    monkeypatch.setattr(ads_module.cdsapi, "Client", fake_client)

    c = client(True)

    ask.assert_called_once_with()
    fake_client.assert_called_once_with(url=RC_CONTENT["url"], key=RC_CONTENT["key"])
    assert c is fake_client.return_value


@pytest.mark.parametrize("use_prompt", [True, False])
def test_ads_client_with_rcfile(tmp_rcfile, monkeypatch, use_prompt):
    with open(tmp_rcfile, "w") as f:
        yaml.dump(RC_CONTENT, f)

    ask = MagicMock(name="ask_user_and_save")
    monkeypatch.setattr(ADSAPIKeyPrompt, "ask_user_and_save", ask)
    fake_client = MagicMock(name="cdsapi.Client")
    monkeypatch.setattr(ads_module.cdsapi, "Client", fake_client)

    c = client(use_prompt)

    fake_client.assert_called_once_with(url=RC_CONTENT["url"], key=RC_CONTENT["key"])
    ask.assert_not_called()
    assert c is fake_client.return_value


def test_ads_retriever_client_forwards_prompt(monkeypatch):
    seen = []
    monkeypatch.setattr(ads_module, "client", lambda use_prompt: seen.append(use_prompt) or "client")

    # constructed with __new__ to avoid triggering a retrieval; the test only
    # checks that client() forwards self.prompt to the module level client()
    for prompt in (True, False):
        s = ADSRetriever.__new__(ADSRetriever)
        s.prompt = prompt
        assert s.client() == "client"

    assert seen == [True, False]


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_ADS, reason="No access to ADS")
@pytest.mark.parametrize("prompt", [True, False])
def test_ads_grib_1_prompt(prompt):
    s = from_source(
        "ads",
        "cams-global-reanalysis-eac4",
        variable=["particulate_matter_10um", "particulate_matter_1um"],
        area=[50, -50, 20, 50],
        date="2012-12-12",
        prompt=prompt,
        time="12:00",
    ).to_fieldlist()
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_ADS, reason="No access to ADS")
def test_ads_grib_2():
    s = from_source(
        "ads",
        "cams-global-reanalysis-eac4",
        variable=["particulate_matter_10um", "particulate_matter_1um"],
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time="12:00",
        split_on="variable",
    ).to_fieldlist()
    assert len(s) == 2


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_ADS, reason="No access to ADS")
def test_ads_grib_3():
    s = from_source(
        "ads",
        "cams-global-reanalysis-eac4",
        variable=["particulate_matter_10um", "particulate_matter_1um"],
        area=[50, -50, 20, 50],
        date="2012-12-12/to/2012-12-15",
        time="12:00",
    ).to_fieldlist()
    assert len(s) == 8


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_ADS, reason="No access to ADS")
def test_ads_netcdf():
    s = from_source(
        "ads",
        "cams-global-reanalysis-eac4",
        variable=["particulate_matter_10um", "particulate_matter_1um"],
        area=[50, -50, 20, 50],
        date="2012-12-12",
        time="12:00",
        format="netcdf",
    ).to_fieldlist()
    assert len(s) == 2


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
