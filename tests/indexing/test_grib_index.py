#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Tests of the public API ``to_fieldlist(index=..., index_extra_keys=...)``."""

import os
import pathlib

import numpy as np
import pytest
from indexing_fixtures import get_tmp_fixture, install_handle_counter, install_scan_counter  # noqa: E402

from earthkit.data import config, from_source
from earthkit.data.readers.grib.file import GribFieldListInFile, IndexedGribFieldListInFile
from earthkit.data.readers.grib.index import GribIndex

VARIABLES = {
    "file": ["t", "u", "v"] * 6,
    "multi": ["t"] * 6 + ["u"] * 6 + ["v"] * 6,
    "directory": ["t"] * 6 + ["u"] * 6 + ["v"] * 6,
}
COUNTS = {
    "file": [18],
    "multi": [6, 6, 6],
    "directory": [6, 6, 6],
}
MODES = list(VARIABLES)


@pytest.fixture
def cache_dir(tmp_path):
    """Use a temporary earthkit-data user cache so that the real one is not touched."""
    path = tmp_path / "cache"
    path.mkdir()
    with config.temporary({"cache-policy": "user", "user-cache-directory": str(path)}):
        yield path


@pytest.fixture
def handle_counter(monkeypatch):
    return install_handle_counter(monkeypatch)


@pytest.fixture
def make_source():
    """Create the temporary GRIB files of a fixture mode.

    Returns a function ``make(mode)`` giving ``(source path(s), list of the GRIB files in the order
    of the fieldlist)``. The files are removed at the end of the test.
    """
    created = []

    def _make(mode):
        tmp, path = get_tmp_fixture(mode)
        created.append(tmp)
        if mode == "file":
            files = [path]
        elif mode == "multi":
            files = list(path)
        else:
            files = [os.path.join(path, x) for x in sorted(os.listdir(path))]
        return path, files

    yield _make

    for tmp in created:
        for t in tmp if isinstance(tmp, list) else [tmp]:
            t.cleanup()


def _db_state(path):
    st = os.stat(path)
    return st.st_size, st.st_mtime_ns


def _plain(path):
    return from_source("file", path).to_fieldlist()


def _check_same_as_plain(fl, plain, variables):
    assert len(fl) == len(plain) == len(variables)
    assert fl.get("parameter.variable") == variables
    assert fl.get("parameter.variable") == plain.get("parameter.variable")
    assert fl.get("vertical.level") == plain.get("vertical.level")
    np.testing.assert_array_equal(fl.to_numpy(), plain.to_numpy())


def _cache_dbs(files):
    """Return the cache dbs of the files as ``{path: (db_path, count)}``."""
    r = {}
    for p in files:
        db = GribIndex.find_in_cache(p)
        assert db is not None, f"no cache db found for {p}"
        with db:
            r[p] = (db.path, db.count(p))
    return r


# ----------------------------------------------------------------- index=True


@pytest.mark.parametrize("mode", MODES)
def test_indexing_db_cache(mode, cache_dir, handle_counter, make_source):
    path, files = make_source(mode)
    plain = _plain(path)
    variables = VARIABLES[mode]

    d = from_source("file", path)
    fl = d.to_fieldlist(index=True)
    _check_same_as_plain(fl, plain, variables)

    # one db per file
    dbs = _cache_dbs(files)
    assert [dbs[p][1] for p in files] == COUNTS[mode]
    assert len({v[0] for v in dbs.values()}) == len(files)
    state = {p: _db_state(v[0]) for p, v in dbs.items()}

    # repeated use: the dbs are reused and no GRIB handle is needed
    d = from_source("file", path)
    handle_counter["n"] = 0
    fl = d.to_fieldlist(index=True)
    assert fl.get("parameter.variable") == variables
    assert handle_counter["n"] == 0

    assert _cache_dbs(files) == dbs
    assert {p: _db_state(v[0]) for p, v in dbs.items()} == state
    _check_same_as_plain(fl, plain, variables)


def test_indexing_db_cache_single_type(cache_dir):
    _, path = get_tmp_fixture("file")
    fl = from_source("file", path).to_fieldlist(index=True)
    assert isinstance(fl, IndexedGribFieldListInFile)

    for index in [None, False]:
        fl = from_source("file", path).to_fieldlist(index=index)
        assert isinstance(fl, GribFieldListInFile)
        assert len(fl) == 18


def test_indexing_no_index_no_db(cache_dir):
    _, path = get_tmp_fixture("file")
    for index in [None, False]:
        from_source("file", path).to_fieldlist(index=index)
    assert GribIndex.find_in_cache(path) is None


def test_indexing_db_cache_changed_file(cache_dir, make_source):
    path, files = make_source("multi")
    d = from_source("file", path)
    fl = d.to_fieldlist(index=True)
    assert len(fl) == 18
    dbs = _cache_dbs(files)

    # keep only 2 messages in the second file
    messages = [f.message() for f in from_source("file", files[1]).to_fieldlist()][:2]
    with open(files[1], "wb") as f:
        for m in messages:
            f.write(m)

    # the db of the changed file is not up to date, the others are
    assert GribIndex.find_in_cache(files[1]) is None
    with GribIndex.find_in_cache(files[0]):
        pass

    fl = from_source("file", path).to_fieldlist(index=True)
    assert len(fl) == 14
    assert fl.get("parameter.variable") == ["t"] * 6 + ["u"] * 2 + ["v"] * 6
    np.testing.assert_array_equal(fl.to_numpy(), _plain(path).to_numpy())

    new_dbs = _cache_dbs(files)
    assert new_dbs[files[0]] == dbs[files[0]]
    assert new_dbs[files[2]] == dbs[files[2]]
    assert new_dbs[files[1]][1] == 2


# ----------------------------------------------------------------- index=<path>


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("kind", [str, pathlib.Path])
def test_indexing_db_custom_path(mode, kind, tmp_path, handle_counter, make_source):
    path, files = make_source(mode)
    plain = _plain(path)
    variables = VARIABLES[mode]
    db_path = tmp_path / "sub" / "idx.sqlite"
    db_path.parent.mkdir()

    fl = from_source("file", path).to_fieldlist(index=kind(db_path))
    _check_same_as_plain(fl, plain, variables)

    # a single db with all the files
    assert db_path.is_file()
    with GribIndex(db_path) as db:
        assert db.paths() == [os.path.abspath(p) for p in files]
        assert db.count() == len(variables)
        assert [db.count(p) for p in files] == COUNTS[mode]
    state = _db_state(db_path)

    # repeated use: the db is reused and no GRIB handle is needed
    d = from_source("file", path)
    handle_counter["n"] = 0
    fl = d.to_fieldlist(index=kind(db_path))
    assert fl.get("parameter.variable") == variables
    assert handle_counter["n"] == 0
    assert _db_state(db_path) == state
    _check_same_as_plain(fl, plain, variables)


def test_indexing_db_custom_path_no_cache_needed(tmp_path):
    # an explicit db path works with the default cache-policy ("off")
    assert config.get("cache-policy") == "off"
    _, path = get_tmp_fixture("multi")
    fl = from_source("file", path).to_fieldlist(index=str(tmp_path / "idx.sqlite"))
    assert fl.get("parameter.variable") == VARIABLES["multi"]


def test_indexing_db_custom_path_changed_file(tmp_path, monkeypatch, make_source):
    path, files = make_source("multi")
    db_path = str(tmp_path / "idx.sqlite")
    scanned = install_scan_counter(monkeypatch)

    fl = from_source("file", path).to_fieldlist(index=db_path)
    assert len(fl) == 18
    assert sorted(scanned) == sorted(os.path.basename(p) for p in files)

    # nothing is scanned when nothing has changed
    scanned.clear()
    from_source("file", path).to_fieldlist(index=db_path)
    assert scanned == []

    # keep only 3 messages in the first file
    messages = [f.message() for f in from_source("file", files[0]).to_fieldlist()][:3]
    with open(files[0], "wb") as f:
        for m in messages:
            f.write(m)

    # only the changed file is scanned again
    fl = from_source("file", path).to_fieldlist(index=db_path)
    assert scanned == [os.path.basename(files[0])]
    assert len(fl) == 15
    assert fl.get("parameter.variable") == ["t"] * 3 + ["u"] * 6 + ["v"] * 6
    np.testing.assert_array_equal(fl.to_numpy(), _plain(path).to_numpy())

    with GribIndex(db_path) as db:
        assert [db.count(p) for p in files] == [3, 6, 6]


def test_indexing_db_custom_path_new_file_added(tmp_path, monkeypatch):
    # files can be added to an existing db by indexing a larger source
    _, files = get_tmp_fixture("multi")
    db_path = str(tmp_path / "idx.sqlite")
    scanned = install_scan_counter(monkeypatch)

    fl = from_source("file", files[:2]).to_fieldlist(index=db_path)
    assert len(fl) == 12
    scanned.clear()

    fl = from_source("file", files).to_fieldlist(index=db_path)
    assert len(fl) == 18
    assert scanned == [os.path.basename(files[2])]
    with GribIndex(db_path) as db:
        assert db.paths() == [os.path.abspath(p) for p in files]


# ----------------------------------------------------------------- errors


@pytest.mark.parametrize("mode", MODES)
def test_indexing_cache_policy_off(mode, tmp_path, make_source):
    path, _ = make_source(mode)
    with config.temporary("cache-policy", "off"):
        d = from_source("file", path)
        with pytest.raises(ValueError, match="cache-policy") as e:
            d.to_fieldlist(index=True)
        assert "'user'" in str(e.value) and "'temporary'" in str(e.value)

        # no index and an explicit db are fine
        assert len(d.to_fieldlist()) == len(VARIABLES[mode])
        assert len(d.to_fieldlist(index=str(tmp_path / "idx.sqlite"))) == len(VARIABLES[mode])


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("index", [1, 0, 2.5, ["idx.sqlite"], {"a": 1}, b"idx.sqlite", object()])
def test_indexing_invalid_index_type(mode, index, cache_dir, make_source):
    path, files = make_source(mode)
    d = from_source("file", path)
    with pytest.raises(TypeError, match="index"):
        d.to_fieldlist(index=index)

    # nothing was created
    assert all(GribIndex.find_in_cache(p) is None for p in files)


def test_indexing_grib_index_keyword_removed(cache_dir):
    _, path = get_tmp_fixture("file")
    with pytest.raises(TypeError):
        from_source("file", path).to_fieldlist(grib_index=True)

    _, path = get_tmp_fixture("multi")
    with pytest.raises(TypeError):
        from_source("file", path).to_fieldlist(grib_index=True)


# ----------------------------------------------------------------- index_extra_keys


@pytest.mark.parametrize("mode", MODES)
@pytest.mark.parametrize("kind", ["cache", "path"])
def test_indexing_extra_keys(mode, kind, cache_dir, tmp_path, handle_counter, make_source):
    path, files = make_source(mode)
    plain = _plain(path)
    expected = plain.get("metadata.bitsPerValue")
    assert len(expected) == len(VARIABLES[mode])

    index = True if kind == "cache" else str(tmp_path / "idx.sqlite")
    fl = from_source("file", path).to_fieldlist(index=index, index_extra_keys=["bitsPerValue"])

    # stored as metadata.bitsPerValue
    if kind == "path":
        with GribIndex(index) as db:
            assert all(db.extra_keys(p) == ["bitsPerValue"] for p in files)
            assert "metadata.bitsPerValue" in db._dynamic_columns()
    else:
        for p in files:
            with GribIndex.find_in_cache(p, extra_keys=["bitsPerValue"]) as db:
                assert db.extra_keys(p) == ["bitsPerValue"]
                assert "metadata.bitsPerValue" in db._dynamic_columns()

    # and served without a handle
    handle_counter["n"] = 0
    assert fl.get("metadata.bitsPerValue") == expected
    assert fl[0].get("metadata.bitsPerValue") == expected[0]
    assert handle_counter["n"] == 0


def test_indexing_extra_keys_added_later(tmp_path, monkeypatch, handle_counter):
    _, path = get_tmp_fixture("file")
    db_path = str(tmp_path / "idx.sqlite")
    scanned = install_scan_counter(monkeypatch)

    from_source("file", path).to_fieldlist(index=db_path)
    assert len(scanned) == 1

    # a key that is not stored needs the GRIB file
    fl = from_source("file", path).to_fieldlist(index=db_path)
    handle_counter["n"] = 0
    values = fl.get("metadata.bitsPerValue")
    assert handle_counter["n"] > 0

    # requesting the key re-scans the file
    fl = from_source("file", path).to_fieldlist(index=db_path, index_extra_keys=["bitsPerValue"])
    assert len(scanned) == 2
    handle_counter["n"] = 0
    assert fl.get("metadata.bitsPerValue") == values
    assert handle_counter["n"] == 0

    # already stored: no new scan
    from_source("file", path).to_fieldlist(index=db_path, index_extra_keys=["bitsPerValue"])
    assert len(scanned) == 2
