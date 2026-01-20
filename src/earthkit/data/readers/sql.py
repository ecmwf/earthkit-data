from . import Reader


class SQLReader(Reader):

    def __init__(self, source, sql_engine, sql, **kwargs):
        super().__init__(source, sql_engine)
        self._sql_engine = sql_engine
        self._sql = sql

    def mutate_source(self):
        return self

    def to_pandas(self, **kwargs):
        import pandas as pd

        conn = self._sql_engine.connect()
        try:
            df = pd.read_sql(self._sql, conn, **kwargs)
        finally:
            conn.close()

        return df

    def to_xarray(self, **kwargs):

        return self.to_pandas().to_xarray(**kwargs)


def reader(source, path, *, magic=None, deeper_check=False, fwf=False, **kwargs):
    return
