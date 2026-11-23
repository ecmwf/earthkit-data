#!/usr/bin/env python3

# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import base64
import datetime
import json
import logging
import os
import pathlib
import threading
import time
from unittest.mock import MagicMock

import numpy as np
import pytest

copernicusmarine = pytest.importorskip("copernicusmarine")

from copernicusmarine.core_functions import credentials_utils  # noqa: E402

from earthkit.data import cache, config, from_source  # noqa: E402
from earthkit.data.sources import cmems as cm_source  # noqa: E402
from earthkit.data.sources import prompt as prompt_module  # noqa: E402
from earthkit.data.sources.cmems import (  # noqa: E402
    CREDENTIAL_KEYS,
    CMEMSAPIKeyPrompt,
    InteractivePromptError,
    LibraryCompatibilityError,
    _no_interactive_prompt,
)
from earthkit.data.utils.testing import NO_CMEMS  # noqa: E402

# Re-use the CDS timeout command line option (--cds-timeout) for the live tests
CM_TIMEOUT = pytest.CDS_TIMEOUT

# The cache owner is derived from the class name (CMEMSRetriever) by
# earthkit.data.sources.base when the source downloads
OWNER = "c-memsretriever"

# IBI (Iberia-Biscay-Ireland) multiyear reanalysis: monthly mean 3D physical variables, 0.027 degrees
DATASET = "cmems_mod_ibi_phy-temp_my_0.027deg_P1M-m"

# A tiny subset used by all offline tests
BASE_REQUEST = dict(
    variables=["thetao"],
    minimum_longitude=-9.0,
    maximum_longitude=-8.9,
    minimum_latitude=42.0,
    maximum_latitude=42.1,
    start_datetime="2020-01-01T00:00:00",
    end_datetime="2020-01-02T00:00:00",
    minimum_depth=0.0,
    maximum_depth=1.0,
)

FAKE_USERNAME = "fake-username"
FAKE_PASSWORD = "fake-password-super-secret"

# The mocked downloads can run in parallel download threads. netCDF4/HDF5
# writes from several threads at once crash (segfault) in this environment,
# so the fake writer serialises them: what the tests exercise is the source
# machinery under parallelism, not the thread safety of the netCDF library.
FAKE_WRITE_LOCK = threading.Lock()


def make_source(**overrides):
    """Build a request dictionary with the default tiny subset."""
    request = dict(BASE_REQUEST)
    request.update(overrides)
    return request


class FakeResponse:
    """Mimics ``copernicusmarine.core_functions.models.ResponseSubset``: the
    ``file_path`` is relative to ``output_directory``.
    """

    def __init__(self, output_directory, filename):
        self.output_directory = pathlib.Path(output_directory)
        self.filename = filename
        self.file_path = pathlib.Path(filename)


def write_fake_netcdf(path, variables):
    import xarray as xr

    ds = xr.Dataset(
        {
            name: (["time", "latitude", "longitude"], np.arange(4.0).reshape(1, 2, 2) + i)
            for i, name in enumerate(variables)
        },
        coords=dict(
            time=[np.datetime64("2020-01-01")],
            latitude=[42.0, 42.1],
            longitude=[-9.0, -8.9],
        ),
    )
    ds.to_netcdf(path)


def write_fake_csv(path, variables):
    import pandas as pd

    n = 4
    df = pd.DataFrame({
        "time": ["2020-01-01"] * n,
        "latitude": [42.0, 42.0, 42.1, 42.1],
        "longitude": [-9.0, -8.9, -9.0, -8.9],
        "depth": [0.0] * n,
        **{name: [1.0 + i] * n for i, name in enumerate(variables)},
    })
    df.to_csv(path, index=False)


class FakeSubset:
    """Mimics ``copernicusmarine.subset``: appends the format extension to
    ``output_filename`` when it is missing, writes a small NetCDF or CSV file
    into ``output_directory`` (never into the cache target) and returns a
    response object with a relative ``file_path``.

    When ``error`` is set the file is not written and the error is raised
    after the output directory has been recorded, mimicking a failed download.
    """

    EXTENSIONS = {"netcdf": ".nc", "csv": ".csv"}

    def __init__(self, error=None):
        self.error = error
        self.calls = []
        self.output_directories = []

    def __call__(self, **kwargs):
        self.calls.append(dict(kwargs))

        # the source no longer accepts credentials: they must never be
        # forwarded to the library
        for key in CREDENTIAL_KEYS:
            assert key not in kwargs, f"{key} must not be passed to subset()"

        file_format = kwargs.get("file_format") or "netcdf"
        output_directory = kwargs["output_directory"]
        self.output_directories.append(str(output_directory))

        assert os.path.isdir(output_directory), f"output_directory does not exist: {output_directory}"
        assert not os.path.isabs(kwargs["output_filename"]), "output_filename must be a name, not a target path"

        if self.error is not None:
            raise self.error

        filename = kwargs["output_filename"]
        extension = self.EXTENSIONS[file_format]
        if not filename.endswith(extension):
            filename += extension

        path = os.path.join(output_directory, filename)
        variables = kwargs.get("variables") or ["fake_variable"]
        with FAKE_WRITE_LOCK:
            if file_format == "csv":
                write_fake_csv(path, variables)
            else:
                write_fake_netcdf(path, variables)

        return FakeResponse(output_directory, filename)


@pytest.fixture
def fake_subset(monkeypatch):
    fake = FakeSubset()
    monkeypatch.setattr(copernicusmarine, "subset", fake)
    return fake


@pytest.fixture
def no_subset(monkeypatch):
    """Patch ``subset`` so that any attempt to download fails the test."""

    def fail(*args, **kwargs):
        raise AssertionError("copernicusmarine.subset() should not have been called")

    monkeypatch.setattr(copernicusmarine, "subset", fail)


@pytest.fixture
def cm_cache(tmp_path):
    """Isolate the cache in a temporary directory."""
    with config.temporary({"cache-policy": "user", "user-cache-directory": str(tmp_path / "cache")}):
        yield tmp_path / "cache"


@pytest.fixture
def cm_cache_two_threads(tmp_path):
    """Isolated cache with parallel downloads enabled (the retriever falls
    back to a sequential path with a single thread).
    """
    with config.temporary({
        "cache-policy": "user",
        "user-cache-directory": str(tmp_path / "cache"),
        "number-of-download-threads": 2,
    }):
        yield tmp_path / "cache"


@pytest.fixture
def no_credentials(monkeypatch, tmp_path):
    """Ensure no credentials can be found: no credentials file (the default
    location is redirected to an empty temporary directory, HOME is also
    overwritten) and no environment variables. The real ~/.copernicusmarine
    directory is never read.
    """
    monkeypatch.delenv(cm_source.USERNAME_ENV, raising=False)
    monkeypatch.delenv(cm_source.PASSWORD_ENV, raising=False)
    monkeypatch.setenv(cm_source.CREDENTIALS_DIRECTORY_ENV, str(tmp_path / "missing-credentials-dir"))
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setenv("USERPROFILE", str(tmp_path))


@pytest.fixture
def credentials_in_env(no_credentials, monkeypatch):
    """Credentials are available through the environment variables, no
    credentials file exists.
    """
    monkeypatch.setenv(cm_source.USERNAME_ENV, FAKE_USERNAME)
    monkeypatch.setenv(cm_source.PASSWORD_ENV, FAKE_PASSWORD)


class FakeLogin:
    """Stands in for ``copernicusmarine.login``: records the calls and never
    touches the network or a real credentials file.
    """

    def __init__(self, result=True):
        self.result = result
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(dict(kwargs))
        return self.result


@pytest.fixture
def fake_login(monkeypatch):
    fake = FakeLogin()
    monkeypatch.setattr(copernicusmarine, "login", fake)
    return fake


@pytest.fixture
def fake_prompt(monkeypatch):
    """Replace the user input of the credentials prompt: records the number
    of times the user was asked and returns the fake credentials.
    """
    calls = []

    def ask_user(self):
        calls.append(1)
        return dict(username=FAKE_USERNAME, password=FAKE_PASSWORD)

    monkeypatch.setattr(CMEMSAPIKeyPrompt, "ask_user", ask_user)
    return calls


@pytest.fixture
def fake_answers(monkeypatch, capsys):
    """Patch the user input functions (``input`` and ``getpass``) used by the
    earthkit prompt machinery, so that the real prompt classes can be
    exercised without interactive input. Returns the recorder.
    """

    class Answers:
        def __init__(self):
            self.methods = []

    recorder = Answers()

    def fake_input(message):
        recorder.methods.append(("input", message))
        return FAKE_USERNAME

    def fake_getpass(message):
        recorder.methods.append(("getpass", message))
        return FAKE_PASSWORD

    monkeypatch.setitem(prompt_module.__dict__, "input", fake_input)
    monkeypatch.setattr(prompt_module, "getpass", fake_getpass)
    return recorder


@pytest.fixture
def library_without_env_credentials(monkeypatch):
    """The copernicusmarine library captures the credential environment
    variables into module constants when it is imported, so clearing the
    environment is not enough: make sure the constants are empty in the tests.
    """
    monkeypatch.setattr(credentials_utils, "COPERNICUSMARINE_SERVICE_USERNAME", None, raising=False)
    monkeypatch.setattr(credentials_utils, "COPERNICUSMARINE_SERVICE_PASSWORD", None, raising=False)


@pytest.fixture
def fail_on_click_prompt(monkeypatch):
    """Make any attempt of the library to prompt interactively a visible
    failure instead of a hang. The source's prompt guard must stop the
    library before it ever reaches ``click.prompt``.
    """

    def prompt(*args, **kwargs):
        raise AssertionError("copernicusmarine tried to prompt for credentials")

    monkeypatch.setattr(credentials_utils.click, "prompt", prompt)


def write_fake_credentials_file(path, username="", password=""):
    """Write a credentials file in the base64 encoded INI format used by the
    copernicusmarine library, by default with empty fields.
    """
    content = f"[credentials]\nusername={username}\npassword={password}\n"
    encoded = base64.standard_b64encode(content.encode("utf-8")).decode("utf-8")
    path.write_text(encoded, encoding="ascii")


class SubsetResolvingCredentials:
    """Mimics the credential handling of ``copernicusmarine.subset``: it
    resolves the username and the password with the real library functions
    (no validation, no download, no network), so an incomplete set of
    credentials reaches the library's interactive prompt. If the prompt guard
    does not stop it the fake fails the test.
    """

    def __init__(self):
        self.calls = []

    def __call__(self, **kwargs):
        self.calls.append(dict(kwargs))
        username, password = credentials_utils.get_username_password(None, None, None)
        raise AssertionError(
            f"the library unexpectedly resolved credentials: username={bool(username)} password={bool(password)}"
        )


def cm_entries():
    return [e for e in cache.entries() if e["owner"] == OWNER]


def one_cm_entry():
    entries = cm_entries()
    assert len(entries) == 1, f"expected exactly one cmems cache entry, got {len(entries)}"
    return entries[0]


def no_password_in_logs(caplog):
    for record in caplog.records:
        assert FAKE_PASSWORD not in record.getMessage()


# ---------------------------------------------------------------------------
# offline tests: mocked subset, isolated cache, no network and no credentials
# ---------------------------------------------------------------------------


def test_cmems_netcdf(fake_subset, cm_cache, credentials_in_env):
    # the mocked subset only writes into a temporary directory, so the move
    # onto the exact cache target is exercised here
    ds = from_source("cmems", DATASET, request=make_source())

    path = ds.path
    assert isinstance(path, str)
    assert path.endswith(".nc")
    assert os.path.isfile(path)
    assert os.path.getsize(path) > 0

    xx = ds.to_xarray()
    assert "thetao" in xx.data_vars

    assert len(fake_subset.calls) == 1


@pytest.mark.parametrize("key", ["dataset", "dataset_id"])
def test_cmems_request_dict_with_dataset_key(fake_subset, cm_cache, credentials_in_env, key):
    # a "dataset" or "dataset_id" key equal to the argument is accepted;
    # subset() only ever receives "dataset_id"
    ds = from_source("cmems", DATASET, request=dict(**{key: DATASET}, **make_source()))
    assert ds.path.endswith(".nc")
    assert os.path.isfile(ds.path)
    assert "thetao" in ds.to_xarray().data_vars
    assert len(fake_subset.calls) == 1
    assert fake_subset.calls[0]["dataset_id"] == DATASET
    assert "dataset" not in fake_subset.calls[0]


def test_cmems_request_dict_with_both_dataset_keys(fake_subset, cm_cache, credentials_in_env):
    # both spellings present, both matching the argument: accepted
    ds = from_source("cmems", DATASET, request=dict(dataset=DATASET, dataset_id=DATASET, **make_source()))
    assert ds.path.endswith(".nc")
    assert len(fake_subset.calls) == 1
    assert fake_subset.calls[0]["dataset_id"] == DATASET
    assert "dataset" not in fake_subset.calls[0]


def test_cmems_request_passthrough(fake_subset, cm_cache, credentials_in_env):
    request = make_source(
        variables=["thetao", "so"],
        # datetime objects are normalised to strings
        start_datetime=datetime.datetime(2020, 1, 1, 0, 0),
        end_datetime=datetime.datetime(2020, 1, 2, 0, 0),
    )
    ds = from_source("cmems", DATASET, request=request)

    assert len(fake_subset.calls) == 1
    call = fake_subset.calls[0]

    assert call["dataset_id"] == DATASET
    assert call["variables"] == ["thetao", "so"]
    assert call["start_datetime"] == "2020-01-01T00:00:00"
    assert call["end_datetime"] == "2020-01-02T00:00:00"
    assert call["minimum_longitude"] == -9.0
    assert call["maximum_longitude"] == -8.9
    assert call["minimum_latitude"] == 42.0
    assert call["maximum_latitude"] == 42.1
    assert call["minimum_depth"] == 0.0
    assert call["maximum_depth"] == 1.0

    # keys controlled by the source
    assert call["file_format"] == "netcdf"
    assert call["output_filename"] == "cmems-subset.nc"
    assert call["overwrite"] is True
    assert call["disable_progress_bar"] is True
    # subset() was pointed at a temporary directory, not at the cache target
    assert os.path.basename(call["output_directory"]).startswith("cmems-")

    # the response was moved onto the cache target
    assert ds.path.endswith(".nc")
    assert os.path.isfile(ds.path)

    # the stored cache arguments match the request and never contain the
    # credentials taken from the environment
    entry = one_cm_entry()
    assert entry["path"] == ds.path
    assert entry["args"]["dataset_id"] == DATASET
    assert entry["args"]["start_datetime"] == "2020-01-01T00:00:00"
    serialised = json.dumps(entry["args"])
    assert FAKE_USERNAME not in serialised
    assert FAKE_PASSWORD not in serialised


def test_cmems_request_list(fake_subset, cm_cache, credentials_in_env):
    ds = from_source(
        "cmems",
        DATASET,
        request=[make_source(variables=["thetao"]), make_source(variables=["so"])],
    )
    assert len(fake_subset.calls) == 2
    paths = ds.path if isinstance(ds.path, list) else [ds.path]
    assert len(paths) == 2
    assert len(cm_entries()) == 2


def test_cmems_split_on(fake_subset, cm_cache, credentials_in_env):
    from_source(
        "cmems",
        DATASET,
        request=make_source(variables=["thetao", "so"], split_on="variables"),
    )
    assert len(fake_subset.calls) == 2
    assert [c["variables"] for c in fake_subset.calls] == [("thetao",), ("so",)]


def test_cmems_cache_reuse(fake_subset, cm_cache, credentials_in_env):
    ds1 = from_source("cmems", DATASET, request=make_source())
    ds2 = from_source("cmems", DATASET, request=make_source())

    assert ds1.path == ds2.path
    assert len(fake_subset.calls) == 1
    assert len(cm_entries()) == 1

    # a different request is a different cache entry
    ds3 = from_source("cmems", DATASET, request=make_source(minimum_depth=1.0))
    assert ds3.path != ds1.path
    assert len(fake_subset.calls) == 2
    assert len(cm_entries()) == 2


def test_cmems_cache_hit_without_credentials(fake_subset, cm_cache, credentials_in_env, monkeypatch):
    # populate the cache with credentials available in the environment
    ds1 = from_source("cmems", DATASET, request=make_source())
    assert len(fake_subset.calls) == 1

    # remove the credentials: a cache hit works without them and never prompts
    monkeypatch.delenv(cm_source.USERNAME_ENV)
    monkeypatch.delenv(cm_source.PASSWORD_ENV)
    ask = MagicMock(name="ask_user_and_save")
    monkeypatch.setattr(CMEMSAPIKeyPrompt, "ask_user_and_save", ask)

    ds2 = from_source("cmems", DATASET, request=make_source(), prompt=False)
    assert ds2.path == ds1.path
    assert len(fake_subset.calls) == 1
    ask.assert_not_called()


@pytest.mark.parametrize("form", ["positional", "keyword", "request-dataset", "request-dataset-id"])
def test_cmems_dataset_forms(fake_subset, cm_cache, credentials_in_env, form):
    if form == "positional":
        ds = from_source("cmems", DATASET, request=make_source())
    elif form == "keyword":
        ds = from_source("cmems", dataset=DATASET, request=make_source())
    elif form == "request-dataset":
        ds = from_source("cmems", DATASET, request=dict(dataset=DATASET, **make_source()))
    else:
        ds = from_source("cmems", DATASET, request=dict(dataset_id=DATASET, **make_source()))

    assert ds.path.endswith(".nc")
    assert os.path.isfile(ds.path)
    assert len(fake_subset.calls) == 1
    assert fake_subset.calls[0]["dataset_id"] == DATASET
    assert "dataset" not in fake_subset.calls[0]


def test_cmems_dataset_id_keyword_rejected(cm_cache, credentials_in_env, no_subset):
    # the argument is named "dataset"; the library option name is not accepted
    with pytest.raises(TypeError):
        from_source("cmems", dataset_id=DATASET, request=make_source())
    with pytest.raises(TypeError):
        cm_source.CMEMSRetriever(dataset_id=DATASET, request=make_source())


@pytest.mark.parametrize("key", ["dataset", "dataset_id"])
def test_cmems_dataset_conflict(cm_cache, credentials_in_env, no_subset, key):
    with pytest.raises(ValueError, match=f"conflicting values for '{key}'"):
        from_source("cmems", DATASET, request=dict(**{key: "dataset-two"}, **make_source()))

    with pytest.raises(ValueError, match=f"conflicting values for '{key}'"):
        from_source(
            "cmems",
            DATASET,
            request=[make_source(), dict(**{key: "dataset-two"}, **make_source(variables=["so"]))],
        )


def test_cmems_dataset_conflict_both_keys(cm_cache, credentials_in_env, no_subset):
    # both spellings present: a conflict on either one is an error
    with pytest.raises(ValueError, match="conflicting values for 'dataset'"):
        from_source("cmems", DATASET, request=dict(dataset="dataset-two", dataset_id=DATASET, **make_source()))
    with pytest.raises(ValueError, match="conflicting values for 'dataset_id'"):
        from_source("cmems", DATASET, request=dict(dataset=DATASET, dataset_id="dataset-two", **make_source()))


def test_cmems_dataset_conflict_no_leak(cm_cache, credentials_in_env, no_subset):
    # the values are dataset ids, they may be reported but the request is not
    # otherwise touched; check the positional one is in the message
    with pytest.raises(ValueError) as excinfo:
        from_source("cmems", DATASET, request=dict(dataset_id="dataset-two", **make_source()))
    assert DATASET in str(excinfo.value)
    assert "dataset-two" in str(excinfo.value)


def test_cmems_missing_selection(cm_cache, credentials_in_env, no_subset):
    with pytest.raises(ValueError, match="missing subset selection"):
        from_source("cmems", DATASET, request=dict(dataset_id=DATASET))


@pytest.mark.parametrize("key", CREDENTIAL_KEYS)
def test_cmems_credential_keys_rejected(cm_cache, credentials_in_env, no_subset, key):
    # credentials are not accepted in the request any more; the values must
    # not leak into the error message
    secret = f"secret-{key}-value"
    with pytest.raises(ValueError) as excinfo:
        from_source("cmems", DATASET, request=make_source(**{key: secret}))

    assert f"the {key!r} parameter is not supported" in str(excinfo.value)
    assert secret not in str(excinfo.value)
    assert cm_entries() == []


def test_cmems_credential_kwargs_rejected(cm_cache, credentials_in_env, no_subset):
    with pytest.raises(TypeError):
        from_source("cmems", DATASET, request=make_source(), username=FAKE_USERNAME)
    with pytest.raises(TypeError):
        from_source("cmems", DATASET, request=make_source(), password=FAKE_PASSWORD)
    with pytest.raises(TypeError):
        from_source("cmems", DATASET, request=make_source(), credentials_file="some-file")


# ---------------------------------------------------------------------------
# signature: dataset positional, request required keyword-only, nothing else
# ---------------------------------------------------------------------------


def test_cmems_signature():
    import inspect

    params = inspect.signature(cm_source.CMEMSRetriever.__init__).parameters
    assert list(params) == ["self", "dataset", "request", "prompt"]
    assert params["dataset"].kind is inspect.Parameter.POSITIONAL_OR_KEYWORD
    assert params["request"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["request"].default is inspect.Parameter.empty
    assert params["prompt"].kind is inspect.Parameter.KEYWORD_ONLY
    assert params["prompt"].default is True


def test_cmems_positional_request_rejected(cm_cache, credentials_in_env, no_subset):
    with pytest.raises(TypeError):
        cm_source.CMEMSRetriever(DATASET, make_source())
    with pytest.raises(TypeError):
        from_source("cmems", DATASET, make_source())


def test_cmems_extra_kwargs_rejected(cm_cache, credentials_in_env, no_subset):
    with pytest.raises(TypeError):
        cm_source.CMEMSRetriever(DATASET, request=make_source(), variables=["thetao"])
    with pytest.raises(TypeError):
        from_source("cmems", DATASET, request=make_source(), dataset_version="202511")


def test_cmems_missing_request_rejected(cm_cache, credentials_in_env, no_subset):
    with pytest.raises(TypeError):
        cm_source.CMEMSRetriever(DATASET)
    with pytest.raises(TypeError):
        from_source("cmems", DATASET)


def test_cmems_missing_dataset_rejected(cm_cache, credentials_in_env, no_subset):
    with pytest.raises(TypeError):
        cm_source.CMEMSRetriever(request=make_source())
    with pytest.raises(TypeError):
        from_source("cmems", request=make_source())


def test_cmems_dataset_must_be_a_string(cm_cache, credentials_in_env, no_subset):
    with pytest.raises(TypeError, match="dataset must be a string"):
        from_source("cmems", 42, request=make_source())


def test_cmems_request_must_be_dictionaries(cm_cache, credentials_in_env, no_subset):
    with pytest.raises(TypeError, match="requests must be dictionaries"):
        from_source("cmems", DATASET, request="thetao")
    with pytest.raises(TypeError, match="requests must be dictionaries"):
        from_source("cmems", DATASET, request=[make_source(), "thetao"])


# ---------------------------------------------------------------------------
# prompt behaviour
# ---------------------------------------------------------------------------


def test_cmems_prompt_false_no_credentials_raises(cm_cache, no_credentials, fake_subset, fake_login, fake_prompt):
    with pytest.raises(FileNotFoundError) as excinfo:
        from_source("cmems", DATASET, request=make_source(), prompt=False)

    message = str(excinfo.value)
    assert "Copernicus Marine credentials not found" in message
    assert cm_source.USERNAME_ENV in message
    assert cm_source.PASSWORD_ENV in message
    assert cm_source.DEFAULT_CREDENTIALS_FILENAME in message
    assert "prompt=True" in message
    # the prompt was never used
    assert fake_prompt == []
    assert fake_login.calls == []
    assert fake_subset.calls == []


def test_cmems_prompt_true_asks_once_and_logs_in(
    cm_cache, no_credentials, fake_subset, fake_login, fake_prompt, caplog
):
    caplog.set_level(logging.DEBUG)

    ds = from_source("cmems", DATASET, request=make_source())

    # the user was asked once and the answers were stored with login()
    assert len(fake_prompt) == 1
    assert fake_login.calls == [
        dict(
            username=FAKE_USERNAME,
            password=FAKE_PASSWORD,
            force_overwrite=True,
            check_credentials_valid=False,
        )
    ]

    # the download proceeded
    assert len(fake_subset.calls) == 1
    assert ds.path.endswith(".nc")
    assert os.path.isfile(ds.path)

    no_password_in_logs(caplog)


def test_cmems_prompt_true_asks_once_for_parallel_requests(
    cm_cache_two_threads, no_credentials, fake_subset, fake_login, fake_prompt
):
    ds = from_source(
        "cmems",
        DATASET,
        request=[make_source(), make_source(variables=["so"])],
    )

    # several requests are downloaded in parallel but the user is asked once
    assert len(fake_prompt) == 1
    assert len(fake_login.calls) == 1
    assert len(fake_subset.calls) == 2
    paths = ds.path if isinstance(ds.path, list) else [ds.path]
    assert len(paths) == 2


def test_cmems_prompt_uses_input_and_getpass(cm_cache, no_credentials, fake_login, fake_answers, capsys):
    # exercise the real prompt machinery with patched user input: the
    # username is typed with input(), the password with getpass() (hidden)
    prompt = CMEMSAPIKeyPrompt()
    answers = prompt.ask_user()

    assert answers == dict(username=FAKE_USERNAME, password=FAKE_PASSWORD)
    assert [kind for kind, _ in fake_answers.methods] == ["input", "getpass"]

    # the password never appears in what is printed
    out = capsys.readouterr().out
    assert FAKE_PASSWORD not in out
    for _, message in fake_answers.methods:
        assert FAKE_PASSWORD not in message


def test_cmems_prompt_end_to_end_hidden_password(
    cm_cache, no_credentials, fake_subset, fake_login, fake_answers, capsys, caplog
):
    caplog.set_level(logging.DEBUG)

    ds = from_source("cmems", DATASET, request=make_source())

    assert fake_login.calls[0]["password"] == FAKE_PASSWORD
    assert len(fake_subset.calls) == 1
    assert ds.path.endswith(".nc")

    # the password is not printed and not logged
    out = capsys.readouterr().out
    assert FAKE_PASSWORD not in out
    no_password_in_logs(caplog)


def test_cmems_prompt_not_used_when_env_credentials(cm_cache, credentials_in_env, fake_subset, fake_login, fake_prompt):
    # prompt=True (default) but credentials are in the environment: no question
    ds = from_source("cmems", DATASET, request=make_source())
    assert ds.path.endswith(".nc")
    assert fake_prompt == []
    assert fake_login.calls == []


def test_cmems_prompt_not_used_when_credentials_file_exists(
    cm_cache, no_credentials, fake_subset, fake_login, fake_prompt, monkeypatch, tmp_path
):
    # an existing credentials file is enough: only its existence is checked,
    # never its content
    credentials_dir = tmp_path / "cm-credentials-directory"
    credentials_dir.mkdir()
    write_fake_credentials_file(credentials_dir / cm_source.DEFAULT_CREDENTIALS_FILENAME)
    monkeypatch.setenv(cm_source.CREDENTIALS_DIRECTORY_ENV, str(credentials_dir))

    ds = from_source("cmems", DATASET, request=make_source())
    assert ds.path.endswith(".nc")
    assert fake_prompt == []
    assert fake_login.calls == []


def test_cmems_prompt_login_failure_raises(cm_cache, no_credentials, fake_subset, monkeypatch, fake_prompt):
    failed = FakeLogin(result=False)
    monkeypatch.setattr(copernicusmarine, "login", failed)

    with pytest.raises(RuntimeError) as excinfo:
        from_source("cmems", DATASET, request=make_source())

    assert "login failed" in str(excinfo.value).lower()
    assert FAKE_PASSWORD not in str(excinfo.value)
    assert len(failed.calls) == 1
    assert fake_subset.calls == []
    # nothing was stored in the cache
    assert cm_entries() == []


def test_cmems_prompt_false_does_not_write_anything(no_credentials, tmp_path, monkeypatch):
    # the prompt class must compute the credentials path from the redirected
    # environment only: the real ~/.copernicusmarine is never touched
    monkeypatch.setenv(cm_source.CREDENTIALS_DIRECTORY_ENV, str(tmp_path / "some-dir"))
    prompt = CMEMSAPIKeyPrompt()
    assert prompt.rcfile == str(tmp_path / "some-dir" / cm_source.DEFAULT_CREDENTIALS_FILENAME)
    assert prompt.existing_rcfile_path() is None
    assert not prompt.has_api_config()


# ---------------------------------------------------------------------------
# prompt guard: the library must never be able to ask for credentials
# interactively (it would hang a non interactive session)
# ---------------------------------------------------------------------------


def test_cmems_prompt_guard_patch_and_restore(library_without_env_credentials, fail_on_click_prompt, tmp_path):
    full_file = tmp_path / "cm-credentials-full"
    write_fake_credentials_file(full_file, username="test-user", password="test-pass")

    original = credentials_utils._retrieve_credential_from_prompt
    try:
        with _no_interactive_prompt():
            assert credentials_utils._retrieve_credential_from_prompt is not original

            with pytest.raises(InteractivePromptError, match="asked for the username interactively"):
                credentials_utils._retrieve_credential_from_prompt("username", False)
            with pytest.raises(InteractivePromptError, match="asked for the password interactively"):
                credentials_utils._retrieve_credential_from_prompt("password", hide_input=True)

            # a nested context keeps the guard on until the outermost exits
            with _no_interactive_prompt():
                assert credentials_utils._retrieve_credential_from_prompt is not original
            assert credentials_utils._retrieve_credential_from_prompt is not original

            # complete credentials are resolved normally, without any prompt
            assert credentials_utils.get_username_password(None, None, full_file) == ("test-user", "test-pass")

        assert credentials_utils._retrieve_credential_from_prompt is original

        # sanity check: without the guard the fake prompt fails loudly (no hang)
        with pytest.raises(AssertionError, match="tried to prompt"):
            credentials_utils._retrieve_credential_from_prompt("username", False)
    finally:
        assert credentials_utils._retrieve_credential_from_prompt is original


def test_cmems_default_credentials_file_with_empty_fields(
    cm_cache,
    no_credentials,
    library_without_env_credentials,
    fail_on_click_prompt,
    fake_login,
    monkeypatch,
    tmp_path,
):
    credentials_directory = tmp_path / "cm-credentials-directory"
    credentials_directory.mkdir()
    write_fake_credentials_file(credentials_directory / cm_source.DEFAULT_CREDENTIALS_FILENAME)

    # redirect both the source and the library to the fake credentials file
    monkeypatch.setenv(cm_source.CREDENTIALS_DIRECTORY_ENV, str(credentials_directory))
    monkeypatch.setattr(credentials_utils, "DEFAULT_CLIENT_BASE_DIRECTORY", credentials_directory)

    fake = SubsetResolvingCredentials()
    monkeypatch.setattr(copernicusmarine, "subset", fake)

    original = credentials_utils._retrieve_credential_from_prompt
    # the credentials file exists so earthkit does not prompt, but its fields
    # are empty: the library would prompt, the guard must raise instead of
    # hanging
    with pytest.raises(InteractivePromptError, match="asked for the username interactively"):
        from_source("cmems", DATASET, request=make_source())

    assert len(fake.calls) == 1
    assert fake_login.calls == []
    assert credentials_utils._retrieve_credential_from_prompt is original


def test_cmems_prompt_guard_survives_concurrent_failure(
    cm_cache_two_threads,
    credentials_in_env,
    library_without_env_credentials,
    fail_on_click_prompt,
    monkeypatch,
    tmp_path,
):
    # Regression test: when one parallel request fails, FileRequestRetriever
    # abandons the retrieval without joining the remaining download threads.
    # The prompt guard must stay installed while a worker is still inside
    # subset() and the original prompt function must be restored only when
    # the last in-flight call has returned.
    credentials_file = tmp_path / "cm-credentials-empty-parallel"
    write_fake_credentials_file(credentials_file)

    original = credentials_utils._retrieve_credential_from_prompt

    started_b = threading.Event()
    release_b = threading.Event()
    b_finished = threading.Event()
    outcomes = {}

    class ConcurrentSubset:
        def __call__(self, **kwargs):
            if kwargs.get("variables") == ["thetao"]:
                # worker A: fails fast while worker B is still inside subset()
                raise RuntimeError("worker A failed")

            # worker B: stays inside subset() until the retrieval has been
            # abandoned and only then resolves the credentials
            started_b.set()
            released = release_b.wait(timeout=30)
            try:
                assert released, "worker B was not released in time"
                # the retrieval has already failed in the main thread: the
                # guard must still be installed, B is inside subset()
                assert credentials_utils._retrieve_credential_from_prompt is not original
                credentials_utils.get_username_password(None, None, credentials_file)
            except BaseException as exc:
                outcomes["b_prompt"] = exc
            finally:
                b_finished.set()
            raise RuntimeError("worker B finished")

    monkeypatch.setattr(copernicusmarine, "subset", ConcurrentSubset())

    with pytest.raises(RuntimeError, match="worker A failed"):
        from_source(
            "cmems",
            DATASET,
            request=[make_source(), make_source(variables=["so"])],
        )

    # A has failed and retrieve() has returned, B is still inside subset()
    assert started_b.wait(timeout=30), "worker B never entered subset()"
    assert credentials_utils._retrieve_credential_from_prompt is not original, (
        "the prompt guard was restored while a download thread was still in flight"
    )

    release_b.set()
    assert b_finished.wait(timeout=30), "worker B did not finish in time"

    # B reached the library prompt path while guarded
    b_prompt = outcomes.get("b_prompt")
    assert isinstance(b_prompt, InteractivePromptError), b_prompt

    # the last in-flight subset() call has returned: the original is restored
    deadline = time.time() + 30
    while time.time() < deadline and credentials_utils._retrieve_credential_from_prompt is not original:
        time.sleep(0.01)
    assert credentials_utils._retrieve_credential_from_prompt is original


def test_cmems_prompt_guard_missing_module(cm_cache, credentials_in_env, no_subset, monkeypatch):
    # the guard must fail closed: without it the library could hang the
    # download on an interactive prompt, so nothing may be attempted
    monkeypatch.setattr(cm_source, "PROMPT_MODULE", "copernicusmarine.core_functions.does_not_exist")

    with pytest.raises(LibraryCompatibilityError) as excinfo:
        from_source("cmems", DATASET, request=make_source())

    assert copernicusmarine.__version__ in str(excinfo.value)
    assert "does_not_exist" in str(excinfo.value)
    assert cm_source._prompt_count == 0
    assert cm_source._prompt_original is None


def test_cmems_prompt_guard_missing_function(cm_cache, credentials_in_env, no_subset, monkeypatch):
    # same for an installed library which lacks the internal prompt function
    monkeypatch.setattr(cm_source, "PROMPT_FUNCTION", "_no_such_prompt_function")

    original = credentials_utils._retrieve_credential_from_prompt
    with pytest.raises(LibraryCompatibilityError) as excinfo:
        from_source("cmems", DATASET, request=make_source())

    assert copernicusmarine.__version__ in str(excinfo.value)
    assert "_no_such_prompt_function" in str(excinfo.value)
    # the library was left untouched and no download was attempted
    assert credentials_utils._retrieve_credential_from_prompt is original
    assert cm_source._prompt_count == 0
    assert cm_source._prompt_original is None


# ---------------------------------------------------------------------------
# formats and request validation
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("file_format", ["csv", "CSV"])
def test_cmems_csv(fake_subset, cm_cache, credentials_in_env, file_format):
    ds = from_source("cmems", DATASET, request=make_source(file_format=file_format))

    # the cache extension follows the format
    assert ds.path.endswith(".csv")
    assert os.path.isfile(ds.path)

    df = ds.to_pandas()
    assert "thetao" in df.columns
    assert len(df) == 4

    assert len(fake_subset.calls) == 1
    call = fake_subset.calls[0]
    assert call["file_format"] == "csv"
    assert call["output_filename"] == "cmems-subset.csv"

    # the format is part of the cache arguments
    assert one_cm_entry()["args"]["file_format"] == "csv"


def test_cmems_netcdf_and_csv_are_different_cache_entries(fake_subset, cm_cache, credentials_in_env):
    ds_nc = from_source("cmems", DATASET, request=make_source())
    ds_csv = from_source("cmems", DATASET, request=make_source(file_format="csv"))

    assert ds_nc.path.endswith(".nc")
    assert ds_csv.path.endswith(".csv")
    assert ds_nc.path != ds_csv.path
    assert len(fake_subset.calls) == 2


@pytest.mark.parametrize("file_format", ["zarr", "parquet", "grib"])
def test_cmems_unsupported_format(cm_cache, credentials_in_env, no_subset, file_format):
    with pytest.raises(ValueError, match="unsupported file format"):
        from_source("cmems", DATASET, request=make_source(file_format=file_format))


@pytest.mark.parametrize("key", ["output_directory", "output_filename", "overwrite", "dry_run"])
def test_cmems_forbidden_keys(cm_cache, credentials_in_env, no_subset, key):
    with pytest.raises(ValueError, match="controlled by the source"):
        from_source("cmems", DATASET, request=make_source(**{key: "value"}))


def test_cmems_temp_dir_cleanup_success(fake_subset, cm_cache, credentials_in_env):
    ds = from_source("cmems", DATASET, request=make_source())

    assert len(fake_subset.output_directories) == 1
    temp_dir = fake_subset.output_directories[0]
    assert os.path.isfile(ds.path)
    # the temporary download directory is removed after a successful retrieval
    assert not os.path.exists(temp_dir)


def test_cmems_temp_dir_cleanup_failure(cm_cache, credentials_in_env, monkeypatch):
    # the fake subset records the temporary directory and then fails
    fake = FakeSubset(error=RuntimeError("subset failed"))
    monkeypatch.setattr(copernicusmarine, "subset", fake)

    with pytest.raises(RuntimeError, match="subset failed"):
        from_source("cmems", DATASET, request=make_source())

    assert len(fake.output_directories) == 1
    temp_dir = fake.output_directories[0]
    # the temporary download directory is removed even when the download fails
    assert not os.path.exists(temp_dir)


# ---------------------------------------------------------------------------
# live tests: need network access and Copernicus Marine credentials
# (run with: pytest -E long tests/sources/test_cmems.py)
# prompt=False so that a live run never waits for interactive input: it is
# skipped entirely when no credentials can be found.
# ---------------------------------------------------------------------------


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CMEMS, reason="No access to Copernicus Marine")
@pytest.mark.timeout(CM_TIMEOUT)
def test_cmems_netcdf_live():
    # a 1 degree box off the northwest coast of Portugal, a single time step
    # and the first depth level
    ds = from_source(
        "cmems",
        DATASET,
        request=dict(
            variables=["thetao"],
            minimum_longitude=-10,
            maximum_longitude=-9,
            minimum_latitude=40,
            maximum_latitude=41,
            start_datetime="2020-01-01",
            end_datetime="2020-01-01T23:59:59",
            minimum_depth=0,
            maximum_depth=1,
        ),
        prompt=False,
    ).to_xarray()
    assert "thetao" in ds.data_vars
    assert ds["thetao"].size > 0


@pytest.mark.long_test
@pytest.mark.download
@pytest.mark.skipif(NO_CMEMS, reason="No access to Copernicus Marine")
@pytest.mark.timeout(CM_TIMEOUT)
def test_cmems_csv_live():
    ds = from_source(
        "cmems",
        DATASET,
        request=dict(
            file_format="csv",
            variables=["thetao"],
            minimum_longitude=-10,
            maximum_longitude=-9,
            minimum_latitude=40,
            maximum_latitude=41,
            start_datetime="2020-01-01",
            end_datetime="2020-01-01T23:59:59",
            minimum_depth=0,
            maximum_depth=1,
        ),
        prompt=False,
    )
    df = ds.to_pandas()
    assert len(df) > 0
    assert "thetao" in df.columns


if __name__ == "__main__":
    from earthkit.data.utils.testing import main

    main(__file__)
