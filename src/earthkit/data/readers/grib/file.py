# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os
import warnings

from earthkit.utils.decorators import thread_safe_cached_property

from earthkit.data.indexing.simple import SimpleFieldListBase
from earthkit.data.readers.grib.index import DEFAULT_RAW_KEYS, METADATA_PREFIX, GribIndex
from earthkit.data.sources import Source
from earthkit.data.utils.parts import Part

from .core import GRIBReaderBase
from .scan import GribCodesMessagePositionIndex


def first_field_from_grib_file(path, parts=None):
    offset = GribCodesMessagePositionIndex(path, parts=parts, max_count=1).offsets[0]
    if offset < 0 or offset is None:
        return None
    from .memory import GribStreamReader

    with open(path, "rb") as f:
        if parts:
            f.seek(offset)
        reader = GribStreamReader(f)
        return next(reader, None)


class GribFieldListInFile(SimpleFieldListBase, GRIBReaderBase):
    handle_cache = None

    def __init__(
        self,
        path,
        parts=None,
        positions=None,
        grib_handle_policy=None,
        grib_handle_cache_size=None,
        use_grib_metadata_cache=None,
    ):
        assert isinstance(path, str), path
        GRIBReaderBase.__init__(self, self, path)
        # self.path = path
        self._file_parts = parts
        self.__positions = positions

        from earthkit.data.core.config import CONFIG

        def _get_opt(v, name):
            return v if v is not None else CONFIG.get(name)

        self.handle_policy = _get_opt(grib_handle_policy, "grib-handle-policy")
        self.handle_cache_size = _get_opt(grib_handle_cache_size, "grib-handle-cache-size")
        self.use_metadata_cache = _get_opt(use_grib_metadata_cache, "use-grib-metadata-cache")

    @thread_safe_cached_property
    def _fields(self):
        handle_cache = None
        if self.handle_policy == "cache":
            from .handle import GribHandleCache

            handle_cache = GribHandleCache(cache_size=self.handle_cache_size)

        return [self._create_field(i, handle_cache) for i in range(self.number_of_parts())]

    def _create_field(self, n, handle_cache):
        from earthkit.data.field.grib.create import create_grib_field

        from .handle import FileGribHandle

        part = self.part(n)
        handle = FileGribHandle.from_part(part, self.handle_policy, handle_cache)
        field = create_grib_field(handle, cache=self.use_metadata_cache)
        return field

    @property
    def _positions(self):
        # TODO: thread safety
        if self.__positions is None:
            self.__positions = GribCodesMessagePositionIndex(self.path, self._file_parts)
        return self.__positions

    def part(self, n):
        pos = self._positions
        return Part(self.path, pos.offsets[n], pos.lengths[n])

    def number_of_parts(self):
        return len(self._positions)

    def __getstate__(self):
        from earthkit.data.core.config import CONFIG

        policy = CONFIG.get("grib-file-serialisation-policy")
        # state = {"serialisation_policy": policy, "kwargs": self._source_kwargs}
        state = {"serialisation_policy": policy}

        state["handle_policy"] = self.handle_policy
        state["handle_cache_size"] = self.handle_cache_size
        state["use_metadata_cache"] = self.use_metadata_cache

        if policy == "path":
            state["path"] = self.path
            state["positions"] = self._positions
            # state["handle_policy"] = self.handle_policy
            # state["handle_cache_size"] = self.handle_cache_size
            # state["use_metadata_cache"] = self.use_metadata_cache
        elif policy == "memory":
            state["messages"] = [f.message() for f in self]
        else:
            raise ValueError(f"Policy {policy} not supported for GribFieldListInFile")

        return state

    def __setstate__(self, state):
        policy = state["serialisation_policy"]

        if policy == "path":
            path = state["path"]
            positions = state["positions"]
            handle_policy = state["handle_policy"]
            handle_cache_size = state["handle_cache_size"]
            use_metadata_cache = state["use_metadata_cache"]
            self.__init__(
                path,
                positions=positions,
                grib_handle_policy=handle_policy,
                grib_handle_cache_size=handle_cache_size,
                use_grib_metadata_cache=use_metadata_cache,
            )
        elif policy == "memory":
            from earthkit.data.core.caching import cache_file
            from earthkit.data.sources import _from_source_internal

            def _create(path, args):
                with open(path, "wb") as f:
                    for message in state["messages"]:
                        f.write(message)

            path = cache_file(
                "GRIBReader",
                _create,
                [],
            )
            handle_policy = state["handle_policy"]
            handle_cache_size = state["handle_cache_size"]
            use_metadata_cache = state["use_metadata_cache"]
            ds = _from_source_internal(
                "file",
                path,
                grib_handle_policy=handle_policy,
                grib_handle_cache_size=handle_cache_size,
                use_grib_metadata_cache=use_metadata_cache,
            )
            self.__init__(ds.path)
        else:
            raise ValueError(f"Unknown serialisation policy {policy}")

    def _diag(self):
        """For diagnostics purposes, returns a dict with information about the handle and metadata cache."""
        from collections import defaultdict

        r = defaultdict(int)
        r["grib_handle_policy"] = self.handle_policy

        handle = self._fields[0]._get_grib().handle
        if hasattr(handle, "manager"):
            manager = handle.manager
            if manager is not None:
                r.update(manager._diag())

        if self.use_metadata_cache:
            from earthkit.data.utils.diag import metadata_cache_diag

            r.update(metadata_cache_diag(self._fields))
        return r


class IndexedGribFieldListInFile(SimpleFieldListBase, GRIBReaderBase):
    """GRIB fieldlist built from the sqlite index of a GRIB file.

    The fields are built from the rows of the index (see
    :class:`~earthkit.data.readers.grib.index.GribIndex`). No ecCodes handle is created
    until the values or a raw GRIB key that is not stored in the index is needed.

    Parameters
    ----------
    path : str
        The GRIB file. It must be indexed in the db.
    db_path : str or os.PathLike
        The index db. It is only opened (and closed) when the rows are read.
    """

    handle_cache = None

    def __init__(
        self,
        path,
        db_path,
        grib_handle_policy=None,
        grib_handle_cache_size=None,
        use_grib_metadata_cache=None,
    ):
        assert isinstance(path, str), path
        GRIBReaderBase.__init__(self, self, path)

        db_path = os.path.abspath(os.fspath(db_path))
        if not os.path.isfile(db_path):
            raise FileNotFoundError(f"GRIB index db {db_path} does not exist")
        self._db_path = db_path

        from earthkit.data.core.config import CONFIG

        def _get_opt(v, name):
            return v if v is not None else CONFIG.get(name)

        self.handle_policy = _get_opt(grib_handle_policy, "grib-handle-policy")
        self.handle_cache_size = _get_opt(grib_handle_cache_size, "grib-handle-cache-size")
        self.use_metadata_cache = _get_opt(use_grib_metadata_cache, "use-grib-metadata-cache")

    @thread_safe_cached_property
    def _index_rows(self):
        """The decoded rows of the file and the extra raw keys scanned for it.

        The db is closed before returning.
        """
        with GribIndex(self._db_path) as db:
            rows = list(db.rows(self.path))
            extra_keys = db.extra_keys(self.path)
        return rows, extra_keys

    @thread_safe_cached_property
    def _fields(self):
        handle_cache = None
        if self.handle_policy == "cache":
            from .handle import GribHandleCache

            handle_cache = GribHandleCache(cache_size=self.handle_cache_size)

        rows, extra_keys = self._index_rows
        known_keys = {*DEFAULT_RAW_KEYS, *extra_keys}
        return [self._create_field(row, known_keys, handle_cache) for row in rows]

    def _create_field(self, row, known_keys, handle_cache):
        from earthkit.data.core.field import Field
        from earthkit.data.field.grib.data import GribData
        from earthkit.data.field.grib.metadata import IndexedGribMetadata

        from .handle import FileGribHandle

        part = Part(self.path, row["_offset"], row["_length"])
        handle = FileGribHandle.from_part(part, self.handle_policy, handle_cache)

        d = {}
        raw = {}
        for k, v in row.items():
            if k.startswith(METADATA_PREFIX):
                raw[k[len(METADATA_PREFIX) :]] = v
            elif not k.startswith("_"):
                d[k] = v

        # the handle is lazy: it is only created when the values or a key that is not
        # in the index are needed
        field = Field._from_flat_dict(d, handle=handle, data=GribData(handle))
        field._set_private_data("metadata", IndexedGribMetadata(handle, raw, known_keys, cache=self.use_metadata_cache))
        return field

    @property
    def _positions(self):
        return _IndexedPositions(self._index_rows[0])

    def part(self, n):
        row = self._index_rows[0][n]
        return Part(self.path, row["_offset"], row["_length"])

    def number_of_parts(self):
        return len(self._index_rows[0])

    def __getstate__(self):
        return {
            "path": self.path,
            "db_path": self._db_path,
            "kwargs": {
                "grib_handle_policy": self.handle_policy,
                "grib_handle_cache_size": self.handle_cache_size,
                "use_grib_metadata_cache": self.use_metadata_cache,
            },
        }

    def __setstate__(self, state):
        # the fields are not pickled, they are rebuilt from the db
        self.__init__(state["path"], state["db_path"], **state["kwargs"])

    def _diag(self):
        """For diagnostics purposes, returns a dict with information about the handle and metadata cache."""
        from collections import defaultdict

        r = defaultdict(int)
        r["grib_handle_policy"] = self.handle_policy

        handle = self._fields[0]._get_grib().handle
        if hasattr(handle, "manager"):
            manager = handle.manager
            if manager is not None:
                r.update(manager._diag())

        if self.use_metadata_cache:
            from earthkit.data.utils.diag import metadata_cache_diag

            r.update(metadata_cache_diag(self._fields))
        return r


class _IndexedPositions:
    """The offsets and lengths of the messages of an indexed file."""

    def __init__(self, rows):
        self.offsets = [r["_offset"] for r in rows]
        self.lengths = [r["_length"] for r in rows]

    def __len__(self):
        return len(self.offsets)


def _normalise_index(index):
    """Validate the ``index`` argument of ``to_fieldlist``.

    Returns None (no index), True (db in the cache) or the db path as a str.
    """
    if index is None or index is False:
        return None
    if index is True:
        return True
    if isinstance(index, (str, os.PathLike)):
        path = os.fspath(index)
        if isinstance(path, str):
            return path
    raise TypeError(
        f"Invalid index={index!r}: must be None, a bool, a str or an os.PathLike, not {type(index).__name__}"
    )


class GRIBReader(Source, GRIBReaderBase):
    def __init__(
        self,
        source,
        path,
        parts=None,
        positions=None,
        grib_handle_policy=None,
        grib_handle_cache_size=None,
        use_grib_metadata_cache=None,
        **kwargs,
    ):
        if kwargs:
            names = ", ".join(repr(name) for name in kwargs)
            warnings.warn(
                f"Arguments {names} have no effect for the GRIB reader.",
                UserWarning,
                stacklevel=2,
            )
        self._ori_source = source
        self._kwargs = {
            "parts": parts,
            "positions": positions,
            "grib_handle_policy": grib_handle_policy,
            "grib_handle_cache_size": grib_handle_cache_size,
            "use_grib_metadata_cache": use_grib_metadata_cache,
        }

        GRIBReaderBase.__init__(self, source, path)

    def to_fieldlist(self, *args, index=None, index_extra_keys=None, **kwargs):
        """Convert into a fieldlist.

        Parameters
        ----------
        *args
            Unused.
        index : None, bool, str or os.PathLike, optional
            Controls the use of the sqlite metadata index of the GRIB file. See
            :py:meth:`GribData.to_fieldlist <earthkit.data.data.grib.GribData.to_fieldlist>`.
        index_extra_keys : list of str, optional
            Extra raw GRIB keys to store in the index. Only used when ``index`` is set.
        **kwargs
            Passed to the fieldlist constructor.

        Returns
        -------
        :py:class:`~earthkit.data.core.fieldlist.FieldList`

        Raises
        ------
        TypeError
            When ``index`` has an invalid type.
        ValueError
            When ``index`` is True and the cache-policy is "off", or when an index is
            used together with ``parts``.
        """
        index = _normalise_index(index)

        if index is None:
            return GribFieldListInFile(self.path, **self._kwargs, **kwargs)

        self._check_index_parts()
        db_path = index if isinstance(index, str) else None
        with GribIndex.open(self.path, db_path=db_path, extra_keys=index_extra_keys) as db:
            db_path = db.path
        return self._indexed_fieldlist(db_path, **kwargs)

    def _check_index_parts(self):
        if self._kwargs["parts"] is not None:
            raise ValueError("The GRIB index cannot be used with the 'parts' argument")

    def _indexed_fieldlist(self, db_path, **kwargs):
        """Build the fieldlist of the file from an existing db that already indexes it."""
        kw = {k: v for k, v in self._kwargs.items() if k not in ("parts", "positions")}
        kw.update(kwargs)
        return IndexedGribFieldListInFile(self.path, db_path, **kw)

    def to_xarray(self, *args, **kwargs):
        return self.to_fieldlist().to_xarray(*args, **kwargs)

    def to_numpy(self, *args, **kwargs):
        return self.to_fieldlist().to_numpy(*args, **kwargs)

    def to_array(self, *args, **kwargs):
        return self.to_fieldlist().to_array(*args, **kwargs)

    def to_pandas(self, *args, **kwargs):
        return self.to_fieldlist().to_pandas(*args, **kwargs)

    def peek(self):
        return first_field_from_grib_file(self.path, parts=self._kwargs["parts"])

    def mutate_source(self):
        # A GRIBReader is a source itself
        return self

    # def mutate(self):
    #     return self

    def is_streamable_file(self):
        return True

    def to_data_object(self):
        from earthkit.data.data.grib import GribData

        return GribData(self)

    @classmethod
    def merge(cls, sources):
        assert all(isinstance(s, GRIBReader) for s in sources)
        return MultiGRIBReader(sources)

    def _encode_default(self, encoder, *args, **kwargs):
        return encoder._encode_fieldlist(self.to_fieldlist(), *args, **kwargs)


class MultiGRIBReader(Source, GRIBReaderBase):
    def __init__(self, sources):
        GRIBReader.__init__(self, self, "")
        self.sources = list(self._flatten(sources))

    @property
    def path(self):
        return [s.path for s in self.sources]

    def _flatten(self, sources):
        for s in sources:
            if isinstance(s, MultiGRIBReader):
                yield from self._flatten(s.sources)
            else:
                yield s

    def to_fieldlist(self, *args, index=None, index_extra_keys=None, **kwargs):
        """Convert into a single fieldlist containing the fields of all the files.

        Parameters
        ----------
        *args
            Unused.
        index : None, bool, str or os.PathLike, optional
            Controls the use of the sqlite metadata index. With True each file has its own
            db in the cache. With a path a single db holds all the files. See
            :py:meth:`GribData.to_fieldlist <earthkit.data.data.grib.GribData.to_fieldlist>`.
        index_extra_keys : list of str, optional
            Extra raw GRIB keys to store in the index. Only used when ``index`` is set.
        **kwargs
            Passed to the fieldlist constructors.

        Returns
        -------
        :py:class:`~earthkit.data.core.fieldlist.FieldList`

        Raises
        ------
        TypeError
            When ``index`` has an invalid type.
        ValueError
            When ``index`` is True and the cache-policy is "off", or when an index is
            used together with ``parts``.
        """
        from earthkit.data.mergers import make_merger, merge_by_class

        index = _normalise_index(index)

        if isinstance(index, str):
            # one db for all the files, scanned/checked once
            for s in self.sources:
                s._check_index_parts()
            with GribIndex.open([s.path for s in self.sources], db_path=index, extra_keys=index_extra_keys) as db:
                db_path = db.path
            merged = merge_by_class([s._indexed_fieldlist(db_path, **kwargs) for s in self.sources])
        else:
            if index is not None:
                kwargs["index"] = index
                kwargs["index_extra_keys"] = index_extra_keys
            merged = make_merger(None, self.sources).to_fieldlist(**kwargs)

        if merged is not None:
            return merged.mutate()

        raise NotImplementedError("Conversion of MultiGRIBReader to fieldlist is not implemented")

    def to_xarray(self, *args, **kwargs):
        return self.to_fieldlist().to_xarray(*args, **kwargs)

    def to_pandas(self, *args, **kwargs):
        return self.to_fieldlist().to_pandas(*args, **kwargs)

    def __repr__(self):
        return f"MultiGRIBReader({self.sources})"

    def to_data_object(self):
        from earthkit.data.data.grib import GribData

        return GribData(self)

    @classmethod
    def merge(cls, sources):
        r = []
        for source in sources:
            if isinstance(source, MultiGRIBReader):
                r.extend(source.sources)
            elif isinstance(source, GRIBReader):
                r.append(source)
            elif not source.ignore():
                raise ValueError(f"Cannot merge source of type {type(source)} in MultiGRIBReader.merge")

        if r:
            return MultiGRIBReader(r)

        raise ValueError("No GRIBReader found in sources to merge")

    def _encode(self, encoder, hints=None, **kwargs):
        return self.to_fieldlist()._encode(encoder, **kwargs)

    def _encode_default(self, encoder, **kwargs):
        return self.to_fieldlist()._encode(encoder, **kwargs)
