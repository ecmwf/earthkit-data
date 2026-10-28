#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""The indexer must work on every valid sample GRIB file and store what the plain fieldlist gives."""

import os

import pytest

from earthkit.data import from_source
from earthkit.data.readers.grib.index import GribIndex
from earthkit.data.utils.testing import earthkit_test_data_file

DATA_DIR = os.path.dirname(earthkit_test_data_file("test.grib"))
MAX_SIZE = 20 * 1024 * 1024
GRIB_EXTENSIONS = (".grib", ".grib1", ".grib2")

COMPONENT_KEYS = [
    "parameter.variable",
    "time.base_datetime",
    "time.step",
    "vertical.level",
    "vertical.level_type",
    "ensemble.member",
]


def _is_grib(path):
    if path.endswith(GRIB_EXTENSIONS):
        return True
    try:
        with open(path, "rb") as f:
            return f.read(4) == b"GRIB"
    except OSError:
        return False


def _sample_files():
    r = []
    for root, _, files in os.walk(DATA_DIR):
        for name in files:
            path = os.path.join(root, name)
            if _is_grib(path):
                r.append(os.path.relpath(path, DATA_DIR))
    return sorted(r)


SAMPLE_FILES = _sample_files()


def _plain_value(field, key):
    """Value of a component key in the plain field; None when its component cannot be built."""
    try:
        return field.get(key, default=None)
    except AttributeError:
        # raised by the lazy component handler when the component cannot be built
        return None


def _index(path, tmp_path):
    return GribIndex.open(path, db_path=str(tmp_path / "index.sqlite"))


def _compare_with_plain(path, tmp_path, keys):
    fl = from_source("file", path).to_fieldlist()
    with _index(path, tmp_path) as index:
        rows = list(index.rows(path))
        assert index.count(path) == len(fl) == len(rows)

        for row, f in zip(rows, fl):
            for key in keys:
                assert row.get(key) == _plain_value(f, key), key
    return rows


def test_grib_index_samples_found():
    assert len(SAMPLE_FILES) > 20
    assert "test_icon.grib" in SAMPLE_FILES
    assert "t_year_missing.grib" in SAMPLE_FILES


@pytest.mark.parametrize("name", SAMPLE_FILES)
def test_grib_index_all_samples(name, tmp_path):
    path = os.path.join(DATA_DIR, name)
    if os.path.getsize(path) > MAX_SIZE:
        pytest.skip(f"{name}: larger than 20 MB")

    try:
        fl = from_source("file", path).to_fieldlist()
        n = len(fl)
    except Exception as e:
        pytest.skip(f"{name}: the plain reader cannot read it as a fieldlist ({e!r})")

    if n == 0:
        pytest.skip(f"{name}: the plain reader finds no fields")

    with _index(path, tmp_path) as index:
        assert index.count(path) == n

    _compare_with_plain(path, tmp_path, COMPONENT_KEYS)
    _compare_indexed_fieldlist_with_plain(path, tmp_path)


def _compare_indexed_fieldlist_with_plain(path, tmp_path):
    """Build the fieldlist from the index and compare ``len`` and the component keys with the plain one.

    Where the plain component cannot be built the plain ``get`` raises AttributeError
    (``t_year_missing.grib``, time), while the indexed field returns None for the key, because
    the keys of the component are not stored in the index. Both are mapped to None
    by ``_plain_value``; ``test_grib_index_year_missing`` checks the indexed side explicitly.
    """
    from earthkit.data.readers.grib.file import IndexedGribFieldListInFile

    db_path = str(tmp_path / "index.sqlite")
    GribIndex.open(path, db_path=db_path).close()

    plain = from_source("file", path).to_fieldlist()
    fl = IndexedGribFieldListInFile(path, db_path)
    assert len(fl) == len(plain)

    for f, p in zip(fl, plain):
        for key in COMPONENT_KEYS:
            assert _plain_value(f, key) == _plain_value(p, key), key
    return fl


def test_grib_index_fieldlist_hybrid(tmp_path):
    # hybrid levels: the coefficients are not stored, they are read from the file on demand
    path = earthkit_test_data_file("O32_global.grib2")
    fl = _compare_indexed_fieldlist_with_plain(path, tmp_path)
    plain = from_source("file", path).to_fieldlist()
    assert fl[0].get("vertical.level_type") == "hybrid"
    assert fl[0].get("vertical.number_of_levels") == plain[0].get("vertical.number_of_levels")
    for a, b in zip(fl[0].get("vertical.coefficients"), plain[0].get("vertical.coefficients")):
        assert (a == b).all()


def test_grib_index_icon(tmp_path):
    # unstructured grid with an unknown grid uid and without gridName: the plain geography
    # component cannot be built (ValueError) but all the other components can.
    path = earthkit_test_data_file("test_icon.grib")
    rows = _compare_with_plain(path, tmp_path, COMPONENT_KEYS)
    assert len(rows) == 9

    import datetime

    assert rows[0]["time.base_datetime"] == datetime.datetime(2022, 2, 16, 0, 0)
    assert rows[0]["time.step"] == datetime.timedelta(hours=1)
    assert rows[0]["parameter.variable"] is not None
    assert rows[0]["vertical.level"] is not None
    assert rows[0]["ensemble.member"] is not None


def test_grib_index_year_missing(tmp_path):
    # the date of the message is invalid, so the plain time component cannot be built
    path = earthkit_test_data_file("t_year_missing.grib")

    fl = from_source("file", path).to_fieldlist()
    assert _plain_value(fl[0], "time.base_datetime") is None
    # the other components work
    assert fl[0].get("parameter.variable") is not None

    rows = _compare_with_plain(path, tmp_path, COMPONENT_KEYS)
    assert len(rows) == 1
    assert rows[0].get("time.base_datetime") is None
    assert rows[0].get("time.step") is None
    assert rows[0]["parameter.variable"] == fl[0].get("parameter.variable")
    assert rows[0]["vertical.level"] == fl[0].get("vertical.level")

    # the fieldlist built from the index returns None (it does not raise) for the missing time keys
    ifl = _compare_indexed_fieldlist_with_plain(path, tmp_path)
    assert ifl[0].get("time.base_datetime", default=None) is None
    assert ifl[0].get("time.step", default=None) is None
    assert ifl[0].get("parameter.variable") == fl[0].get("parameter.variable")
