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
import os
import shutil
import sqlite3

import pytest
from indexing_fixtures import get_tmp_fixture  # noqa: E402

from earthkit.data import config, from_source
from earthkit.data.readers.grib.index import DEFAULT_RAW_KEYS, GribIndex
from earthkit.data.utils.testing import earthkit_examples_file

COMPONENT_KEYS = ["parameter.variable", "vertical.level", "ensemble.member", "time.step"]
EXTRA_KEY = "latitudeOfFirstGridPointInDegrees"


def _same(a, b):
    """Equal values of the same type, also inside containers."""
    assert type(a) is type(b), (a, b)
    if isinstance(a, (list, tuple)):
        assert len(a) == len(b)
        for x, y in zip(a, b):
            _same(x, y)
    elif isinstance(a, dict):
        assert a.keys() == b.keys()
        for k in a:
            _same(a[k], b[k])
    else:
        assert a == b


def _scan_counter(monkeypatch):
    """Count the scanned files."""
    scanned = []
    orig = GribIndex._scan

    def _scan(self, path, extra_keys):
        scanned.append(os.path.basename(path))
        return orig(self, path, extra_keys)

    monkeypatch.setattr(GribIndex, "_scan", _scan)
    return scanned


def _db_state(path):
    st = os.stat(path)
    return st.st_size, st.st_mtime_ns


def _dump(db, path):
    return list(db.rows(path))


def test_grib_index_db_schema(tmp_path):
    _, path = get_tmp_fixture("file")
    db_path = str(tmp_path / "idx.sqlite")

    with GribIndex.open(path, db_path) as db:
        assert db.path == db_path
        tables = {r[0] for r in db.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        assert {"meta", "paths", "grib_index"} <= tables
        assert "column_types" not in tables

        assert db.conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()[0] == "2"

        cols = [r[1] for r in db.conn.execute("PRAGMA table_info(paths)")]
        assert cols == ["id", "path", "size", "mtime", "extra_keys"]

        cols = [r[1] for r in db.conn.execute("PRAGMA table_info(grib_index)")]
        assert cols[:4] == ["_id", "_path_id", "_offset", "_length"]
        assert "parameter.variable" in cols
        for k in DEFAULT_RAW_KEYS:
            assert "metadata." + k in cols

        size, mtime, extra = db.conn.execute("SELECT size, mtime, extra_keys FROM paths").fetchone()
        st = os.stat(path)
        assert (size, mtime, extra) == (st.st_size, st.st_mtime_ns, "[]")

        idx = db.conn.execute("PRAGMA index_list(grib_index)").fetchall()
        assert any(i[1] == "idx_grib_index_path_offset" and i[2] == 1 for i in idx)


def test_grib_index_db_incompatible_schema(tmp_path):
    db_path = str(tmp_path / "old.sqlite")
    conn = sqlite3.connect(db_path)
    conn.execute("CREATE TABLE paths (id INTEGER PRIMARY KEY, path TEXT not null)")
    conn.commit()
    conn.close()

    with pytest.raises(ValueError, match="schema version"):
        GribIndex(db_path)


def test_grib_index_db_typed_roundtrip(tmp_path, monkeypatch):
    values = {
        "t.none": None,
        "t.int": 42,
        "t.negint": -7,
        "t.bigint": 2**70,
        "t.float": 1.5,
        "t.nan": float("nan"),
        "t.str": "abc",
        "t.bool_true": True,
        "t.bool_false": False,
        "t.datetime": datetime.datetime(2018, 8, 1, 12, 30, 15, 123456),
        "t.datetime_tz": datetime.datetime(2018, 8, 1, 12, 0, tzinfo=datetime.timezone.utc),
        "t.date": datetime.date(2018, 8, 1),
        "t.timedelta": datetime.timedelta(days=1, hours=6, microseconds=7),
        "t.timedelta_neg": datetime.timedelta(seconds=-90),
        "t.list": [1, 2.5, "a", None, [3, 4], True],
        "t.tuple": (1, 2),
        "t.dict": {"a": [1, 2], "b": {"c": None, "d": "x"}, "e": 1.5},
        "t.empty_list": [],
        "t.bytes": b"ab\x00cd",
        "metadata.str_number": "007",
    }
    # None as a value is not the same as an absent key
    row2 = dict(values)
    row1 = {k: v for k, v in values.items() if k not in ("t.int", "t.str", "t.none")}
    # a column holds values of different kinds (and a missing key)
    row3 = {
        "t.int": "now a str",
        "t.str": 3,
        "t.float": [1.5],
        "t.list": True,
        "t.tuple": None,
        "t.dict": datetime.date(2020, 1, 2),
        "t.bool_true": 1.25,
        "t.datetime": {"a": 1},
    }
    expected_rows = [row1, row2, row3]

    monkeypatch.setattr(
        GribIndex,
        "_scan",
        lambda self, path, extra_keys: iter([(0, 10, row1), (10, 10, row2), (20, 10, row3)]),
    )

    def _check(rows):
        assert [r["_offset"] for r in rows] == [0, 10, 20]
        assert [r["_length"] for r in rows] == [10, 10, 10]
        for r, expected in zip(rows, expected_rows):
            assert {k for k in r if not k.startswith("_")} == set(expected)
            for k, v in expected.items():
                if isinstance(v, float) and v != v:
                    assert isinstance(r[k], float) and r[k] != r[k]
                else:
                    _same(r[k], v)

    _, path = get_tmp_fixture("file")
    with GribIndex.open(path, str(tmp_path / "idx.sqlite")) as db:
        rows = _dump(db, path)
        _check(rows)

        # absent keys are not in the row, None as a value is
        assert "t.none" not in rows[0]
        assert "t.none" in rows[1] and rows[1]["t.none"] is None
        assert "t.int" not in rows[0]
        assert "t.none" not in rows[2]
        assert "t.tuple" in rows[2] and rows[2]["t.tuple"] is None

        # native values keep their sqlite type, the others are tagged blobs; absent is NULL
        types = db.conn.execute(
            'SELECT typeof("t.int"), typeof("t.float"), typeof("t.str"), typeof("t.bool_true"), '
            'typeof("t.none"), typeof("t.nan") FROM grib_index ORDER BY _offset'
        ).fetchall()
        assert types[0] == ("null", "real", "null", "blob", "null", "blob")
        assert types[1] == ("integer", "real", "text", "blob", "blob", "blob")

    # reading again from a new connection gives the same
    with GribIndex(str(tmp_path / "idx.sqlite")) as db:
        _check(_dump(db, path))


def test_grib_index_db_tuv_pl_values(tmp_path):
    path = earthkit_examples_file("tuv_pl.grib")
    plain = from_source("file", path).to_fieldlist()

    with GribIndex.open(path, str(tmp_path / "idx.sqlite")) as db:
        assert db.count() == 18
        assert db.count(path) == 18
        assert db.paths() == [os.path.abspath(path)]
        rows = _dump(db, path)

    assert len(rows) == 18
    # ordered by offset
    offsets = [r["_offset"] for r in rows]
    assert offsets == sorted(offsets)
    assert offsets[0] == 0

    for key in ["metadata.shortName", "metadata.level", "metadata.param", "metadata.paramId", "metadata.date"]:
        expected = plain.get(key)
        assert len(expected) == 18
        got = [r[key] for r in rows]
        for g, e in zip(got, expected):
            _same(g, e)

    # native types
    assert all(isinstance(r["metadata.level"], int) for r in rows)
    assert all(isinstance(r["metadata.shortName"], str) for r in rows)

    for key in COMPONENT_KEYS:
        expected = plain.get(key)
        assert len(expected) == 18
        got = [r[key] for r in rows]
        for g, e in zip(got, expected):
            _same(g, e)

    # offset/length
    for r, f in zip(rows, plain):
        h = f._get_grib().handle
        assert r["_offset"] == int(h.get("offset"))
        assert r["_length"] == int(h.get("totalLength"))


def test_grib_index_db_missing_keys_are_null(tmp_path):
    _, path = get_tmp_fixture("file")
    with GribIndex.open(path, str(tmp_path / "idx.sqlite"), extra_keys=["thisKeyDoesNotExist"]) as db:
        # nothing is stored for a key that no message has, so there is not even a column
        assert "metadata.thisKeyDoesNotExist" not in db._dynamic_columns()
        assert db.extra_keys(path) == ["thisKeyDoesNotExist"]
        for r in db.rows(path):
            assert "metadata.thisKeyDoesNotExist" not in r


def test_grib_index_db_reuse(tmp_path, monkeypatch):
    _, path = get_tmp_fixture("file")
    db_path = str(tmp_path / "idx.sqlite")

    scanned = _scan_counter(monkeypatch)

    with GribIndex.open(path, db_path) as db:
        assert db.count() == 18
        first = _dump(db, path)
    assert len(scanned) == 1
    state = _db_state(db_path)

    with GribIndex.open(path, db_path) as db:
        assert db.count() == 18
        assert _dump(db, path) == first

    assert len(scanned) == 1
    assert _db_state(db_path) == state

    # path given as list or pathlib gives the same
    import pathlib

    with GribIndex.open([pathlib.Path(path)], db_path) as db:
        assert db.count() == 18
    assert len(scanned) == 1
    assert _db_state(db_path) == state


def test_grib_index_db_rescan_when_file_changes(tmp_path, monkeypatch):
    src = earthkit_examples_file("tuv_pl.grib")
    path = str(tmp_path / "data.grib")
    shutil.copy(src, path)
    db_path = str(tmp_path / "idx.sqlite")

    with GribIndex.open(path, db_path) as db:
        rows = _dump(db, path)
        assert len(rows) == 18

    scanned = _scan_counter(monkeypatch)

    # 1. the size changes: keep only the first 12 messages
    cut = rows[12]["_offset"]
    with open(path, "rb") as f:
        data = f.read(cut)
    with open(path, "wb") as f:
        f.write(data)

    with GribIndex.open(path, db_path) as db:
        assert db.count() == 12
        assert db.count(path) == 12
        assert [r["_offset"] for r in db.rows(path)] == [r["_offset"] for r in rows[:12]]
        assert db.paths() == [path]
        size, mtime = db.conn.execute("SELECT size, mtime FROM paths").fetchone()
        assert (size, mtime) == (os.stat(path).st_size, os.stat(path).st_mtime_ns)
    assert scanned == ["data.grib"]

    # unchanged: reused
    with GribIndex.open(path, db_path) as db:
        assert db.count() == 12
    assert scanned == ["data.grib"]

    # 2. only the mtime changes
    st = os.stat(path)
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))
    with GribIndex.open(path, db_path) as db:
        assert db.count() == 12
    assert scanned == ["data.grib", "data.grib"]

    # 3. the content is back to the full file
    shutil.copy(src, path)
    with GribIndex.open(path, db_path) as db:
        assert db.count() == 18
        assert _dump(db, path) == rows
    assert len(scanned) == 3


def test_grib_index_db_multi_files_in_one_db(tmp_path, monkeypatch):
    _, paths = get_tmp_fixture("multi")
    db_path = str(tmp_path / "idx.sqlite")
    scanned = _scan_counter(monkeypatch)

    with GribIndex.open(paths, db_path) as db:
        assert db.paths() == paths
        assert db.count() == 18
        for p in paths:
            assert db.count(p) == 6
        for p, v in zip(paths, "tuv"):
            rows = _dump(db, p)
            assert [r["parameter.variable"] for r in rows] == [v] * 6
            assert [r["metadata.shortName"] for r in rows] == [v] * 6
        assert db.count("/not/in/db.grib") == 0
        assert not db.has_path("/not/in/db.grib")
        with pytest.raises(ValueError, match="does not exist"):
            list(db.rows("/not/in/db.grib"))
    assert len(scanned) == 3
    state = _db_state(db_path)

    # reuse
    with GribIndex.open(paths, db_path) as db:
        assert db.count() == 18
    assert len(scanned) == 3
    assert _db_state(db_path) == state

    # a subset does not remove the others; a new file is added
    with GribIndex.open(paths[1:2], db_path) as db:
        assert db.paths() == paths
        assert db.count() == 18
    assert len(scanned) == 3

    _, other = get_tmp_fixture("file")
    with GribIndex.open(other, db_path) as db:
        assert db.paths() == [*paths, other]
        assert db.count() == 36
    assert len(scanned) == 4


def test_grib_index_db_per_file_extra_keys(tmp_path, monkeypatch):
    _, paths = get_tmp_fixture("multi")
    a, b = paths[0], paths[1]
    db_path = str(tmp_path / "idx.sqlite")
    scanned = _scan_counter(monkeypatch)

    with GribIndex.open(a, db_path) as db:
        assert db.conn.execute("SELECT extra_keys FROM paths WHERE path=?", (a,)).fetchone()[0] == "[]"
        assert "metadata." + EXTRA_KEY not in [r[1] for r in db.conn.execute("PRAGMA table_info(grib_index)")]
    assert scanned == [os.path.basename(a)]

    with GribIndex.open(b, db_path, extra_keys=EXTRA_KEY) as db:
        extra = dict(db.conn.execute("SELECT path, extra_keys FROM paths"))
        assert extra == {a: "[]", b: f'["{EXTRA_KEY}"]'}
        key = "metadata." + EXTRA_KEY
        # the column exists but there is no value for a
        assert all(key not in r for r in db.rows(a))
        assert all(isinstance(r[key], float) for r in db.rows(b))
    assert scanned == [os.path.basename(a), os.path.basename(b)]

    # a is scanned again to get the key, b is reused
    with GribIndex.open([a, b], db_path, extra_keys=[EXTRA_KEY]) as db:
        extra = dict(db.conn.execute("SELECT path, extra_keys FROM paths"))
        assert extra == {a: f'["{EXTRA_KEY}"]', b: f'["{EXTRA_KEY}"]'}
        plain = from_source("file", a).to_fieldlist()
        got = [r[key] for r in db.rows(a)]
        assert got == plain.get(key)
        assert all(isinstance(x, float) for x in got)
        assert db.count() == 12
        assert db.count(a) == 6
    assert scanned == [os.path.basename(a), os.path.basename(b), os.path.basename(a)]

    # requesting fewer keys reuses the files
    with GribIndex.open([a, b], db_path) as db:
        assert db.count() == 12
    assert len(scanned) == 3


def test_grib_index_db_failure_leaves_no_partial_file(tmp_path, monkeypatch):
    _, paths = get_tmp_fixture("multi")
    a, b = paths[0], paths[1]
    db_path = str(tmp_path / "idx.sqlite")

    with GribIndex.open(a, db_path) as db:
        assert db.count() == 6
        rows_a = _dump(db, a)

    calls = []
    orig = GribIndex._raw_keys

    def _failing(handle, extra_keys):
        calls.append(1)
        if len(calls) == 3:
            raise RuntimeError("scan failure")
        return orig(handle, extra_keys)

    monkeypatch.setattr(GribIndex, "_raw_keys", staticmethod(_failing))

    # new file: nothing of it is stored
    with pytest.raises(RuntimeError, match="scan failure"):
        GribIndex.open(b, db_path)
    assert len(calls) == 3

    with GribIndex(db_path) as db:
        assert db.paths() == [a]
        assert db.count() == 6
        assert db.count(b) == 0
        assert not db.has_path(b)
        assert _dump(db, a) == rows_a

    # file to be scanned again (an extra key is requested): the old rows are kept
    calls.clear()
    with pytest.raises(RuntimeError, match="scan failure"):
        GribIndex.open(a, db_path, extra_keys=EXTRA_KEY)

    with GribIndex(db_path) as db:
        assert db.count(a) == 6
        assert _dump(db, a) == rows_a
        assert db.conn.execute("SELECT extra_keys FROM paths").fetchone()[0] == "[]"
        assert "metadata." + EXTRA_KEY not in [r[1] for r in db.conn.execute("PRAGMA table_info(grib_index)")]

    # after the failure the db is usable
    monkeypatch.setattr(GribIndex, "_raw_keys", staticmethod(orig))
    with GribIndex.open([a, b], db_path) as db:
        assert db.count() == 12


def test_grib_index_db_close_and_context_manager(tmp_path):
    _, path = get_tmp_fixture("file")
    db_path = str(tmp_path / "idx.sqlite")

    db = GribIndex.open(path, db_path)
    assert db.count() == 18
    db.close()
    with pytest.raises(sqlite3.ProgrammingError):
        db.count()
    # closing again is fine
    db.close()

    with GribIndex(db_path) as db:
        assert db.count() == 18
    with pytest.raises(sqlite3.ProgrammingError):
        db.count()

    # failed open does not leak the connection
    with pytest.raises(FileNotFoundError):
        GribIndex.open(str(tmp_path / "missing.grib"), db_path)


def test_grib_index_db_without_db_path_needs_one_file():
    _, paths = get_tmp_fixture("multi")
    with pytest.raises(ValueError, match="single file"):
        GribIndex.open(paths)


def test_grib_index_db_cache_policy_off():
    _, path = get_tmp_fixture("file")

    with config.temporary("cache-policy", "off"):
        for func in [
            lambda: GribIndex.open(path),
            lambda: GribIndex.from_file(path),
            lambda: GribIndex.cache_db_path(path),
            lambda: GribIndex.cache_db_path(path, create=True),
            lambda: GribIndex.find_in_cache(path),
        ]:
            with pytest.raises(ValueError, match="cache-policy") as e:
                func()
            assert "'user'" in str(e.value) and "'temporary'" in str(e.value)


@pytest.mark.cache
def test_grib_index_db_cache_helper_create_and_lookup(monkeypatch):
    _, path = get_tmp_fixture("file")
    scanned = _scan_counter(monkeypatch)

    expected = GribIndex.cache_db_path(path)
    assert expected.endswith(".sqlite")

    # computing the path or looking up creates nothing
    assert not os.path.exists(expected)
    assert GribIndex.find_in_cache(path) is None
    assert not os.path.exists(expected)
    assert not os.path.exists(GribIndex.cache_db_path(path, extra_keys=EXTRA_KEY))

    with GribIndex.open(path) as db:
        assert db.path == expected
        assert db.count() == 18
        assert db.paths() == [path]
    assert scanned == [os.path.basename(path)]
    state = _db_state(expected)

    # lookup finds the same db, with no write
    with GribIndex.find_in_cache(path) as db:
        assert db.path == expected
        assert db.count() == 18
    assert _db_state(expected) == state

    # the extra keys are part of the key: different db, nothing found
    db_extra = GribIndex.cache_db_path(path, extra_keys=[EXTRA_KEY])
    assert db_extra != expected
    assert GribIndex.cache_db_path(path, extra_keys=[EXTRA_KEY, "b"]) == GribIndex.cache_db_path(
        path, extra_keys=["b", EXTRA_KEY, "b"]
    )
    assert GribIndex.find_in_cache(path, extra_keys=EXTRA_KEY) is None
    assert not os.path.exists(db_extra)

    with GribIndex.open(path, extra_keys=EXTRA_KEY) as db:
        assert db.path == db_extra
        assert db.count() == 18
    with GribIndex.find_in_cache(path, extra_keys=EXTRA_KEY) as db:
        assert db.path == db_extra

    # open again: the same db is reused without scanning
    state = _db_state(expected)
    with GribIndex.open(path) as db:
        assert db.path == expected
    assert _db_state(expected) == state
    assert len(scanned) == 2


@pytest.mark.cache
def test_grib_index_db_cache_changed_file(tmp_path):
    path = str(tmp_path / "data.grib")
    shutil.copy(earthkit_examples_file("tuv_pl.grib"), path)

    with GribIndex.open(path) as db:
        db_path = db.path
        assert db.count() == 18

    st = os.stat(path)
    os.utime(path, ns=(st.st_atime_ns, st.st_mtime_ns + 5_000_000_000))

    # the key of the cache db contains the identity of the file
    assert GribIndex.cache_db_path(path) != db_path
    assert GribIndex.find_in_cache(path) is None


@pytest.mark.cache
def test_grib_index_db_find_in_cache_stale_content():
    # a cache db that does not hold an up-to-date entry for the file is not returned
    _, path = get_tmp_fixture("file")
    db_path = GribIndex.cache_db_path(path, create=True)
    assert os.path.getsize(db_path) == 0
    assert GribIndex.find_in_cache(path) is None

    GribIndex(db_path).close()
    assert GribIndex.find_in_cache(path) is None

    with GribIndex.open(path) as db:
        assert db.count() == 18
    with GribIndex.find_in_cache(path) as db:
        assert db.count() == 18
