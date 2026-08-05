# (C) Copyright 2025-2026 Anemoi contributors.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import logging
import os
import pathlib
import sqlite3
from typing import Any

import tqdm

LOG = logging.getLogger(__name__)


class GribIndex:
    def __init__(
        self,
        path: str,
        *,
        overwrite: bool = False,
    ) -> None:
        """Initialize the GribIndex object.

        Parameters
        ----------
        path : str
            Path to the SQLite database file.
        overwrite : bool, optional
            Whether to overwrite the database if it exists, by default False.
        """
        self.path = path
        update = False

        if overwrite:
            assert update
            if os.path.exists(path):
                os.remove(path)

        if not os.path.exists(path) and pathlib.Path(path).stat().st_size == 0:
            LOG.warning(f"Database {path} is empty, overwriting")
            update = True

        self.conn = sqlite3.connect(path)
        self.cursor = self.conn.cursor()

        self._columns = None

        if update:
            self._create_tables()

    def _quote_column(self, column: str) -> str:
        """Quote a column name for use in SQL queries."""
        return f'"{column}"'

    def _create_tables(self) -> None:
        """Create the necessary tables in the database."""
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS paths (
            id INTEGER PRIMARY KEY,
            path TEXT not null
        )
        """)

        # columns = ("valid_datetime",)
        # We don't use NULL as a default because NULL is considered a different value
        # in UNIQUE INDEX constraints (https://www.sqlite.org/lang_createindex.html)

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS grib_index (
            _id INTEGER PRIMARY KEY,
            _path_id INTEGER not null,
            _offset INTEGER not null,
            _length INTEGER not null,
            FOREIGN KEY(_path_id) REFERENCES paths(id))
        """)  # ,

        # {", ".join(f"{self._quote_column(key)} TEXT not null default ''" for key in columns)},

        self.cursor.execute("""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_grib_index_path_offset
        ON grib_index (_path_id, _offset)
        """)

        # self.cursor.execute(f"""
        # CREATE UNIQUE INDEX IF NOT EXISTS idx_grib_index_all_keys
        # ON grib_index ({", ".join(self._quote_column(col) for col in columns)})
        # """)

        # for key in columns:
        #     self.cursor.execute(f"""
        #     CREATE INDEX IF NOT EXISTS idx_grib_index_{key.replace(":", "_")}
        #     ON grib_index ({self._quote_column(key)})
        #     """)

        self._commit()

    def _commit(self) -> None:
        """Commit the current transaction to the database."""
        self.conn.commit()

    # def _get_metadata_keys(self) -> list[str]:
    #     """Retrieve the metadata keys from the database.

    #     Returns
    #     -------
    #     list[str]
    #         A list of metadata keys stored in the database.
    #     """
    #     self.cursor.execute("SELECT key FROM metadata_keys")
    #     return [row[0] for row in self.cursor.fetchall()]

    def has_path(self, path: str) -> bool:
        """Check if a path exists in the database.

        Parameters
        ----------
        path : str
            The file path to check.

        Returns
        -------
        bool
            True if the path exists in the database, False otherwise.
        """
        return self._path_id(path, insert=False) is not None

    def _path_id(self, path: str, insert: bool = True) -> int:
        """Get the id of a path in the database.

        Parameters
        ----------
        path : str
            The file path to retrieve or insert.
        insert : bool, optional
            Whether to insert the path if it does not exist, by default True.

        Returns
        -------
        int
            The ID of the path in the database.
        """
        self.cursor.execute("SELECT id FROM paths WHERE path = ?", (path,))
        row = self.cursor.fetchone()
        if row is None:
            if insert:
                self.cursor.execute("INSERT INTO paths (path) VALUES (?)", (path,))
                self._commit()
                return self.cursor.lastrowid
            else:
                return None
        return row[0]

    def _add_grib(self, **kwargs: Any) -> None:
        """Add a GRIB record to the database.

        Parameters
        ----------
        **kwargs : Any
            Key-value pairs representing the GRIB record fields.
        """
        assert self.update

        # print(f"Adding grib record: {kwargs}")

        try:
            self.cursor.execute(
                f"""
            INSERT INTO grib_index ({", ".join(self._quote_column(k) for k in kwargs.keys())})
            VALUES ({", ".join("?" for _ in kwargs)})
            """,
                tuple(kwargs.values()),
            )

        except sqlite3.IntegrityError:
            LOG.error(f"Error adding grib record: {kwargs}")
            LOG.error("Record already exists")
            LOG.info(f"Path: {self._get_path(kwargs['_path_id'])}")
            for n in ("_path_id", "_offset", "_length"):
                kwargs.pop(n)
            self.cursor.execute(
                "SELECT * FROM grib_index WHERE "
                + " AND ".join(f"{self._quote_column(key)} = ?" for key in kwargs.keys()),
                tuple(kwargs.values()),
            )
            existing_record = self.cursor.fetchone()
            if existing_record:
                LOG.info(f"Existing record found: {existing_record}")
                LOG.info(f"Path: {self._get_path(existing_record[1])}")
            raise

    def _all_columns(self) -> list[str]:
        """Retrieve all column names from the grib_index table.

        Returns
        -------
        list[str]
            A list of column names.
        """
        if self._columns is not None:
            return self._columns

        self.cursor.execute("PRAGMA table_info(grib_index)")
        columns = {row[1] for row in self.cursor.fetchall()}
        self._columns = [col for col in columns if not col.startswith("_")]
        return self._columns

    def _ensure_columns(self, columns: list[str]) -> None:
        """Add missing columns to the grib_index table.

        Parameters
        ----------
        columns : list[str]
            list of column names to ensure in the table.
        """
        existing_columns = self._all_columns()
        new_columns = [column for column in columns if column not in existing_columns]

        if not new_columns:
            return

        self._columns = None

        for column in new_columns:
            self.cursor.execute(
                f"ALTER TABLE grib_index ADD COLUMN {self._quote_column(column)} TEXT not null default ''"
            )

        self.cursor.execute("""DROP INDEX IF EXISTS idx_grib_index_all_keys""")
        self._all_columns()

        # self.cursor.execute(f"""
        # CREATE UNIQUE INDEX IF NOT EXISTS idx_grib_index_all_keys
        # ON grib_index ({', '.join(self._quote_column(col) for col in all_columns)})
        # """)

        # for key in all_columns:
        #     self.cursor.execute(f"""
        #     CREATE INDEX IF NOT EXISTS idx_grib_index_{key.replace(':', '_')}
        #     ON grib_index ({self._quote_column(key)})
        #     """)

    def add_grib_file(self, path: str) -> None:
        """Add a GRIB file to the database.

        Parameters
        ----------
        path : str
            Path to the GRIB file to add.
        """
        path_id = self._path_id(path, insert=False)
        if path_id is None:
            path_id = self._path_id(path, insert=True)
        else:
            raise ValueError(f"Path {path} already exists in the database with path_id {path_id}")

        from earthkit.data.core.field import Field

        from .scan import GribHandleScanner

        for _, (handle, offset, length) in enumerate(tqdm.tqdm(GribHandleScanner(path).scan(), leave=False)):
            ctx = {}
            Field._get_grib_indexer_context(handle, ctx)
            keys = ctx

            self._ensure_columns(keys)

            self._add_grib(
                _path_id=path_id,
                _offset=offset,
                _length=length,
                **keys,
            )

        self._commit()

    def _get_path(self, path_id: int) -> str:
        """Retrieve the path corresponding to a given path_id.

        Parameters
        ----------
        path_id : int
            The ID of the path to retrieve.

        Returns
        -------
        str
            The path corresponding to the given path_id.

        Raises
        ------
        ValueError
            If the path_id does not exist in the database.
        """
        self.cursor.execute("SELECT path FROM paths WHERE id = ?", (path_id,))
        row = self.cursor.fetchone()
        if row is None:
            raise ValueError(f"No path found for path_id {path_id}")
        return row[0]

    # def _dump(self, matcher=lambda x: True):
    #     # result = []
    #     with self.conn as db:
    #         for d in db.execute("SELECT * FROM grib_index"):
    #             print(d)
    #             # n = dict(d)
    #             # # for k in ("args", "owner_data"):
    #             # #     if n[k] is not None:
    #             # #         n[k] = json.loads(n[k])
    #             # if matcher(n):
    #             #     result.append(n)
    #     # return result

    def __iter__(self):
        # with self.cursor as db:
        # print("description", self.cursor.description)
        keys = (
            self._quote_column("_offset")
            + ", "
            + self._quote_column("_length")
            + ", "
            + ", ".join([self._quote_column(c) for c in self._all_columns()])
        )
        for d in self.cursor.execute(f"SELECT {keys} FROM grib_index"):
            # print("d", d)
            # print("description", self.cursor.description)
            # print("type(d)", type(d))
            yield d

    @classmethod
    def from_file(cls, path: str, db_path: str | None = None) -> "GribIndex":
        # the db is stored in the cache
        if not db_path:
            from earthkit.data.core.caching import auxiliary_cache_file

            # this will create an empty file if it does not exist
            db_path = auxiliary_cache_file(
                "grib-index",
                path,
                content="null",
                extension=".sqlite",
            )

        grib_index = None
        if os.path.exists(db_path) and pathlib.Path(db_path).stat().st_size > 0:
            grib_index = cls(db_path)
            if grib_index._path_id(path) is None:
                grib_index.add_grib_file(path)
            return grib_index

        grib_index = cls(db_path, overwrite=True)
        grib_index.add_grib_file(path)

        return grib_index

    @classmethod
    def from_fieldlist(cls, fieldlist, db_path: str | None = None) -> "GribIndex":
        if hasattr(fieldlist, "path"):
            path = fieldlist.path
            return cls.from_file(path, db_path=db_path)
        else:
            if not db_path:
                raise ValueError(
                    (
                        "db_path must be provided when creating GribIndex from fieldlist built from "
                        "multiple files or having no path"
                    )
                )

            grib_index = None
            if os.path.exists(db_path) and pathlib.Path(db_path).stat().st_size > 0:
                grib_index = cls(db_path)
                return grib_index

            else:
                grib_index = cls(db_path, overwrite=True)
                grib_index.add_fieldlist(fieldlist)
                return grib_index

        return None
