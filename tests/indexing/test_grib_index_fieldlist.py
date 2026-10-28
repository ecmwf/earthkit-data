#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import pickle

import eccodes
import numpy as np
import pytest
from indexing_fixtures import get_tmp_fixture  # noqa: E402

from earthkit.data import from_source
from earthkit.data.readers.grib.file import IndexedGribFieldListInFile
from earthkit.data.readers.grib.index import GribIndex
from earthkit.data.utils.testing import earthkit_examples_file, earthkit_test_data_file

COMPONENT_KEYS = [
    "parameter.variable",
    "time.base_datetime",
    "time.step",
    "time.valid_datetime",
    "vertical.level",
    "vertical.level_type",
    "ensemble.member",
]
RAW_KEYS = [
    "metadata.shortName",
    "metadata.param",
    "metadata.level",
    "metadata.typeOfLevel",
    "metadata.number",
    "metadata.date",
    "metadata.dataTime",
]

FILES = {
    "tuv_pl": earthkit_examples_file("tuv_pl.grib"),
    "ens_50": earthkit_test_data_file("ens_50.grib"),
    "t_time_series": earthkit_test_data_file("t_time_series.grib"),
    "O32": earthkit_test_data_file("O32_global.grib1"),
}


@pytest.fixture
def handle_counter(monkeypatch):
    """Count the eccodes handles created from files or messages."""
    counter = {"n": 0}

    def _wrap(name):
        orig = getattr(eccodes, name)

        def _new(*args, **kwargs):
            counter["n"] += 1
            return orig(*args, **kwargs)

        monkeypatch.setattr(eccodes, name, _new)

    _wrap("codes_new_from_file")
    _wrap("codes_new_from_message")
    return counter


def _build_db(tmp_path, path, **kwargs):
    db_path = str(tmp_path / "idx.sqlite")
    GribIndex.open(path, db_path=db_path, **kwargs).close()
    return db_path


def _same_list(a, b):
    assert len(a) == len(b)
    for x, y in zip(a, b):
        assert x == y
        assert type(x) is type(y)


def _check_equal(fl, plain, keys):
    assert len(fl) == len(plain)
    for k in keys:
        _same_list(fl.get(k), plain.get(k))


@pytest.fixture(params=list(FILES))
def indexed(request, tmp_path):
    path = FILES[request.param]
    db_path = _build_db(tmp_path, path)
    plain = from_source("file", path).to_fieldlist()
    return path, db_path, plain


def test_grib_index_fieldlist_no_handle(indexed, handle_counter):
    path, db_path, plain = indexed

    handle_counter["n"] = 0
    fl = IndexedGribFieldListInFile(path, db_path)
    assert len(fl) == len(plain)
    assert fl.number_of_parts() == len(plain)
    assert [fl.part(i).offset for i in range(len(fl))] == [plain.part(i).offset for i in range(len(plain))]
    assert [fl.part(i).length for i in range(len(fl))] == [plain.part(i).length for i in range(len(plain))]

    # the plain fieldlist is not used here to avoid its handles in the counts
    n_plain = len(plain)
    handle_counter["n"] = 0
    for k in COMPONENT_KEYS + RAW_KEYS:
        fl.get(k)
    assert fl[0].get("metadata.shortName") is not None
    assert fl[0].get("metadata.number", default=-1) is not None
    assert len(fl) == n_plain
    assert handle_counter["n"] == 0

    f = fl[0]
    assert f.shape is not None
    assert f.geography.shape() is not None
    assert handle_counter["n"] == 0


def test_grib_index_fieldlist_equal_plain(indexed, handle_counter):
    path, db_path, plain = indexed

    # reference values first, they create handles
    ref = {k: plain.get(k) for k in COMPONENT_KEYS + RAW_KEYS}
    ref_shape = [f.shape for f in plain]
    ref_geo_shape = [f.geography.shape() for f in plain]

    handle_counter["n"] = 0
    fl = IndexedGribFieldListInFile(path, db_path)
    for k, v in ref.items():
        _same_list(fl.get(k), v)
    assert [f.shape for f in fl] == ref_shape
    assert [f.geography.shape() for f in fl] == ref_geo_shape
    assert handle_counter["n"] == 0


def test_grib_index_fieldlist_sel_order_by_no_handle(tmp_path, handle_counter):
    path = FILES["tuv_pl"]
    db_path = _build_db(tmp_path, path)
    plain = from_source("file", path).to_fieldlist()

    p_sel = plain.sel(**{"parameter.variable": "t", "vertical.level": [500, 850]})
    p_sel_raw = plain.sel(**{"metadata.shortName": "u", "metadata.level": 300})
    p_ord = plain.order_by(["parameter.variable", "-vertical.level"])
    p_ord_raw = plain.order_by(["metadata.shortName", "metadata.level"])
    expected = [
        (p_sel.get("parameter.variable"), p_sel.get("vertical.level")),
        (p_sel_raw.get("parameter.variable"), p_sel_raw.get("vertical.level")),
        (p_ord.get("parameter.variable"), p_ord.get("vertical.level")),
        (p_ord_raw.get("parameter.variable"), p_ord_raw.get("vertical.level")),
    ]
    assert len(p_sel) == 2 and len(p_sel_raw) == 1

    handle_counter["n"] = 0
    fl = IndexedGribFieldListInFile(path, db_path)
    r_sel = fl.sel(**{"parameter.variable": "t", "vertical.level": [500, 850]})
    r_sel_raw = fl.sel(**{"metadata.shortName": "u", "metadata.level": 300})
    r_ord = fl.order_by(["parameter.variable", "-vertical.level"])
    r_ord_raw = fl.order_by(["metadata.shortName", "metadata.level"])
    res = [
        (r_sel.get("parameter.variable"), r_sel.get("vertical.level")),
        (r_sel_raw.get("parameter.variable"), r_sel_raw.get("vertical.level")),
        (r_ord.get("parameter.variable"), r_ord.get("vertical.level")),
        (r_ord_raw.get("parameter.variable"), r_ord_raw.get("vertical.level")),
    ]
    assert handle_counter["n"] == 0
    assert res == expected


def test_grib_index_fieldlist_multi_file_no_handle(tmp_path, handle_counter):
    # the files are indexed in one db
    _, paths = get_tmp_fixture("multi")
    db_path = str(tmp_path / "multi.sqlite")
    GribIndex.open(paths, db_path=db_path).close()

    for path in paths:
        plain = from_source("file", path).to_fieldlist()
        ref = {k: plain.get(k) for k in COMPONENT_KEYS + RAW_KEYS}

        handle_counter["n"] = 0
        fl = IndexedGribFieldListInFile(path, db_path)
        assert len(fl) == len(plain)
        for k, v in ref.items():
            _same_list(fl.get(k), v)
        assert handle_counter["n"] == 0


def test_grib_index_fieldlist_values(indexed):
    path, db_path, plain = indexed
    fl = IndexedGribFieldListInFile(path, db_path)

    assert np.array_equal(fl.to_numpy(), plain.to_numpy(), equal_nan=True)
    for f, p in zip(fl, plain):
        assert np.array_equal(f.values, p.values, equal_nan=True)
        assert np.array_equal(f.to_numpy(flatten=True), p.to_numpy(flatten=True), equal_nan=True)
        assert f.shape == p.shape


def test_grib_index_fieldlist_unstored_raw_key(tmp_path, handle_counter):
    path = FILES["tuv_pl"]
    db_path = _build_db(tmp_path, path)
    plain = from_source("file", path).to_fieldlist()
    ref = plain.get("metadata.bitsPerValue")
    ref_str = plain.get("metadata.shortName:s")
    ref_missing = plain.get("metadata.notAKeyAtAll")
    assert all(x is not None for x in ref)

    with GribIndex(db_path) as db:
        assert "metadata.bitsPerValue" not in db._dynamic_columns()

    fl = IndexedGribFieldListInFile(path, db_path)
    handle_counter["n"] = 0
    assert fl.get("metadata.bitsPerValue") == ref
    assert handle_counter["n"] > 0
    assert fl.get("metadata.shortName:s") == ref_str
    assert fl.get("metadata.notAKeyAtAll") == ref_missing
    assert fl.get("metadata.notAKeyAtAll", default=3) == plain.get("metadata.notAKeyAtAll", default=3)

    # a stored key with a different type is read from the handle
    assert fl.get("metadata.level", astype=str) == plain.get("metadata.level", astype=str)


def _outcome(f, key, **kwargs):
    try:
        return ("value", f.get(key, **kwargs))
    except KeyError as e:
        return ("KeyError", str(e))


@pytest.mark.parametrize(
    "name,path,key,missing",
    [
        # a default key that the deterministic messages do not have: NULL means "missing"
        ("ll_10_20", earthkit_test_data_file("ll_10_20.grib"), "metadata.levelist", True),
        ("mercator", earthkit_test_data_file("mercator.grib"), "metadata.number", True),
        ("mercator", earthkit_test_data_file("mercator.grib"), "metadata.expver", True),
        # the same key in an ensemble: it has a value
        ("ens_50", FILES["ens_50"], "metadata.number", False),
        ("tuv_pl", FILES["tuv_pl"], "metadata.number", False),
    ],
)
def test_grib_index_fieldlist_none_means_missing_for_default_keys(tmp_path, handle_counter, name, path, key, missing):
    db_path = _build_db(tmp_path, path)

    variants = [
        {},
        {"default": -1},
        {"raise_on_missing": True},
        {"default": -1, "astype": int},
        {"default": "x", "astype": str},
    ]

    plain = from_source("file", path).to_fieldlist()
    refs = [[_outcome(f, key, **kw) for kw in variants] for f in plain]
    assert all((r[2][0] == "KeyError") == missing for r in refs)

    fl = IndexedGribFieldListInFile(path, db_path)
    handle_counter["n"] = 0
    res = [[_outcome(f, key, **kw) for kw in variants] for f in fl]
    assert res == refs
    if missing:
        # known to be missing: no need to read the message
        assert handle_counter["n"] == 0


def test_grib_index_fieldlist_none_means_unknown_for_other_keys(tmp_path, handle_counter):
    # "bitsPerValue" is scanned only for the second file: NULL for the first file means
    # "unknown" and it is read from the handle
    path_a = FILES["tuv_pl"]
    path_b = FILES["ens_50"]
    db_path = str(tmp_path / "idx.sqlite")
    GribIndex.open(path_a, db_path=db_path).close()
    GribIndex.open(path_b, db_path=db_path, extra_keys=["bitsPerValue", "notAKeyAtAll"]).close()

    plain_a = from_source("file", path_a).to_fieldlist()
    plain_b = from_source("file", path_b).to_fieldlist()
    ref_a = plain_a.get("metadata.bitsPerValue")
    ref_b = plain_b.get("metadata.bitsPerValue")
    ref_b_missing = [_outcome(f, "metadata.notAKeyAtAll", raise_on_missing=True) for f in plain_b]
    assert all(x is not None for x in ref_a + ref_b)

    # first file: handle is needed
    fl_a = IndexedGribFieldListInFile(path_a, db_path)
    handle_counter["n"] = 0
    assert fl_a.get("metadata.bitsPerValue") == ref_a
    assert handle_counter["n"] > 0

    # second file: served from the index, also the key the messages do not have
    fl_b = IndexedGribFieldListInFile(path_b, db_path)
    handle_counter["n"] = 0
    _same_list(fl_b.get("metadata.bitsPerValue"), ref_b)
    assert [_outcome(f, "metadata.notAKeyAtAll", raise_on_missing=True) for f in fl_b] == ref_b_missing
    assert fl_b.get("metadata.notAKeyAtAll", default=7) == [7] * len(fl_b)
    assert handle_counter["n"] == 0


def test_grib_index_fieldlist_pickle(indexed):
    path, db_path, plain = indexed
    fl = IndexedGribFieldListInFile(path, db_path)
    # force the fields to be created before pickling
    assert len(fl[0].get("parameter.variable")) > 0

    fl2 = pickle.loads(pickle.dumps(fl))
    assert isinstance(fl2, IndexedGribFieldListInFile)
    assert len(fl2) == len(fl)
    assert fl2.get("parameter.variable") == fl.get("parameter.variable")
    assert fl2.get("metadata.shortName") == fl.get("metadata.shortName")
    assert np.array_equal(fl2.to_numpy(), plain.to_numpy(), equal_nan=True)


def test_grib_index_fieldlist_pickle_does_not_pickle_fields(tmp_path):
    path = FILES["tuv_pl"]
    db_path = _build_db(tmp_path, path)
    fl = IndexedGribFieldListInFile(path, db_path)
    fl.get("parameter.variable")

    state = fl.__getstate__()
    assert set(state) == {"path", "db_path", "kwargs"}
    assert state["db_path"] == db_path


def test_grib_index_fieldlist_db_closed(tmp_path, monkeypatch):
    import sqlite3

    path = FILES["tuv_pl"]
    db_path = _build_db(tmp_path, path)

    connections = []
    orig = sqlite3.connect

    def _connect(*args, **kwargs):
        c = orig(*args, **kwargs)
        connections.append(c)
        return c

    monkeypatch.setattr(sqlite3, "connect", _connect)

    fl = IndexedGribFieldListInFile(path, db_path)
    assert len(fl) == 18
    fl.get("parameter.variable")

    assert len(connections) >= 1
    for c in connections:
        with pytest.raises(sqlite3.ProgrammingError):
            c.execute("SELECT 1")


def test_grib_index_fieldlist_missing_db(tmp_path):
    path = FILES["tuv_pl"]
    with pytest.raises(FileNotFoundError):
        IndexedGribFieldListInFile(path, str(tmp_path / "nope.sqlite"))
    assert not (tmp_path / "nope.sqlite").exists()


def test_grib_index_fieldlist_path_not_in_db(tmp_path):
    db_path = _build_db(tmp_path, FILES["tuv_pl"])
    fl = IndexedGribFieldListInFile(FILES["ens_50"], db_path)
    with pytest.raises(ValueError):
        len(fl)


def test_grib_index_fieldlist_no_geography_keys(tmp_path, handle_counter):
    # the geography of this unstructured grid cannot be indexed (and cannot be built by the plain
    # reader either): the row has no geography keys, but the field is built and behaves like the plain one
    path = earthkit_test_data_file("test_icon.grib")
    db_path = _build_db(tmp_path, path)

    with GribIndex(db_path) as db:
        assert not any(k.startswith("geography.") for r in db.rows(path) for k in r)

    plain = from_source("file", path).to_fieldlist()
    ref_var = plain.get("parameter.variable")
    ref_values = plain.to_numpy()
    ref_shape = plain[0].shape

    def _geo(f):
        try:
            return ("value", f.geography.shape())
        except Exception:
            # the exact exception differs: the plain handler fails later with an AttributeError
            return ("error", None)

    ref_geo = _geo(plain[0])

    handle_counter["n"] = 0
    fl = IndexedGribFieldListInFile(path, db_path)
    assert len(fl) == len(plain)
    _same_list(fl.get("parameter.variable"), ref_var)
    assert handle_counter["n"] == 0

    assert np.array_equal(fl.to_numpy(), ref_values, equal_nan=True)
    assert fl[0].shape == ref_shape
    assert _geo(fl[0]) == ref_geo
    assert handle_counter["n"] > 0
