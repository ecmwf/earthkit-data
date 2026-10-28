#!/usr/bin/env python3

# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import sqlite3
from contextlib import closing

from earthkit.data import from_source


def make_sqlite(path, tables):
    with closing(sqlite3.connect(path)) as conn, conn:
        for name in tables:
            quoted = name.replace('"', '""')
            conn.execute(f'CREATE TABLE "{quoted}" (x INTEGER)')
            conn.executemany(f'INSERT INTO "{quoted}" VALUES (?)', [(1,), (2,)])
    return path


def test_sql_reader_multiple_tables(tmp_path):
    path = make_sqlite(os.path.join(tmp_path, "test.db"), ["a", "b"])
    ds = from_source("file", path)

    assert ds._TYPE_NAME == "SQL"
    assert ds.is_stream() is False
    assert "pandas" in ds.available_types
    assert "geopandas" in ds.available_types
    assert isinstance(ds.path, str)
