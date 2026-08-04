# (C) Copyright 2025-2026 Anemoi contributors.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
#
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.

import hashlib
import json
import logging
import os
import sqlite3
from collections import defaultdict
from collections.abc import Iterator
from typing import Any

import tqdm

# from anemoi.transform.fields import new_field_from_grid
# from anemoi.transform.flavour import RuleBasedFlavour
# from anemoi.transform.grids import grid_registry
from cachetools import LRUCache

import earthkit.data as ekd

# from earthkit.data.indexing.fieldlist import FieldArray

# from anemoi.datasets.create.arguments import Intervals
# from anemoi.datasets.create.arguments import ValidDates

# from ..source import Source
# from . import source_registry

LOG = logging.getLogger(__name__)

KEYS1 = ("class", "type", "stream", "expver", "levtype")
KEYS2 = ("shortName", "paramId", "level", "step", "number", "date", "time", "valid_datetime", "levelist")

KEYS = KEYS1 + KEYS2


class GribIndex:
    def __init__(
        self,
        database: str,
        *,
        keys: list[str] | str | None = None,
        flavour: str | None = None,
        update: bool = False,
        overwrite: bool = False,
    ) -> None:
        """Initialize the GribIndex object.

        Parameters
        ----------
        database : str
            Path to the SQLite database file.
        keys : Optional[list[str] | str], optional
            list of keys or a string of keys to use for indexing, by default None.
        flavour : Optional[str], optional
            Flavour configuration for mapping fields, by default None.
        update : bool, optional
            Whether to update the database, by default False.
        overwrite : bool, optional
            Whether to overwrite the database if it exists, by default False.
        """
        self.database = database
        if overwrite:
            assert update
            if os.path.exists(database):
                os.remove(database)

        if not update:
            if not os.path.exists(database):
                raise FileNotFoundError(f"Database {database} does not exist")

        if keys is not None:
            if isinstance(keys, str):
                if keys.startswith("+"):
                    keys = set(KEYS) | set(keys[1:].split(","))
                else:
                    keys = set(",".split(keys.split(",")))
                keys = list(keys)

        self.conn = sqlite3.connect(database)
        self.cursor = self.conn.cursor()

        self.flavour = None
        # if flavour is not None:
        #     self.flavour = RuleBasedFlavour(flavour)
        # else:
        #     self.flavour = None

        self.update = update
        self.cache = None
        self.keys = keys
        self._columns = None

        if update:
            if self.keys is None:
                self.keys = KEYS
            LOG.info(f"Using keys: {sorted(self.keys)}")
            self._create_tables()
        else:
            assert keys is None
            self.keys = self._all_columns()
            self.cache = LRUCache(maxsize=50)

        self.warnings = {}
        self.cache = {}

    def _quote_column(self, column: str) -> str:
        """Quote a column name for use in SQL queries."""
        return f'"{column}"'

    def _create_tables(self) -> None:
        """Create the necessary tables in the database."""
        assert self.update

        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS paths (
            id INTEGER PRIMARY KEY,
            path TEXT not null
        )
        """)

        columns = ("valid_datetime",)
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

        self.cursor.execute(f"""
        CREATE UNIQUE INDEX IF NOT EXISTS idx_grib_index_all_keys
        ON grib_index ({", ".join(self._quote_column(col) for col in columns)})
        """)

        for key in columns:
            self.cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_grib_index_{key.replace(":", "_")}
            ON grib_index ({self._quote_column(key)})
            """)

        self._commit()

    def _commit(self) -> None:
        """Commit the current transaction to the database."""
        self.conn.commit()

    def _get_metadata_keys(self) -> list[str]:
        """Retrieve the metadata keys from the database.

        Returns
        -------
        list[str]
            A list of metadata keys stored in the database.
        """
        self.cursor.execute("SELECT key FROM metadata_keys")
        return [row[0] for row in self.cursor.fetchall()]

    def _path_id(self, path: str) -> int:
        """Get the id of a path in the database.

        Parameters
        ----------
        path : str
            The file path to retrieve or insert.

        Returns
        -------
        int
            The ID of the path in the database.
        """
        self.cursor.execute("SELECT id FROM paths WHERE path = ?", (path,))
        row = self.cursor.fetchone()
        if row is None:
            self.cursor.execute("INSERT INTO paths (path) VALUES (?)", (path,))
            self._commit()
            return self.cursor.lastrowid
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
        # if self._columns is not None:
        #     return self._columns

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
        assert self.update

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
        # all_columns = self._all_columns()

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
        path_id = self._path_id(path)
        # print(f"Indexing {path} (path_id={path_id})")

        from earthkit.data.core.field import Field

        from .scan import GribHandleScanner

        # positions = GribCodesMessagePositionIndex(path)

        keys = ["shortName", "paramId", "level", "step", "number", "date", "time", "valid_datetime", "levelist"]

        for i, (handle, offset, length) in enumerate(tqdm.tqdm(GribHandleScanner(path).scan(), leave=False)):
            ctx = {}
            Field._get_grib_indexer_context(handle, ctx)
            keys = ctx

            # print(f"Field {i + 1}: {ctx=}", flush=True)

            self._ensure_columns(keys)

            self._add_grib(
                _path_id=path_id,
                _offset=offset,
                _length=length,
                **keys,
            )

        self._commit()
        # return

        # with open(path, "rb") as f:
        #     for i, (offset, length) in enumerate(tqdm.tqdm(positions, leave=False)):
        #         f.seek(offset)
        #         data = f.read(length)
        #         handle = GribCodesHandle.from_message(data)

        #         ctx = {}
        #         from earthkit.data.core.field import Field

        #         Field._get_grib_indexer_context(handle, ctx)
        #         keys = ctx

        #         # print(f"Field {i + 1}: {ctx=}", flush=True)

        #         self._ensure_columns(keys)

        #         self._add_grib(
        #             _path_id=path_id,
        #             # _offset=handle.get("offset"),
        #             # _length=handle.get("totalLength"),
        #             _offset=offset,
        #             _length=length,
        #             **keys,
        #         )
        # self._commit()
        # return

        # fields = ekd.from_source("file", path).to_fieldlist()
        # if self.flavour is not None:
        #     fields = self.flavour.map(fields)

        # from earthkit.data.field.grib.context import GribIndexerContext

        # for i, field in enumerate(tqdm.tqdm(fields, leave=False)):
        #     ctx = GribIndexerContext()
        #     field._get_grib_context(ctx)
        #     ctx.pop("handle", None)
        #     # print(f"Field {i + 1}: {ctx=}")

        #     keys = ctx

        #     # keys = field._serialise()

        #     # keys = field.get(collections="metadata.mars", default={}).copy()
        #     # keys.update({k: field.get(f"metadata.{k}", default=None) for k in self.keys})

        #     # keys.setdefault("param", keys.get("shortName", keys.get("paramId")))

        #     # keys = {k: v for k, v in keys.items() if v is not None}

        #     # if keys.get("param") in (0, "unknown"):
        #     #     param = (
        #     #         field.get("metadata.discipline", default=None),
        #     #         field.get("metadata.parameterCategory", default=None),
        #     #         field.get("metadata.parameterNumber", default=None),
        #     #     )
        #     #     if param not in self.warnings:
        #     #         self._unknown(path, field, i, param)
        #     #         self.warnings[param] = True

        #     #     continue

        #     self._ensure_columns(list(keys.keys()))

        #     self._add_grib(
        #         _path_id=path_id,
        #         _offset=field.metadata("offset"),
        #         _length=field.metadata("totalLength"),
        #         **keys,
        #     )

        # self._commit()

    def add_grib_fieldlist(self, fieldlist) -> None:
        """Add a GRIB file to the database.

        Parameters
        ----------
        path : str
            Path to the GRIB file to add.
        """
        path = fieldlist.path
        path_id = self._path_id(path)
        # print(f"Indexing {path} (path_id={path_id})")

        fields = fieldlist
        if self.flavour is not None:
            fields = self.flavour.map(fields)

        from earthkit.data.field.grib.context import GribIndexerContext

        for i, field in enumerate(tqdm.tqdm(fields, leave=False)):
            ctx = GribIndexerContext()
            field._get_grib_context(ctx)
            ctx.pop("handle", None)
            # print(f"Field {i + 1}: {ctx=}")

            keys = ctx

            # keys = field._serialise()

            # keys = field.get(collections="metadata.mars", default={}).copy()
            # keys.update({k: field.get(f"metadata.{k}", default=None) for k in self.keys})

            # keys.setdefault("param", keys.get("shortName", keys.get("paramId")))

            # keys = {k: v for k, v in keys.items() if v is not None}

            # if keys.get("param") in (0, "unknown"):
            #     param = (
            #         field.get("metadata.discipline", default=None),
            #         field.get("metadata.parameterCategory", default=None),
            #         field.get("metadata.parameterNumber", default=None),
            #     )
            #     if param not in self.warnings:
            #         self._unknown(path, field, i, param)
            #         self.warnings[param] = True

            #     continue

            self._ensure_columns(list(keys.keys()))

            self._add_grib(
                _path_id=path_id,
                _offset=field.metadata("offset"),
                _length=field.metadata("totalLength"),
                **keys,
            )

        self._commit()

    def _paramdb(self, category: int, discipline: int) -> dict | None:
        """Fetch parameter information from the parameter database.

        Parameters
        ----------
        category : int
            The parameter category.
        discipline : int
            The parameter discipline.

        Returns
        -------
        Optional[dict]
            The parameter information, or None if unavailable.
        """
        if (category, discipline) in self.cache:
            return self.cache[(category, discipline)]

        try:
            import requests

            r = requests.get(
                f"https://codes.ecmwf.int/parameter-database/api/v1/param?category={category}&discipline={discipline}"
            )
            r.raise_for_status()
            self.cache[(category, discipline)] = r.json()
            return self.cache[(category, discipline)]

        except Exception as e:
            LOG.warning(f"Failed to fetch information from parameter database: {e}")

    def _param_grib2_info(self, paramId: int) -> list[dict]:
        """Fetch GRIB2 parameter information for a given parameter ID.

        Parameters
        ----------
        paramId : int
            The parameter ID.

        Returns
        -------
        list[dict]
            A list of GRIB2 parameter information.
        """
        if ("grib2", paramId) in self.cache:
            return self.cache[("grib2", paramId)]

        try:
            import requests

            r = requests.get(f"https://codes.ecmwf.int/parameter-database/api/v1/param/{paramId}/grib2/")
            r.raise_for_status()
            self.cache[("grib2", paramId)] = r.json()
            return self.cache[("grib2", paramId)]

        except Exception as e:
            LOG.warning(f"Failed to fetch information from parameter database: {e}")
        return []

    def _param_id_info(self, paramId: int) -> dict | None:
        """Fetch detailed information for a given parameter ID.

        Parameters
        ----------
        paramId : int
            The parameter ID.

        Returns
        -------
        Optional[dict]
            The parameter information, or None if unavailable.
        """
        if ("info", paramId) in self.cache:
            return self.cache[("info", paramId)]

        try:
            import requests

            r = requests.get(f"https://codes.ecmwf.int/parameter-database/api/v1/param/{paramId}/")
            r.raise_for_status()
            self.cache[("info", paramId)] = r.json()
            return self.cache[("info", paramId)]

        except Exception as e:
            LOG.warning(f"Failed to fetch information from parameter database: {e}")

        return None

    def _param_id_unit(self, unitId: int) -> dict | None:
        """Fetch unit information for a given unit ID.

        Parameters
        ----------
        unitId : int
            The unit ID.

        Returns
        -------
        Optional[dict]
            The unit information, or None if unavailable.
        """
        if ("unit", unitId) in self.cache:
            return self.cache[("unit", unitId)]

        try:
            import requests

            r = requests.get(f"https://codes.ecmwf.int/parameter-database/api/v1/unit/{unitId}/")
            r.raise_for_status()
            self.cache[("unit", unitId)] = r.json()
            return self.cache[("unit", unitId)]

        except Exception as e:
            LOG.warning(f"Failed to fetch information from parameter database: {e}")

        return None

    def _unknown(self, path: str, field: ekd.Field, i: int, param: tuple) -> None:
        """Log information about unknown parameters.

        Parameters
        ----------
        path : str
            Path to the GRIB file.
        field : ekd.Field
            The GRIB field object.
        i : int
            The index of the field in the file.
        param : tuple
            The parameter tuple (discipline, category, parameterNumber).
        """

        def _(s):
            try:
                return int(s)
            except ValueError:
                return s

        LOG.warning(
            f"Unknown param for message {i + 1} in {path} at offset {int(field.metadata('offset', default=None))}"
        )
        LOG.warning(
            f"shortName/paramId: {field.metadata('shortName', default=None)}/{field.metadata('paramId', default=None)}"
        )
        name = field.metadata("parameterName", default=None)
        units = field.metadata("parameterUnits", default=None)
        LOG.warning(f"Discipline/category/parameter: {param} ({name}, {units})")
        LOG.warning(f"grib_copy -w count={i + 1} {path} tmp.grib")

        info = self._paramdb(discipline=param[0], category=param[1])
        found = set()
        if info is not None:
            for n in tqdm.tqdm(info, desc="Scanning parameter database"):
                for p in self._param_grib2_info(n["id"]):
                    keys = {k["name"]: _(k["value"]) for k in p["keys"]}
                    if keys.get("parameterNumber") == param[2]:
                        found.add(n["id"])

        for n in found:
            info = self._param_id_info(n)
            if "unit_id" in info:
                info["unit_id"] = self._param_id_unit(info["unit_id"])["name"]

            LOG.info("%s", f"Possible match: {n}")
            LOG.info("%s", f"     Name:        {info.get('name')}")
            LOG.info("%s", f"     Short name:  {info.get('shortname')}")
            LOG.info("%s", f"     Units:       {info.get('unit_id')}")
            LOG.info("%s", f"     Description: {info.get('description')}")
            LOG.info("")

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

    def retrieve(self, dates: list[Any], **kwargs: Any) -> Iterator[Any]:
        """Retrieve GRIB data from the database.

        Parameters
        ----------
        dates : list[Any]
            list of dates to retrieve data for.
        **kwargs : Any
            Additional filtering criteria.

        Returns
        -------
        Iterator[Any]
            The GRIB data matching the criteria.
        """
        assert not self.update

        dates = [d.isoformat() for d in dates]

        query = """SELECT _path_id, _offset, _length
                   FROM grib_index WHERE valid_datetime IN ({})""".format(", ".join("?" for _ in dates))
        params = dates

        for k, v in kwargs.items():
            if k not in self._columns:
                LOG.warning(f"Warning : {k} not in database columns, key discarded")
                continue
            if isinstance(v, list):
                query += f" AND {self._quote_column(k)} IN ({', '.join('?' for _ in v)})"
                params.extend([str(_) for _ in v])
            else:
                query += f" AND {self._quote_column(k)} = ?"
                params.append(str(v))

        print("SELECT (query)", query)
        print("SELECT (params)", params)
        self.cursor.execute(query, params)

        fetch = self.cursor.fetchall()

        for path_id, offset, length in fetch:
            if path_id in self.cache:
                file = self.cache[path_id]
            else:
                path = self._get_path(path_id)
                LOG.info(f"Opening {path}")
                self.cache[path_id] = open(path, "rb")
                file = self.cache[path_id]

            file.seek(offset)
            data = file.read(length)
            yield data

    def _dump(self, matcher=lambda x: True):
        # result = []
        with self.conn as db:
            for d in db.execute("SELECT * FROM grib_index"):
                print(d)
                # n = dict(d)
                # # for k in ("args", "owner_data"):
                # #     if n[k] is not None:
                # #         n[k] = json.loads(n[k])
                # if matcher(n):
                #     result.append(n)
        # return result

    def _iterate(self):
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
        import pathlib as p

        if not db_path:
            from earthkit.data.core.caching import auxiliary_cache_file

            db_path = auxiliary_cache_file(
                "grib-index",
                path,
                content="null",
                extension=".sqlite",
            )

        db_path_p = p.Path(db_path)
        if db_path_p.exists() and db_path_p.stat().st_size > 0:
            grib_index = cls(db_path_p, update=False)
        else:
            grib_index = cls(db_path_p, update=True)
            grib_index.add_grib_file(path)
        return grib_index

        # grib_index = cls(db_path, update=True)
        # grib_index.add_grib_file(path)
        # return grib_index
        # from earthkit.data import from_source

        # fieldlist = from_source("file", path).to_fieldlist()
        # return cls.from_fieldlist(fieldlist, db_path=db_path)

    @classmethod
    def from_fieldlist(cls, fieldlist, db_path: str | None = None) -> "GribIndex":
        import pathlib as p

        if not db_path:
            from earthkit.data.core.caching import auxiliary_cache_file

            path = fieldlist.path
            db_path = auxiliary_cache_file(
                "grib-index",
                path,
                content="null",
                extension=".sqlite",
            )

        db_path_p = p.Path(db_path)
        if db_path_p.exists() and db_path_p.stat().st_size > 0:
            grib_index = cls(db_path_p, update=False)
        else:
            grib_index = cls(db_path_p, update=True)
            grib_index.add_grib_fieldlist(fieldlist)

        return grib_index


# @source_registry.register("grib-index")
# class GribIndexSource(Source):
#     """GRIB-index data source."""

#     emoji = "🌧️"

#     def __init__(
#         self,
#         context: Any,
#         indexdb: str,
#         flavour: str | None = None,
#         grid_definition: dict | None = None,
#         **kwargs: Any,
#     ) -> None:
#         """Initialise the GRIB-index source.

#         Parameters
#         ----------
#         context : Any
#             The execution context.
#         indexdb : str
#             Path to the GRIB index database.
#         flavour : str, optional
#             Flavour configuration for mapping fields.
#         grid_definition : dict, optional
#             Grid definition to reproject retrieved fields onto.
#         **kwargs : Any
#             Additional filtering criteria forwarded to ``GribIndex.retrieve``.
#         """
#         super().__init__(context)
#         self.indexdb = indexdb
#         self.flavour = RuleBasedFlavour(flavour) if flavour is not None else None
#         self.grid = grid_registry.from_config(grid_definition) if grid_definition else None
#         self.request = kwargs

#     def execute_valid_dates(self, dates: ValidDates) -> FieldArray:
#         """Retrieve grib-indexed fields for a list of validity times."""
#         full_requests = [(list(dates), self.request)]
#         return self._run_requests(full_requests)

#     def execute_intervals(self, dates: Intervals) -> FieldArray:
#         """Retrieve grib-indexed fields covering accumulation windows.

#         grib-index is valid-time indexed: each interval is resolved to its
#         validity time (``interval.max``) plus a ``step`` equal to the
#         accumulation period length. No basetime is involved — the
#         ``SignedInterval.base`` attribute is ignored here, which is why this
#         path does not go through ``Intervals.adjust_request``.
#         """
#         full_requests = []
#         for interval in dates.intervals:
#             # grib-index is valid-time indexed; intervals must not carry a basetime.
#             assert interval.base is None, (
#                 f"GribIndexSource received an interval with a basetime: {interval!r}. "
#                 "grib-index resolves intervals by valid time only."
#             )
#             self.context.trace(self.emoji, "interval:", interval)
#             request = self.request.copy()
#             request["step"] = int((interval.end - interval.start).total_seconds() / 3600)
#             self.context.trace(self.emoji, "  request =", request)
#             full_requests.append(([interval.max], request))
#         return self._run_requests(full_requests)

#     def _run_requests(self, full_requests: list[tuple[list, dict]]) -> FieldArray:
#         """Factorise, trace, and run a list of ``(valid_dates, request)`` pairs."""
#         index = GribIndex(self.indexdb)

#         full_requests = factorise(full_requests)
#         self.context.trace(self.emoji, f"number of (factorised) requests: {len(full_requests)}")
#         for valid_dates, request in full_requests:
#             self.context.trace(self.emoji, f"  dates: {valid_dates}, request: {request}")

#         result = []
#         for valid_dates, request in full_requests:
#             for grib in index.retrieve(valid_dates, **request):
#                 field = ekd.from_source("memory", grib)[0]
#                 if self.flavour:
#                     field = self.flavour.apply(field)
#                 result.append(field)

#         if self.grid is not None:
#             result = [new_field_from_grid(field, self.grid) for field in result]

#         return FieldArray(result)


def factorise(lst):
    """Factorise a list of (dates, request) tuples by merging dates with identical requests."""
    content = dict()

    d = defaultdict(list)
    for dates, request in lst:
        assert isinstance(request, dict), type(request)
        key = hashlib.md5(json.dumps(request, sort_keys=True).encode()).hexdigest()
        content[key] = request
        d[key] += dates

    res = []
    for key, dates in d.items():
        dates = list(sorted(set(dates)))
        res.append((dates, content[key]))
    return res
