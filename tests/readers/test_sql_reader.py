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
from earthkit.data.utils.testing import NO_GEOPANDAS


def make_sqlite(path, tables):
    with closing(sqlite3.connect(path)) as conn, conn:
        for name in tables:
            quoted = name.replace('"', '""')
            conn.execute(f'CREATE TABLE "{quoted}" (x INTEGER)')
            conn.executemany(f'INSERT INTO "{quoted}" VALUES (?)', [(1,), (2,)])
    return path


@pytest.mark.parametrize("name", ["test.sqlite3", "test.sqlite", "test.db", "test"])
def test_sql_reader_detected_by_content(tmp_path, name):
    path = make_sqlite(os.path.join(tmp_path, name), ["obs"])
    ds = from_source("file", path)
    assert isinstance(ds, SQLData)
    assert ds.to_pandas()["x"].tolist() == [1, 2]


def test_sql_reader_multiple_tables(tmp_path):
    path = make_sqlite(os.path.join(tmp_path, "test.db"), ["a", "b"])
    ds = from_source("file", path)

    with pytest.raises(ValueError, match="Available tables: a, b"):
        ds.to_pandas()

    assert ds.to_pandas(table="b")["x"].tolist() == [1, 2]


@pytest.fixture
def gpkg_path(tmp_path):
    import geopandas as gpd
    from shapely.geometry import Point

    path = os.path.join(tmp_path, "test.gpkg")
    gdf = gpd.GeoDataFrame({"t2m": [280.0, 290.0]}, geometry=[Point(0, 0), Point(1, 1)], crs="EPSG:4326")
    gdf.to_file(path, layer="stations")
    return path


@pytest.mark.skipif(NO_GEOPANDAS, reason="geopandas is not installed")
def test_sql_reader_gpkg(gpkg_path):
    ds = from_source("file", gpkg_path)
    assert isinstance(ds, SQLData)

    # the GeoPackage internal tables are ignored
    assert ds.to_pandas()["t2m"].tolist() == [280.0, 290.0]

    gdf = ds.to_geopandas()
    assert gdf.crs == "EPSG:4326"
    assert gdf.geometry.x.tolist() == [0.0, 1.0]
    assert ds.to_geopandas(table="stations")["t2m"].tolist() == [280.0, 290.0]
