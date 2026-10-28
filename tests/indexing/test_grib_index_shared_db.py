#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Tests of a db shared by heterogeneous GRIB files and by several connections."""

import os

import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.readers.grib.index import GribIndex
from earthkit.data.utils.testing import earthkit_test_data_file

LL = earthkit_test_data_file("ll_10_20.grib")
CHEM = earthkit_test_data_file("chem-cams.grib")
UNSTRUCTURED = earthkit_test_data_file("unstructured_6_points.grib2")
REDUCED_GG = earthkit_test_data_file("O32_global.grib1")

PARAMETER_KEYS = [
    "parameter.variable",
    "parameter.units",
    "parameter.chem",
    "vertical.level",
    "vertical.level_type",
    "time.step",
]


def _plain(paths):
    return from_source("file", list(paths)).to_fieldlist()


def _indexed(paths, db_path):
    return from_source("file", list(paths)).to_fieldlist(index=str(db_path))


def _same_values(a, b):
    """The Python values are the same, also for lists/tuples."""
    assert type(a) is type(b), (a, b)
    assert a == b


def _assert_same_fieldlists(indexed, plain, keys):
    assert len(indexed) == len(plain)
    for key in keys:
        got, expected = indexed.get(key), plain.get(key)
        assert len(got) == len(expected)
        for g, e in zip(got, expected):
            _same_values(g, e)

    for f, p in zip(indexed, plain):
        assert f.shape == p.shape
        np.testing.assert_array_equal(f.to_numpy(), p.to_numpy())


@pytest.mark.parametrize("order", ["ll_chem", "chem_ll"])
def test_grib_index_shared_db_chem_and_ll(tmp_path, order):
    paths = [LL, CHEM] if order == "ll_chem" else [CHEM, LL]
    db_path = tmp_path / "idx.sqlite"

    _assert_same_fieldlists(_indexed(paths, db_path), _plain(paths), PARAMETER_KEYS)

    # each file on its own from the shared db
    with GribIndex(db_path) as db:
        assert db.count() == 1 + 3
    for p in paths:
        _assert_same_fieldlists(_indexed([p], db_path), _plain([p]), PARAMETER_KEYS)

    # the key of the chem file is not given to the fields without it
    ll = _indexed([LL], db_path)
    assert ll[0].get("parameter.chem") is None
    assert "chem" not in ll[0].parameter.to_dict()


@pytest.mark.parametrize("order", ["ll_chem", "chem_ll"])
def test_grib_index_shared_db_file_added_later(tmp_path, order):
    first, second = (LL, CHEM) if order == "ll_chem" else (CHEM, LL)
    db_path = tmp_path / "idx.sqlite"

    # the db has only the first file, its rows are read again after the new columns appear
    _assert_same_fieldlists(_indexed([first], db_path), _plain([first]), PARAMETER_KEYS)
    before = _indexed([first], db_path)

    _assert_same_fieldlists(_indexed([first, second], db_path), _plain([first, second]), PARAMETER_KEYS)
    # a fieldlist created before the db changed is still valid
    _assert_same_fieldlists(before, _plain([first]), PARAMETER_KEYS)
    # and one created after has the same fields for the first file
    _assert_same_fieldlists(_indexed([first], db_path), _plain([first]), PARAMETER_KEYS)


def test_grib_index_shared_db_mixed_grids(tmp_path):
    paths = [LL, UNSTRUCTURED, REDUCED_GG]
    db_path = tmp_path / "idx.sqlite"

    plain = _plain(paths)
    indexed = _indexed(paths, db_path)

    _assert_same_fieldlists(indexed, plain, [*PARAMETER_KEYS, "geography.unique_grid_id"])
    assert [f.shape for f in indexed] == [f.shape for f in plain]

    # the unique grid id is a str for some grids and a list for others
    ids = plain.get("geography.unique_grid_id")
    assert len({type(i) for i in ids}) > 1

    # also each file alone, from the shared db and with the other grids added later
    for p in paths:
        _assert_same_fieldlists(_indexed([p], db_path), _plain([p]), ["geography.unique_grid_id"])

    # all four files, in another order, into one db
    paths = [REDUCED_GG, CHEM, UNSTRUCTURED, LL]
    _assert_same_fieldlists(
        _indexed(paths, tmp_path / "idx2.sqlite"),
        _plain(paths),
        [*PARAMETER_KEYS, "geography.unique_grid_id"],
    )


def test_grib_index_shared_db_raw_keys_of_heterogeneous_files(tmp_path):
    # a raw key that one of the files does not have is missing for it, as for the plain list
    paths = [LL, CHEM]
    db_path = tmp_path / "idx.sqlite"

    with GribIndex.open(paths, db_path, extra_keys=["bitsPerValue"]):
        pass

    plain = _plain(paths)
    indexed = _indexed(paths, db_path)
    keys = ["metadata.shortName", "metadata.level", "metadata.typeOfLevel", "metadata.number", "metadata.edition"]
    for key in keys:
        assert indexed.get(key) == plain.get(key), key
    assert indexed.get("metadata.thisKeyDoesNotExist", default=-1) == plain.get(
        "metadata.thisKeyDoesNotExist", default=-1
    )


def test_grib_index_shared_db_two_connections_interleaved(tmp_path):
    t, u = (earthkit_test_data_file(f"{x}_pl.grib") for x in ("t", "u"))
    db_path = str(tmp_path / "idx.sqlite")
    key = "metadata.bitsPerValue"

    a = GribIndex(db_path)
    b = GribIndex(db_path)
    try:
        # A knows the schema as it is after indexing the first file
        a.add_file(LL)
        assert key not in a._dynamic_columns()

        # B adds a file with an extra key: a new column and new values
        assert b.add_file(u, extra_keys="bitsPerValue")
        assert key in b._dynamic_columns()

        # A indexes a file with the same extra key: no clash with what B did
        assert a.add_file(t, extra_keys="bitsPerValue")

        # A sees what B wrote, and the other way round
        for db in (a, b):
            assert db.paths() == [os.path.abspath(p) for p in (LL, u, t)]
            assert db.count() == 1 + 6 + 6
            assert db.count(u) == 6
            assert db.count(t) == 6
            assert key in db._dynamic_columns()
            rows = list(db.rows(u))
            assert len(rows) == 6
            assert all(isinstance(r[key], int) for r in rows)
            assert all(isinstance(r[key], int) for r in db.rows(t))
            # the first file was scanned without the key
            assert all(key not in r for r in db.rows(LL))
    finally:
        a.close()
        b.close()

    # and the db gives the same as the plain files
    paths = [LL, u, t]
    plain = _plain(paths)
    indexed = _indexed(paths, db_path)
    _assert_same_fieldlists(indexed, plain, PARAMETER_KEYS)


def test_grib_index_shared_db_two_connections_new_column_seen_by_reader(tmp_path):
    db_path = str(tmp_path / "idx.sqlite")
    key = "metadata.bitsPerValue"

    with GribIndex.open(LL, db_path) as writer:
        reader = GribIndex(db_path)
        try:
            assert key not in reader._dynamic_columns()
            assert all(key not in r for r in reader.rows(LL))

            writer.add_file(CHEM, extra_keys="bitsPerValue")
            assert reader.count() == 1 + 3

            # the reader sees the new column and the new rows without reconnecting
            assert key in reader._dynamic_columns()
            rows = list(reader.rows(CHEM))
            assert len(rows) == 3
            assert all(key in r for r in rows)
            assert any("parameter.chem" in r for r in rows)
            assert all("parameter.chem" not in r for r in reader.rows(LL))
        finally:
            reader.close()
