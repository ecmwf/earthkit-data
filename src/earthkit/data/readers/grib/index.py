# (C) Copyright 2025-2026 Anemoi contributors.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

"""SQLite index of the metadata of GRIB files.

Schema
------
``meta(key, value)``
    Key/value pairs. Currently only ``schema_version``.
``paths(id, path, size, mtime, extra_keys)``
    One row per indexed GRIB file. ``size`` and ``mtime`` (in nanoseconds) are the
    values of the file when it was scanned; they are used to detect changed files.
    ``extra_keys`` is a JSON list with the extra raw GRIB keys scanned for the file.
``grib_index(_id, _path_id, _offset, _length, <dynamic columns>)``
    One row per GRIB message with a unique index on ``(_path_id, _offset)``. The dynamic
    columns are added on demand and are declared without a type, so that SQLite keeps
    the native type of the stored value. They are:

    - the flat ``"<component>.<key>"`` entries of the field indexer context (e.g.
      ``parameter.variable``, ``time.step``, ``vertical.level``)
    - the raw GRIB keys, stored as ``"metadata.<key>"`` (see :data:`DEFAULT_RAW_KEYS`)

    A db can hold files with different sets of keys (e.g. with and without chemical
    species) and different kinds of values in the same column (e.g. the unique grid id is
    a str for some grids and a list for others), and it can be shared by several
    connections. Therefore:

    - A SQL NULL means that the key is absent for the message. It is not returned by
      :meth:`GribIndex.rows`.
    - ``int``, ``float`` and ``str`` values are stored natively. Any other value (None,
      bool, datetime, date, timedelta, list, tuple, dict, bytes, NaN, ints that do not fit
      in 64 bits) is stored as a BLOB with a kind tag and decoded value by value.
    - The set of columns is never cached: it is read from the db when needed.
"""

import datetime
import json
import logging
import os
import sqlite3
from collections.abc import Iterable, Iterator
from typing import Any

import numpy as np
import tqdm

LOG = logging.getLogger(__name__)

#: Version of the db schema. It is part of the key of the dbs in the earthkit-data cache.
SCHEMA_VERSION = 2

#: Prefix of the columns holding raw GRIB keys.
METADATA_PREFIX = "metadata."

#: Raw GRIB keys stored for each message in addition to the keys of the ``mars`` namespace
#: of the message. The list contains the commonly used MARS and metadata keys, and the raw
#: keys used by the ``grib`` Xarray profile (``metadata.param``, ``metadata.number``,
#: ``metadata.date``, ``metadata.time``, ``metadata.level``, ``metadata.typeOfLevel``).
#: A key not defined in a message is not stored (NULL). Note that, as for the field metadata,
#: ``param`` means the shortName (or the paramId when the shortName is "~").
DEFAULT_RAW_KEYS = (
    "shortName",
    "paramId",
    "param",
    "name",
    "units",
    "typeOfLevel",
    "level",
    "levtype",
    "levelist",
    "date",
    "time",
    "step",
    "stepRange",
    "dataDate",
    "dataTime",
    "number",
    "gridType",
    "edition",
    "centre",
    "class",
    "stream",
    "type",
    "expver",
)

_TAG_SEP = b"\x00"
_INT64_MIN = -(2**63)
_INT64_MAX = 2**63 - 1


def _normalise(value: Any) -> Any:
    """Convert numpy scalars/arrays to the equivalent Python objects."""
    if isinstance(value, np.generic):
        return value.item()
    if isinstance(value, np.ndarray):
        return value.tolist()
    return value


def _json_default(value: Any) -> Any:
    """Called by json for objects it cannot serialise: only numpy objects are accepted."""
    if isinstance(value, (np.generic, np.ndarray)):
        return _normalise(value)
    raise TypeError(f"Object of type {type(value).__name__} is not JSON serialisable")


def _tagged(kind: str, payload: str | bytes = b"") -> bytes:
    if isinstance(payload, str):
        payload = payload.encode("utf-8")
    return kind.encode("ascii") + _TAG_SEP + payload


def _encode_json(kind: str, value: Any) -> bytes:
    try:
        return _tagged(kind, json.dumps(value, default=_json_default))
    except TypeError as e:
        raise ValueError(f"Cannot store value {value!r} in the GRIB index: {e}") from e


def _encode_value(value: Any) -> int | float | str | bytes:
    """Convert a Python value into the value stored in sqlite.

    ``int`` (64 bit), ``float`` (not NaN) and ``str`` are stored as they are. Any other
    value, including None, is stored as a BLOB made of a kind tag, a NUL byte and a payload,
    so that each value can be decoded on its own and a column can hold values of different
    kinds. A SQL NULL is never produced: it means that the key is absent (see :func:`_decode_value`).
    """
    value = _normalise(value)

    if value is None:
        return _tagged("none")
    if isinstance(value, bool):
        return _tagged("bool", "1" if value else "0")
    if isinstance(value, int):
        if _INT64_MIN <= value <= _INT64_MAX:
            return value
        return _tagged("bigint", str(value))
    if isinstance(value, float):
        if value != value:
            return _tagged("float", "nan")
        return value
    if isinstance(value, str):
        return value
    if isinstance(value, bytes):
        return _tagged("bytes", value)
    if isinstance(value, datetime.datetime):
        return _tagged("datetime", value.isoformat())
    if isinstance(value, datetime.date):
        return _tagged("date", value.isoformat())
    if isinstance(value, datetime.timedelta):
        # exact, unlike total_seconds()
        return _tagged("timedelta", str((value.days * 86400 + value.seconds) * 1000000 + value.microseconds))
    if isinstance(value, tuple):
        return _encode_json("tuple", value)
    if isinstance(value, dict):
        return _encode_json("dict", value)
    if isinstance(value, list):
        return _encode_json("list", value)

    raise ValueError(f"Cannot store value {value!r} of type {type(value).__name__} in the GRIB index")


_DECODERS = {
    "none": lambda p: None,
    "bool": lambda p: p == b"1",
    "bigint": lambda p: int(p),
    "float": lambda p: float(p),
    "bytes": lambda p: bytes(p),
    "datetime": lambda p: datetime.datetime.fromisoformat(p.decode("utf-8")),
    "date": lambda p: datetime.date.fromisoformat(p.decode("utf-8")),
    "timedelta": lambda p: datetime.timedelta(microseconds=int(p)),
    "list": lambda p: json.loads(p),
    "tuple": lambda p: tuple(json.loads(p)),
    "dict": lambda p: json.loads(p),
}


def _decode_value(value: Any) -> Any:
    """Decode a stored sqlite value (not NULL) into the Python value that was encoded."""
    if isinstance(value, bytes):
        kind, _, payload = value.partition(_TAG_SEP)
        return _DECODERS[kind.decode("ascii")](payload)
    return value


def _normalise_extra_keys(extra_keys: str | Iterable[str] | None) -> list[str]:
    """Return the sorted unique extra raw GRIB keys (without the "metadata." prefix)."""
    if extra_keys is None:
        return []
    if isinstance(extra_keys, str):
        extra_keys = [extra_keys]

    keys = set()
    for k in extra_keys:
        if k.startswith(METADATA_PREFIX):
            k = k[len(METADATA_PREFIX) :]
        keys.add(k)
    return sorted(keys - set(DEFAULT_RAW_KEYS))


def _normalise_path(path: str | os.PathLike) -> str:
    return os.path.abspath(os.fspath(path))


def _quote(name: str) -> str:
    """Quote a column name for use in SQL."""
    return '"' + name.replace('"', '""') + '"'


class GribIndex:
    """SQLite index of the metadata of GRIB files.

    Use :meth:`open` (or :meth:`find_in_cache`) to get an index; constructing the object
    directly only opens (or creates) the db without scanning anything.

    The object holds an open sqlite connection. Call :meth:`close` or use it as a context
    manager.

    Parameters
    ----------
    path : str or os.PathLike
        Path to the SQLite database file. It is created if it does not exist.
    overwrite : bool, optional
        If True an existing database is removed first.

    Raises
    ------
    ValueError
        When the db exists but was created with an incompatible schema version.
    """

    def __init__(self, path: str | os.PathLike, *, overwrite: bool = False) -> None:
        path = os.fspath(path)
        if overwrite and os.path.exists(path):
            os.remove(path)

        self.path = path

        # autocommit mode: transactions are controlled explicitly
        self.conn = sqlite3.connect(path, timeout=60, isolation_level=None)
        try:
            self._init_schema()
        except BaseException:
            self.conn.close()
            raise

    # ------------------------------------------------------------------ schema

    def _init_schema(self) -> None:
        tables = {r[0] for r in self.conn.execute("SELECT name FROM sqlite_master WHERE type='table'")}

        if not tables:
            self.conn.execute("BEGIN IMMEDIATE")
            try:
                self._create_tables()
                self.conn.execute("COMMIT")
            except BaseException:
                self._rollback()
                raise
            return

        version = None
        if "meta" in tables:
            row = self.conn.execute("SELECT value FROM meta WHERE key='schema_version'").fetchone()
            version = row[0] if row else None

        if version != str(SCHEMA_VERSION):
            self.conn.close()
            raise ValueError(
                f"GRIB index db {self.path} has schema version {version!r}, expected {SCHEMA_VERSION}. "
                "It was probably created by another version of earthkit-data. Remove the file to recreate it."
            )

    def _create_tables(self) -> None:
        # Another process may have created the schema between our check and the lock.
        if self.conn.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name='meta'").fetchone():
            return

        self.conn.execute("CREATE TABLE meta (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
        self.conn.execute("INSERT INTO meta (key, value) VALUES ('schema_version', ?)", (str(SCHEMA_VERSION),))
        self.conn.execute(
            """
            CREATE TABLE paths (
                id INTEGER PRIMARY KEY,
                path TEXT NOT NULL UNIQUE,
                size INTEGER NOT NULL,
                mtime INTEGER NOT NULL,
                extra_keys TEXT NOT NULL
            )
            """
        )
        # The dynamic columns are added later without a declared type so that sqlite
        # keeps the native type (int, float, text) of each value.
        self.conn.execute(
            """
            CREATE TABLE grib_index (
                _id INTEGER PRIMARY KEY,
                _path_id INTEGER NOT NULL REFERENCES paths(id),
                _offset INTEGER NOT NULL,
                _length INTEGER NOT NULL
            )
            """
        )
        self.conn.execute("CREATE UNIQUE INDEX idx_grib_index_path_offset ON grib_index (_path_id, _offset)")

    def _rollback(self) -> None:
        if self.conn.in_transaction:
            self.conn.execute("ROLLBACK")

    def _dynamic_columns(self) -> list[str]:
        """Names of the dynamic columns of ``grib_index`` in creation order.

        They are always read from the db because another connection may have added columns.
        """
        rows = self.conn.execute("PRAGMA table_info(grib_index)").fetchall()
        return [r[1] for r in sorted(rows, key=lambda r: r[0]) if not r[1].startswith("_")]

    # ------------------------------------------------------------------ values

    def _ensure_columns(self, columns: Iterable[str], existing: set[str]) -> None:
        """Add the missing columns. ``existing`` is updated; it must be read in the write transaction."""
        for column in columns:
            if column not in existing:
                self.conn.execute(f"ALTER TABLE grib_index ADD COLUMN {_quote(column)}")
                existing.add(column)

    # ------------------------------------------------------------------ files

    def _file_row(self, path: str):
        return self.conn.execute("SELECT id, size, mtime, extra_keys FROM paths WHERE path = ?", (path,)).fetchone()

    def _is_current(self, path: str, extra_keys: list[str]) -> bool:
        """True when the file is indexed, unchanged and was scanned for all ``extra_keys``."""
        row = self._file_row(path)
        if row is None:
            return False
        st = os.stat(path)
        if row[1] != st.st_size or row[2] != st.st_mtime_ns:
            return False
        return set(extra_keys) <= set(json.loads(row[3]))

    def has_path(self, path: str | os.PathLike) -> bool:
        """Return True if the GRIB file is in the db."""
        return self._file_row(_normalise_path(path)) is not None

    def extra_keys(self, path: str | os.PathLike) -> list[str]:
        """Return the extra raw GRIB keys (without the "metadata." prefix) scanned for a file.

        Together with :data:`DEFAULT_RAW_KEYS` these are the keys for which a NULL
        ``metadata.<key>`` value means that the message does not have the key.

        Raises
        ------
        ValueError
            When ``path`` is not in the db.
        """
        row = self._file_row(_normalise_path(path))
        if row is None:
            raise ValueError(f"Path {path} does not exist in the database")
        return list(json.loads(row[3]))

    def paths(self) -> list[str]:
        """Return the paths of the GRIB files in the db, in the order they were added."""
        return [r[0] for r in self.conn.execute("SELECT path FROM paths ORDER BY id")]

    def add_file(self, path: str | os.PathLike, extra_keys: str | Iterable[str] | None = None) -> bool:
        """Make sure a GRIB file is indexed.

        A file that is not in the db is scanned and added. A file that is in the db with
        the same size and modification time, and was scanned for all of ``extra_keys``,
        is reused: nothing is scanned or written. Otherwise (the file changed or some of
        ``extra_keys`` were not scanned for it) its rows are removed and it is scanned
        again. The rows and the ``paths`` entry of a file are written in one transaction,
        so a failure leaves the db as it was.

        Parameters
        ----------
        path : str or os.PathLike
            The GRIB file.
        extra_keys : str or list of str, optional
            Raw GRIB keys to store in addition to :data:`DEFAULT_RAW_KEYS`, as
            ``metadata.<key>`` columns.

        Returns
        -------
        bool
            True if the file was scanned, False if the existing entry was reused.
        """
        path = _normalise_path(path)
        extra_keys = _normalise_extra_keys(extra_keys)

        if self._is_current(path, extra_keys):
            return False

        self.conn.execute("BEGIN IMMEDIATE")
        try:
            # check again now that we hold the write lock: another process may have done it
            if self._is_current(path, extra_keys):
                self._rollback()
                return False

            old = self._file_row(path)
            if old is not None:
                # also keep the keys scanned before when only some keys are missing
                extra_keys = sorted(set(extra_keys) | set(json.loads(old[3])))
                self.conn.execute("DELETE FROM grib_index WHERE _path_id = ?", (old[0],))
                self.conn.execute("DELETE FROM paths WHERE id = ?", (old[0],))

            st = os.stat(path)
            path_id = self.conn.execute(
                "INSERT INTO paths (path, size, mtime, extra_keys) VALUES (?, ?, ?, ?)",
                (path, st.st_size, st.st_mtime_ns, json.dumps(extra_keys)),
            ).lastrowid

            # We hold the write lock, so the columns cannot change under us until the commit
            existing = set(self._dynamic_columns())
            for offset, length, row in self._scan(path, extra_keys):
                row = {k: _encode_value(v) for k, v in row.items()}
                self._ensure_columns(row, existing)
                columns = ["_path_id", "_offset", "_length", *row]
                self.conn.execute(
                    f"INSERT INTO grib_index ({', '.join(_quote(c) for c in columns)}) "
                    f"VALUES ({', '.join('?' for _ in columns)})",
                    [path_id, offset, length, *row.values()],
                )

            self.conn.execute("COMMIT")
        except BaseException:
            self._rollback()
            raise
        return True

    @staticmethod
    def _raw_keys(handle, extra_keys: list[str]) -> dict[str, Any]:
        """Read the raw GRIB keys of a message with their native types.

        Keys that are missing in the message are left out (they are stored as NULL).
        """
        from earthkit.data.field.grib.metadata import GribMetadata

        # the same key semantics as the metadata of the fields (e.g. for "param")
        metadata = GribMetadata(handle)
        keys = dict.fromkeys([*handle.keys(namespace="mars"), *DEFAULT_RAW_KEYS, *extra_keys])
        r = {}
        for k in keys:
            v = metadata.get(k)
            if v is not None:
                r[METADATA_PREFIX + k] = v
        return r

    def _scan(self, path: str, extra_keys: list[str]) -> Iterator[tuple[int, int, dict[str, Any]]]:
        """Yield ``(offset, length, flat dict)`` for each message of a GRIB file."""
        from earthkit.data.field.grib.context import GribIndexerContext
        from earthkit.data.field.grib.create import create_grib_field

        from .scan import GribHandleScanner

        for handle, offset, length in tqdm.tqdm(GribHandleScanner(path).scan(), leave=False):
            ctx = GribIndexerContext()
            create_grib_field(handle)._get_grib_context(ctx)
            ctx.pop("handle", None)

            row = dict(ctx)
            row.update(self._raw_keys(handle, extra_keys))
            yield offset, length, row

    # ------------------------------------------------------------------ reading

    def count(self, path: str | os.PathLike | None = None) -> int:
        """Return the number of messages in the db, or in one GRIB file if ``path`` is given.

        A ``path`` that is not in the db has 0 messages.
        """
        if path is None:
            return self.conn.execute("SELECT count(*) FROM grib_index").fetchone()[0]

        row = self._file_row(_normalise_path(path))
        if row is None:
            return 0
        return self.conn.execute("SELECT count(*) FROM grib_index WHERE _path_id = ?", (row[0],)).fetchone()[0]

    def rows(self, path: str | os.PathLike) -> Iterator[dict[str, Any]]:
        """Iterate over the decoded rows of a GRIB file ordered by offset.

        Each row is a dict with ``_offset``, ``_length``, the flat ``"<component>.<key>"``
        entries and the ``"metadata.<key>"`` entries. The values have the Python types that
        were stored (a stored None is returned as None). Keys that are absent for the
        message (stored as NULL, e.g. columns that only exist because of other files in the
        db) are not in the dict.

        Raises
        ------
        ValueError
            When ``path`` is not in the db.
        """
        file_row = self._file_row(_normalise_path(path))
        if file_row is None:
            raise ValueError(f"Path {path} does not exist in the database")

        # SELECT * so that the columns added by other connections are always seen
        cursor = self.conn.execute("SELECT * FROM grib_index WHERE _path_id = ? ORDER BY _offset", (file_row[0],))
        names = [d[0] for d in cursor.description]
        skip = {"_id", "_path_id"}
        for values in cursor:
            yield {
                name: (value if name in ("_offset", "_length") else _decode_value(value))
                for name, value in zip(names, values)
                if value is not None and name not in skip
            }

    # ------------------------------------------------------------------ lifecycle

    def close(self) -> None:
        """Close the sqlite connection. It is safe to call it more than once."""
        self.conn.close()

    def __enter__(self) -> "GribIndex":
        return self

    def __exit__(self, *args) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}({self.path!r})"

    # ------------------------------------------------------------------ entry points

    @classmethod
    def open(
        cls,
        path: str | os.PathLike | Iterable[str | os.PathLike],
        db_path: str | os.PathLike | None = None,
        extra_keys: str | Iterable[str] | None = None,
    ) -> "GribIndex":
        """Open a db and make sure the GRIB file(s) are indexed in it.

        For each file see :meth:`add_file`: new files are scanned, unchanged files are
        reused and changed files, or files lacking some of ``extra_keys``, are scanned
        again. The caller must close the returned object.

        Parameters
        ----------
        path : str, os.PathLike or list of them
            The GRIB file(s). The paths are made absolute.
        db_path : str or os.PathLike, optional
            The db file, created if needed. It can hold any number of GRIB files. When None
            the db is in the earthkit-data cache and holds a single GRIB file; see
            :meth:`cache_db_path`.
        extra_keys : str or list of str, optional
            Raw GRIB keys to store in addition to :data:`DEFAULT_RAW_KEYS`.

        Raises
        ------
        ValueError
            When ``db_path`` is None and the cache-policy is not "user" or "temporary", or
            more than one file is given.
        """
        if isinstance(path, (str, os.PathLike)):
            paths = [path]
        else:
            paths = list(path)

        extra_keys = _normalise_extra_keys(extra_keys)

        if db_path is None:
            if len(paths) != 1:
                raise ValueError("Without db_path the index is stored in the cache and can only hold a single file")
            db_path = cls.cache_db_path(paths[0], extra_keys, create=True)

        db = cls(db_path)
        try:
            for p in paths:
                db.add_file(p, extra_keys)
        except BaseException:
            db.close()
            raise
        return db

    @classmethod
    def from_file(
        cls,
        path: str | os.PathLike,
        db_path: str | os.PathLike | None = None,
        extra_keys: str | Iterable[str] | None = None,
    ) -> "GribIndex":
        """Index a single GRIB file. A thin wrapper around :meth:`open`."""
        return cls.open(path, db_path=db_path, extra_keys=extra_keys)

    @classmethod
    def cache_db_path(
        cls,
        path: str | os.PathLike,
        extra_keys: str | Iterable[str] | None = None,
        create: bool = False,
    ) -> str:
        """Return the path of the db in the earthkit-data cache for a GRIB file.

        The path depends on the identity of the file (path, ctime, mtime, size), the sorted
        extra keys and the schema version. It is used both to create and to look up the db.

        Parameters
        ----------
        path : str or os.PathLike
            The GRIB file. It must exist.
        extra_keys : str or list of str, optional
            The extra raw GRIB keys.
        create : bool, optional
            When False (default) nothing is created and the db may not exist. When True an
            empty file is created in (and registered with) the cache if it does not exist.

        Raises
        ------
        ValueError
            When the cache-policy is not managed ("off").
        """
        from earthkit.data.core.caching import auxiliary_cache_file, auxiliary_cache_path

        path = _normalise_path(path)
        kwargs = dict(
            extension=".sqlite",
            extra={"grib-index-schema": SCHEMA_VERSION, "extra_keys": _normalise_extra_keys(extra_keys)},
        )

        db_path = auxiliary_cache_path("grib-index", path, **kwargs)
        if db_path is None:
            raise ValueError(
                "Cannot use the earthkit-data cache for the GRIB index when the cache-policy is 'off'. "
                "Set the cache-policy to 'user' or 'temporary' with "
                "earthkit.data.config.set('cache-policy', 'user'), or provide a db path."
            )

        if create:
            created = auxiliary_cache_file("grib-index", path, **kwargs)
            assert created == db_path, (created, db_path)

        return db_path

    @classmethod
    def find_in_cache(
        cls,
        path: str | os.PathLike,
        extra_keys: str | Iterable[str] | None = None,
    ) -> "GribIndex | None":
        """Find the up-to-date db of a GRIB file in the earthkit-data cache.

        Nothing is created or written. The caller must close the returned object.

        Returns
        -------
        GribIndex or None
            None if there is no db for the file, or it does not hold an up-to-date index of
            the file with all ``extra_keys``.

        Raises
        ------
        ValueError
            When the cache-policy is not managed ("off").
        """
        extra_keys = _normalise_extra_keys(extra_keys)
        db_path = cls.cache_db_path(path, extra_keys)
        if not os.path.isfile(db_path) or os.path.getsize(db_path) == 0:
            return None

        db = cls(db_path)
        try:
            if db._is_current(_normalise_path(path), extra_keys):
                return db
        except BaseException:
            db.close()
            raise
        db.close()
        return None
