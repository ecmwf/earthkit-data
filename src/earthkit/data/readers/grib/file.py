# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.utils.decorators import thread_safe_cached_property

from earthkit.data.indexing.simple import SimpleFieldListBase
from earthkit.data.sources import Source
from earthkit.data.utils.parts import Part

from .. import Reader
from .core import GRIBReaderBase
from .scan import GribCodesMessagePositionIndex


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
            from earthkit.data.sources import from_source_internal

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
            ds = from_source_internal(
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


class GRIBReader(Source, GRIBReaderBase):
    def __init__(self, source, path, parts=None, positions=None):
        self._ori_source = source
        self._kwargs = {"parts": parts, "positions": positions}

        for k in [
            "grib_handle_policy",
            "grib_handle_cache_size",
            "use_grib_metadata_cache",
        ]:
            self._kwargs[k] = source._kwargs.get(k, None)

        GRIBReaderBase.__init__(self, source, path)

    def to_fieldlist(self, *args, **kwargs):
        return GribFieldListInFile(self.path, **self._kwargs, **kwargs)

    def to_xarray(self, *args, **kwargs):
        return self.to_fieldlist().to_xarray(*args, **kwargs)

    def to_numpy(self, *args, **kwargs):
        return self.to_fieldlist().to_numpy(*args, **kwargs)

    def to_array(self, *args, **kwargs):
        return self.to_fieldlist().to_array(*args, **kwargs)

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
        return encoder._encode_fieldlist(self.to_xarray(), *args, **kwargs)


class MultiGRIBReader(Source, GRIBReaderBase):
    def __init__(self, sources):
        Reader.__init__(self, self, "")
        self.sources = list(self._flatten(sources))

    def _flatten(self, sources):
        for s in sources:
            if isinstance(s, MultiGRIBReader):
                yield from self._flatten(s.sources)
            else:
                yield s

    def to_fieldlist(self):
        from earthkit.data.mergers import make_merger

        merged = make_merger(None, self.sources).to_fieldlist()
        if merged is not None:
            return merged.mutate()

        raise NotImplementedError("Conversion of MultiGRIBReader to fieldlist is not implemented")

    def to_xarray(self, *args, **kwargs):
        return self.to_fieldlist().to_xarray(*args, **kwargs)

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
