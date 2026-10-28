#!/usr/bin/env python3

# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

"""Hybrid (parametric) vertical levels of fieldlists built from the GRIB index."""

import eccodes
import numpy as np
import pytest

from earthkit.data import from_source
from earthkit.data.readers.grib.file import IndexedGribFieldListInFile
from earthkit.data.readers.grib.index import GribIndex
from earthkit.data.utils.testing import earthkit_examples_file, earthkit_test_data_file

STORED_KEYS = [
    "vertical.level",
    "vertical.level_type",
    "vertical.layer",
    "vertical.units",
    "vertical.abbreviation",
    "vertical.cf",
    "vertical.positive",
    "vertical.parametric",
    "vertical.number_of_levels",
    "vertical.coefficient_names",
]


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


def _build_db(tmp_path, path):
    db_path = str(tmp_path / "idx.sqlite")
    GribIndex.open(path, db_path=db_path).close()
    return db_path


def _same(a, b):
    if isinstance(a, tuple):
        assert isinstance(b, tuple)
        assert len(a) == len(b)
        for x, y in zip(a, b):
            _same(x, y)
    elif isinstance(a, np.ndarray) or isinstance(b, np.ndarray):
        np.testing.assert_array_equal(a, b)
    else:
        assert a == b
        assert type(a) is type(b)


def test_grib_index_vertical_hybrid(tmp_path, handle_counter):
    path = earthkit_test_data_file("O32_global.grib2")
    plain = from_source("file", path).to_fieldlist()
    assert plain[0].get("vertical.level_type") == "hybrid"
    assert plain[0].get("vertical.parametric") is True

    # reference values first, they create handles
    ref = {k: [f.get(k) for f in plain] for k in STORED_KEYS}
    ref_coeffs = [f.get("vertical.coefficients") for f in plain]
    ref_coeffs_m = [f.vertical.coefficients() for f in plain]
    assert ref["vertical.number_of_levels"][0] is not None
    assert ref_coeffs[0] is not None

    db_path = _build_db(tmp_path, path)

    handle_counter["n"] = 0
    fl = IndexedGribFieldListInFile(path, db_path)
    assert len(fl) == len(plain)

    # the stored keys do not need a handle
    for k, v in ref.items():
        got = [f.get(k) for f in fl]
        assert len(got) == len(v)
        for x, y in zip(got, v):
            _same(x, y)
    assert [f.vertical.level() for f in fl] == ref["vertical.level"]
    assert fl.get("vertical.level") == plain.get("vertical.level")
    assert fl.get("vertical.level_type") == plain.get("vertical.level_type")
    assert handle_counter["n"] == 0

    # the coefficients are read from the handle
    for f, expected, expected_m in zip(fl, ref_coeffs, ref_coeffs_m):
        _same(f.get("vertical.coefficients"), expected)
        _same(f.vertical.coefficients(), expected_m)
    assert handle_counter["n"] > 0


def test_grib_index_vertical_hybrid_lazy_per_field(tmp_path, handle_counter):
    path = earthkit_test_data_file("O32_global.grib2")
    db_path = _build_db(tmp_path, path)
    plain = from_source("file", path).to_fieldlist()
    ref = plain[0].vertical.coefficients()

    handle_counter["n"] = 0
    fl = IndexedGribFieldListInFile(path, db_path)
    v = fl[0].vertical
    assert v.level() == plain[0].vertical.level()
    assert v.number_of_levels() == plain[0].vertical.number_of_levels()
    assert v.coefficient_names() == ("A", "B")
    assert handle_counter["n"] == 0

    A, B = v.coefficients()
    assert handle_counter["n"] > 0
    np.testing.assert_array_equal(A, ref[0])
    np.testing.assert_array_equal(B, ref[1])


def test_grib_index_vertical_hybrid_set(tmp_path):
    # changing the level keeps the coefficients
    path = earthkit_test_data_file("O32_global.grib2")
    db_path = _build_db(tmp_path, path)
    plain = from_source("file", path).to_fieldlist()
    fl = IndexedGribFieldListInFile(path, db_path)

    f = fl[0].set({"vertical.level": 10})
    p = plain[0].set({"vertical.level": 10})
    assert f.get("vertical.level") == 10
    assert f.get("vertical.number_of_levels") == p.get("vertical.number_of_levels")
    _same(f.get("vertical.coefficients"), p.get("vertical.coefficients"))


@pytest.mark.parametrize("path", [earthkit_examples_file("tuv_pl.grib"), earthkit_test_data_file("ll_10_20.grib")])
def test_grib_index_vertical_non_parametric_no_handle(path, tmp_path, handle_counter):
    plain = from_source("file", path).to_fieldlist()
    ref = {k: plain.get(k) for k in STORED_KEYS}
    assert plain[0].get("vertical.parametric") is False

    db_path = _build_db(tmp_path, path)

    handle_counter["n"] = 0
    fl = IndexedGribFieldListInFile(path, db_path)
    for k, v in ref.items():
        assert fl.get(k) == v, k
    f = fl[0]
    assert f.vertical.coefficients() is None
    assert f.vertical.number_of_levels() is None
    assert type(f.vertical).__name__ == "Vertical"
    assert handle_counter["n"] == 0
