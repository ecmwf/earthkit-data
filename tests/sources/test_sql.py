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

import pytest

from earthkit.data import from_source
from earthkit.data.data.sql import SQLData
from earthkit.data.utils.testing import NO_GEOPANDAS, modules_installed

NO_SQLALCHEMY = not modules_installed("sqlalchemy")

pytestmark = pytest.mark.skipif(NO_SQLALCHEMY, reason="sqlalchemy is not installed")

TO_GEOPANDAS = pytest.param("to_geopandas", marks=pytest.mark.skipif(NO_GEOPANDAS, reason="geopandas is not installed"))


@pytest.fixture
def db_path(tmp_path):
    # declared DATETIME/BOOLEAN types and NULLs are where the result could depend on how it is read
    path = os.path.join(tmp_path, "test.db")
    with closing(sqlite3.connect(path)) as conn, conn:
        conn.execute("CREATE TABLE obs (station TEXT, t2m REAL, valid DATETIME, flag BOOLEAN, geom BLOB)")
        conn.executemany(
            "INSERT INTO obs VALUES (?, ?, ?, ?, ?)",
            [
                # geom is WKB for POINT(0 0), POINT(1 1) and POINT(2 2)
                ("a", 280.0, "2026-01-01 00:00:00", 1, bytes.fromhex("010100000000000000000000000000000000000000")),
                ("b", 290.0, "2026-01-02 06:00:00", 0, bytes.fromhex("0101000000000000000000f03f000000000000f03f")),
                ("c", None, None, None, bytes.fromhex("010100000000000000000000400000000000000040")),
            ],
        )
    return path


def test_sql_source_query(db_path):
    ds = from_source("sql", f"sqlite:///{db_path}", "SELECT station, t2m FROM obs WHERE t2m > 285")
    assert isinstance(ds, SQLData)

    df = ds.to_pandas()
    assert list(df.columns) == ["station", "t2m"]
    assert df["station"].tolist() == ["b"]


def test_sql_source_params(db_path):
    ds = from_source("sql", f"sqlite:///{db_path}", "SELECT station FROM obs WHERE t2m > :t")
    assert ds.to_pandas(params={"t": 285})["station"].tolist() == ["b"]


def test_sql_source_same_as_file_reader(db_path):
    import pandas as pd

    from_file = from_source("file", db_path).to_pandas()
    from_sql = from_source("sql", f"sqlite:///{db_path}", "SELECT * FROM obs").to_pandas()
    pd.testing.assert_frame_equal(from_file, from_sql)


@pytest.mark.parametrize("method", ["to_pandas", TO_GEOPANDAS])
def test_sql_source_sql_is_always_a_query(db_path, method):
    # pandas would read a bare table name as a table, with different dtypes than a query
    from pandas.errors import DatabaseError

    ds = from_source("sql", f"sqlite:///{db_path}", "obs")
    with pytest.raises(DatabaseError, match="syntax error"):
        getattr(ds, method)()


@pytest.mark.skipif(NO_GEOPANDAS, reason="geopandas is not installed")
def test_sql_source_geopandas(db_path):
    gdf = from_source("sql", f"sqlite:///{db_path}", "SELECT * FROM obs").to_geopandas(crs="EPSG:4326")
    assert gdf.geometry.name == "geom"
    assert gdf.crs == "EPSG:4326"
    assert gdf.geometry.x.tolist() == [0.0, 1.0, 2.0]


@pytest.mark.parametrize("method", ["to_pandas", "to_geopandas"])
def test_sql_source_chunksize_not_supported(db_path, method):
    ds = from_source("sql", f"sqlite:///{db_path}", "SELECT * FROM obs")
    with pytest.raises(ValueError, match="chunksize"):
        getattr(ds, method)(chunksize=1)


def test_sql_source_hides_password():
    ds = from_source("sql", "postgresql://user:secret@host/db", "SELECT * FROM obs")
    assert ds.path == "postgresql://user:***@host/db"
    assert "secret" not in repr(ds)
    assert "secret" not in ds._repr_html_()
