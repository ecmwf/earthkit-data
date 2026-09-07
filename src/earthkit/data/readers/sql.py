import os

from . import Reader


class SQLReader(Reader):
    def __init__(self, source, path, **kwargs):
        super().__init__(source, path)

    def to_data_object(self, **kwargs):
        from earthkit.data.data.sql import SQLData

        return SQLData(self)

    def to_pandas(self, layer=None, **kwargs):
        import sqlite3

        import pandas as pd

        with sqlite3.connect(self.path) as conn:
            if layer is None:
                tables = pd.read_sql_query(
                    """
                    SELECT name
                    FROM sqlite_schema
                    WHERE type = 'table'
                      AND name NOT LIKE 'sqlite_%'
                    ORDER BY name
                    """,
                    conn,
                )

                if len(tables) != 1:
                    names = tables["name"].tolist()
                    raise ValueError(
                        f"Expected exactly one table, found {len(names)}. "
                        f"Please specify table. Available tables: {', '.join(names)}"
                    )
                else:
                    table = tables.iloc[0]["name"]
            else:
                table = layer

            return pd.read_sql_query(
                f'SELECT * FROM "{table}"',
                conn,
                **kwargs,
            )

    def to_geopandas(self, **kwargs):
        import geopandas as gpd

        return gpd.read_file(self.path, **kwargs)

    def _encode_default(self, encoder, *args, **kwargs):
        return None


def reader(source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    _, extension = os.path.splitext(path)
    if extension in (".sqlite3", ".gpkg"):
        return SQLReader(source, path, **kwargs)


READER = reader
