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
from indexing_fixtures import get_tmp_fixture  # noqa: E402

from earthkit.data import from_source
from earthkit.data.readers.grib.index import GribIndex


@pytest.mark.cache
def test_indexing_db_file_single():
    _, path = get_tmp_fixture("file")
    d = from_source("file", path, grib_index=True)
    fl = d.to_fieldlist()

    db = GribIndex._find_db_in_cache(path)
    assert db is not None
    db_path = db.path
    st = os.stat(db.path)
    db_size = st.st_size
    db_modified = st.st_mtime
    assert db.count() == 18
    assert fl.get("parameter.variable") == ["t", "u", "v"] * 6

    # repeated use
    # The db path, size, modtime should be the same as before
    d = from_source("file", path, grib_index=True)
    fl = d.to_fieldlist()

    db = GribIndex._find_db_in_cache(path)
    assert db is not None
    assert db.path == db_path
    st = os.stat(db.path)
    assert st.st_size == db_size
    assert st.st_mtime == db_modified
    assert db.count() == 18
    assert fl.get("parameter.variable") == ["t", "u", "v"] * 6


@pytest.mark.cache
def test_indexing_db_file_multi():
    _, path = get_tmp_fixture("multi")
    d = from_source("file", path, grib_index=True)
    fl = d.to_fieldlist()

    counts = [6, 6, 6]
    db_paths = []
    db_size = []
    db_modified = []
    for i, path_i in enumerate(path):
        db = GribIndex._find_db_in_cache(path_i)
        assert db is not None, f"db is None for path={path_i}"
        db_paths.append(db.path)
        st = os.stat(db.path)
        db_size.append(st.st_size)
        db_modified.append(st.st_mtime)
        assert db.count() == counts[i], f"db.count()={db.count()} for path={path_i}, expected={counts[i]}"

    assert fl.get("parameter.variable") == ["t"] * 6 + ["u"] * 6 + ["v"] * 6

    # Repeated use
    # The db paths, size, modtime should be the same as before
    d = from_source("file", path, grib_index=True)
    fl = d.to_fieldlist()

    for i, path_i in enumerate(path):
        db = GribIndex._find_db_in_cache(path_i)
        assert db is not None, f"db is None for path={path_i}"

        st = os.stat(db.path)
        assert st.st_size == db_size[i], f"db size={st.st_size} for path={path_i}, expected={db_size[i]}"
        assert st.st_mtime == db_modified[i], f"db modified={st.st_mtime} for path={path_i}, expected={db_modified[i]}"

        assert db.path == db_paths[i], f"db.path={db.path} for path={path_i}, expected={db_paths[i]}"
        assert db.count() == counts[i], f"db.count()={db.count()} for path={path_i}, expected={counts[i]}"

    assert fl.get("parameter.variable") == ["t"] * 6 + ["u"] * 6 + ["v"] * 6


# @pytest.mark.cache
# def test_indexing_db_directory():
#     _, path = get_tmp_fixture("directory")
#     d = from_source("file", path, grib_index=True)
#     fl = d.to_fieldlist()
