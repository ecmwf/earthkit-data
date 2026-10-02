# (C) Copyright 2026 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from contextlib import contextmanager

from . import Source


class SQLSource(Source):
    """Read the result of an SQL query from any database supported by SQLAlchemy.

    ⚠️ This source is experimental and may change in future versions without
    warning.

    Parameters
    ----------
    url: str
        SQLAlchemy database URL, e.g. ``"postgresql://user:pass@host/db"`` or ``"sqlite:///path.db"``.
    sql: str
        SQL query. Use ``:name`` placeholders for parameters passed via ``params``.
    """

    def __init__(self, url, sql):
        super().__init__()
        try:
            from sqlalchemy import make_url
        except ImportError:
            raise ImportError("the 'sql' source requires 'sqlalchemy' to be installed")

        self.url = make_url(url)
        self.sql = sql

    @property
    def masked_url(self):
        """str: The url with the password replaced by ``***``."""
        return self.url.render_as_string(hide_password=True)

    @contextmanager
    def _connect(self):
        from sqlalchemy import create_engine

        engine = create_engine(self.url)
        try:
            with engine.connect() as conn:
                yield conn
        finally:
            engine.dispose()

    def to_pandas(self, **kwargs):
        import pandas as pd
        from sqlalchemy import text

        with self._connect() as conn:
            return pd.read_sql_query(text(self.sql), conn, **kwargs)

    def to_geopandas(self, geom_col="geom", **kwargs):
        import geopandas as gpd
        from sqlalchemy import text

        # text() ensures the sql is always run as a query, never looked up as a table name
        with self._connect() as conn:
            return gpd.read_postgis(text(self.sql), conn, geom_col=geom_col, **kwargs)

    def to_data_object(self):
        from earthkit.data.data.sql import SQLData

        return SQLData(self)


source = SQLSource
