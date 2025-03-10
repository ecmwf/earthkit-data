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

import pytest

from earthkit.data import config
from earthkit.data.core.temporary import temp_directory
from earthkit.data.core.temporary import temp_file


def read_config_yaml(path=os.path.expanduser("~/.config/earthkit/data/config.yaml")):
    try:
        with open(path) as f:
            import yaml

            s = yaml.load(f, Loader=yaml.SafeLoader)
            if not isinstance(s, dict):
                s = {}
            return s
    except Exception:
        return {}


@pytest.mark.parametrize(
    "param,default_value,new_value",
    [
        ("url-download-timeout", 30, 5),
    ],
)
def test_configs_params_set_reset(param, default_value, new_value):
    ori_value = config.get(param)

    with config.temporary():
        config.reset()

        assert config.get(param) == default_value
        config.set(param, new_value)
        assert config.get(param) == new_value
        config.reset()
        assert config.get(param) == default_value

    assert config.get(param) == ori_value


def test_config_invalid():
    # invalid param
    with pytest.raises(KeyError):
        config.get("_invalid_")

    with pytest.raises(KeyError):
        config.set("_invalid_", 1)

    # invalid value
    with pytest.raises(ValueError):
        config.set("url-download-timeout", "A")


@pytest.mark.parametrize(
    "param,set_value,stored_value,raise_error",
    [
        ("number-of-download-threads", "A", "A", ValueError),
        ("url-download-timeout", 30, 30, None),
        ("url-download-timeout", "30", 30, None),
        ("url-download-timeout", "2m", 120, None),
        ("url-download-timeout", "10h", 36000, None),
        ("url-download-timeout", "7d", 7 * 24 * 3600, None),
        ("url-download-timeout", "1x", None, ValueError),
        ("url-download-timeout", "1M", 60, ValueError),
        ("reader-type-check-bytes", 8, 8, None),
        ("reader-type-check-bytes", 1, 1, ValueError),
        ("reader-type-check-bytes", 4097, 4097, ValueError),
    ],
)
def test_config_set_numbers(param, set_value, stored_value, raise_error):
    with config.temporary():
        if raise_error is None:
            config.set(param, set_value)
            assert config.get(param) == stored_value
        else:
            with pytest.raises(raise_error):
                config.set(param, set_value)


def test_config_set_cache_numbers():
    with temp_directory() as tmpdir:
        with config.temporary({"cache-policy": "user", "user-cache-directory": tmpdir}):
            data = [
                ("maximum-cache-size", "1", 1, None),
                ("maximum-cache-size", "1k", 1024, None),
                ("maximum-cache-size", "1kb", 1024, None),
                ("maximum-cache-size", "1k", 1024, None),
                ("maximum-cache-size", "1kb", 1024, None),
                ("maximum-cache-size", "1K", 1024, None),
                ("maximum-cache-size", "1M", 1024 * 1024, None),
                ("maximum-cache-size", "1G", 1024 * 1024 * 1024, None),
                ("maximum-cache-size", "1T", 1024 * 1024 * 1024 * 1024, None),
                ("maximum-cache-size", "1P", 1024 * 1024 * 1024 * 1024 * 1024, None),
                ("maximum-cache-size", None, None, None),
                ("maximum-cache-size", "-1", None, ValueError),
                ("maximum-cache-disk-usage", "2%", 2, None),
                ("maximum-cache-disk-usage", None, None, None),
                ("maximum-cache-disk-usage", "-2%", None, ValueError),
                ("maximum-cache-disk-usage", "102%", 102, None),
                ("maximum-cache-disk-usage", "0%", 0, None),
            ]

            for param, set_value, stored_value, raise_error in data:
                if raise_error is None:
                    config.set(param, set_value)
                    if stored_value is not None:
                        assert config.get(param) == stored_value
                    else:
                        assert config.get(param) is None
                else:
                    with pytest.raises(raise_error):
                        config.set(param, set_value)


def test_config_set_multi():
    with config.temporary():
        config.set("url-download-timeout", 7)
        assert config.get("url-download-timeout") == 7

        config.set({"url-download-timeout": 2, "check-out-of-date-urls": False})
        assert config.get("url-download-timeout") == 2
        assert not config.get("check-out-of-date-urls")

        config.set(url_download_timeout=11, check_out_of_date_urls=False)
        assert config.get("url-download-timeout") == 11
        assert not config.get("check-out-of-date-urls")

        with pytest.raises(KeyError):
            config.set({"url-download-timeout": 2, "-invalid-": 21})

        with pytest.raises(KeyError):
            config.set(url_download_timeout=3, __invalid__=11)


def test_config_temporary_single():
    with config.temporary("url-download-timeout", 7):
        assert config.get("url-download-timeout") == 7

    with config.temporary({"url-download-timeout": 7}):
        assert config.get("url-download-timeout") == 7

    with config.temporary(url_download_timeout=7):
        assert config.get("url-download-timeout") == 7


def test_config_temporary_multi():
    with config.temporary({"url-download-timeout": 2, "check-out-of-date-urls": False}):
        assert config.get("url-download-timeout") == 2
        assert not config.get("check-out-of-date-urls")

    with config.temporary(url_download_timeout=3, check_out_of_date_urls=False):
        assert config.get("url-download-timeout") == 3
        assert not config.get("check-out-of-date-urls")


def test_config_temporary_nested():
    with config.temporary("url-download-timeout", 7):
        assert config.get("url-download-timeout") == 7
        with config.temporary("url-download-timeout", 10):
            assert config.get("url-download-timeout") == 10
        assert config.get("url-download-timeout") == 7


def test_config_temporary_autosave_1():
    with temp_file() as config_file:
        with config.temporary(config_yaml=config_file):
            # now config should contain the default values
            # we ensure that the configs are saved into the file
            config.save_as(config_file)

            key = "url-download-timeout"

            v_ori = config.autosave
            config.autosave = False

            # when a key has a default value, it is not saved into the config file
            s = read_config_yaml(config_file)
            assert key not in s

            v = config.get(key)
            config.set(key, v + 10)
            assert config.get(key) == v + 10

            # the config file should be the same
            s = read_config_yaml(config_file)
            assert key not in s

            config.autosave = v_ori


def test_config_temporary_autosave_2():
    with temp_file() as config_file:
        with config.temporary(config_yaml=config_file):
            # now config should contain the default values
            # we ensure that the config is saved into the file
            config.save_as(config_file)

            key = "url-download-timeout"

            v_ori = config.autosave
            config.autosave = True

            # when a key has a default value, it is not saved into the config file
            s = read_config_yaml(config_file)
            assert key not in s

            v = config.get(key)
            v_new = v + 10
            config.set(key, v_new)
            assert config.get(key) == v_new

            # the file changed
            s = read_config_yaml(config_file)
            assert s[key] == v_new

            config.autosave = False
            config.set(key, v)
            assert config.get(key) == v
            s = read_config_yaml(config_file)
            assert s[key] == v_new

            config.autosave = v_ori


@pytest.mark.parametrize(
    "value,error", [("10000", None), (10000, None), ("1b", ValueError), ("A", ValueError)]
)
def test_config_env(monkeypatch, value, error):
    env_key = "EARTHKIT_DATA_URL_DOWNLOAD_TIMEOUT"
    monkeypatch.setenv(env_key, value)

    # v_ori = config.autosave
    # config.autosave = True

    if error is None:
        v = config.get("url-download-timeout")
        assert v == 10000
    else:
        with pytest.raises(error):
            config.get("url-download-timeout")

    # config.autosave = v_ori


if __name__ == "__main__":
    from earthkit.data.testing import main

    main(__file__)
