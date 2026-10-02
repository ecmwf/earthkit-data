# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from . import Reader

SQLITE_MAGIC = b"SQLite format 3\x00"

# internal tables of SQLite and GeoPackage files, these never hold user data
INTERNAL_TABLE_PREFIXES = ("sqlite_", "gpkg_", "rtree_")


class SQLReader(Reader):
    def __init__(self, source, path, **kwargs):
        super().__init__(source, path)

    def to_data_object(self, **kwargs):
        from earthkit.data.data.sql import SQLData

        return SQLData(self)

    def to_pandas(self, table=None, **kwargs):
        import sqlite3
        from contextlib import closing

        import pandas as pd

        with closing(sqlite3.connect(self.path)) as conn:
            if table is None:
                names = [
                    name
                    for (name,) in conn.execute("SELECT name FROM sqlite_master WHERE type = 'table' ORDER BY name")
                    if not name.startswith(INTERNAL_TABLE_PREFIXES)
                ]
                if len(names) != 1:
                    raise ValueError(
                        f"Expected exactly one table, found {len(names)}. "
                        f"Please specify table. Available tables: {', '.join(names)}"
                    )
                table = names[0]

            quoted = table.replace('"', '""')
            return pd.read_sql_query(f'SELECT * FROM "{quoted}"', conn, **kwargs)

    def to_geopandas(self, table=None, **kwargs):
        import geopandas as gpd

        return gpd.read_file(self.path, layer=table, **kwargs)

    def _encode_default(self, encoder, *args, **kwargs):
        return None


def reader(source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    if magic is not None and len(magic) >= len(SQLITE_MAGIC) and magic[: len(SQLITE_MAGIC)] == SQLITE_MAGIC:
        return SQLReader(source, path, **kwargs)


READER = reader
