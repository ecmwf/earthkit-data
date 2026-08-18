from ..readers.sql import SQLReader
from . import Source


def create_sqlalchemy_engine(backend, kwargs):
    from sqlalchemy import create_engine

    if backend == "sqlite":
        return create_engine(f"sqlite:///{kwargs['path']}")
    else:
        raise NotImplementedError(f"Backend: {backend} is not implemented.")


class SQLSource(Source):

    def __init__(self, backend, backend_kwargs, sql, **kwargs):
        super().__init__(**kwargs)
        sql_engine = create_sqlalchemy_engine(backend, backend_kwargs)
        self._reader = SQLReader(self, sql_engine, sql, **kwargs)

    def mutate(self):
        source = self._reader.mutate_source()
        if source not in (None, self):
            source._parent = self
            return source
        return self


source = SQLSource
