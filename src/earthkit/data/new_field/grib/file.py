# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from functools import cached_property

from earthkit.data.indexing.simple import SimpleFieldListCore
from earthkit.data.readers import Reader
from earthkit.data.utils.parts import Part

from .scan import GribCodesMessagePositionIndex


class PositionDataBase:
    def __init__(self, path, parts=None, positions=None):
        self.path = path
        self._file_parts = parts
        self.__positions = positions

    @property
    def file_parts(self):
        return self._file_parts

    @property
    def positions(self):
        if self.__positions is None:
            raise ValueError("Positions not set")
        return self.__positions


class GribFieldListInFile(SimpleFieldListCore):
    handle_cache = None

    def __init__(
        self,
        path,
        parts=None,
        positions=None,
        grib_handle_policy=None,
        grib_handle_cache_size=None,
        use_grib_metadata_cache=None,
        **kwargs,
    ):
        assert isinstance(path, str), path
        self.path = path
        self._file_parts = parts
        self.__positions = positions

        from earthkit.data.core.config import CONFIG

        def _get_opt(v, name):
            return v if v is not None else CONFIG.get(name)

        self.handle_policy = _get_opt(grib_handle_policy, "grib-handle-policy")
        self.handle_cache_size = _get_opt(grib_handle_cache_size, "grib-handle-cache-size")
        self.use_metadata_cache = _get_opt(use_grib_metadata_cache, "use-grib-metadata-cache")

    @cached_property
    def _fields(self):
        handle_cache = None
        if self.handle_policy == "cache":
            from .handle import GribHandleCache

            handle_cache = GribHandleCache(cache_size=self.handle_cache_size)

        return [self._create_field(i, handle_cache) for i in range(self.number_of_parts())]

    # def _getitem(self, n):
    #     if isinstance(n, int):
    #         if n < 0:
    #             n += len(self)
    #         if n >= len(self):
    #             raise IndexError(f"Index {n} out of range")

    #         field = self.fields[n]
    #         if field is None:
    #             field = self.handle_manager.create_field(self.part(n))
    #             self.fields[n] = field
    #         return field

    # def _make_field(self):
    #     if True:
    #         # if not self._fields:
    #         r = []
    #         for n in range(self.number_of_parts()):
    #             r.append(self._create_field(n))
    #         return r
    #     # return self._fields

    def _create_field(self, n, handle_cache):
        from earthkit.data.new_field.grib.field import new_grib_field

        from .handle import FileGribHandle

        part = self.part(n)
        handle = FileGribHandle.from_part(part, self.handle_policy, handle_cache)
        field = new_grib_field(handle, cache=self.use_metadata_cache)
        return field

    @property
    def _positions(self):
        # TODO: thread safe?
        if self.__positions is None:
            self.__positions = GribCodesMessagePositionIndex(self.path, self._file_parts)
        return self.__positions

    def part(self, n):
        pos = self._positions
        return Part(self.path, pos.offsets[n], pos.lengths[n])

    def number_of_parts(self):
        return len(self._positions)

    def __getstate__(self):
        print("GribFieldListInFile Getstate")
        from earthkit.data.core.config import CONFIG

        policy = CONFIG.get("grib-file-serialisation-policy")
        state = {"serialisation_policy": policy, "kwargs": self._source_kwargs}

        if policy == "path":
            state["path"] = self.path
            state["positions"] = self._positions
            state["handle_policy"] = self.handle_policy
            state["handle_cache_size"] = self.handle_cache_size
            state["use_metadata_cache"] = self.use_metadata_cache
        else:
            raise ValueError(f"Policy {policy} not supported for GribFieldListInFile")
            # r["messages"] = [f.get_private_data("grib").message() for f in self]

        return state

    def __setstate__(self, state):
        print("GribFieldListInFile Setstate")
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
            raise ValueError(f"Policy {policy} not supported for GribFieldListInFile")
        else:
            raise ValueError(f"Unknown serialisation policy {policy}")


class GRIBReader(GribFieldListInFile, Reader):
    appendable = True  # GRIB messages can be added to the same file

    def __init__(self, source, path, parts=None, positions=None):
        _kwargs = {}
        for k in [
            "grib_handle_policy",
            "grib_handle_cache_size",
            "use_grib_metadata_cache",
        ]:
            _kwargs[k] = source._kwargs.get(k, None)

        for k in source._kwargs:
            if "-" in k:
                raise KeyError(f"Invalid option {k} in GRIBReader. Option names must not contain '-'.")

        Reader.__init__(self, source, path)
        GribFieldListInFile.__init__(self, path, parts=parts, positions=positions, **_kwargs)
        self._source_kwargs = source._kwargs

    def __repr__(self):
        return "GRIBReader(%s)" % (self.path,)

    def mutate_source(self):
        # A GRIBReader is a source itself
        return self

    def is_streamable_file(self):
        return True

    def __getstate__(self):
        print("GribReader Getstate")
        from earthkit.data.core.config import CONFIG

        policy = CONFIG.get("grib-file-serialisation-policy")
        state = {"serialisation_policy": policy, "source_kwargs": self._source_kwargs}

        if policy == "path":
            state["path"] = self.path
            state["positions"] = self._positions
        else:
            state["messages"] = [f.get_private_data("grib").message() for f in self]

        return state

    def __setstate__(self, state):
        print("GribReader Setstate")
        policy = state["serialisation_policy"]

        if policy == "path":
            from earthkit.data import from_source

            path = state["path"]
            ds = from_source("file", path, **state["source_kwargs"])
            self.__init__(ds.source, path, positions=state["positions"])
        elif policy == "memory":
            from earthkit.data import from_source
            from earthkit.data.core.caching import cache_file

            def _create(path, args):
                with open(path, "wb") as f:
                    for message in state["messages"]:
                        f.write(message)

            path = cache_file(
                "GRIBReader",
                _create,
                [],
            )
            ds = from_source("file", path)
            self.__init__(ds.source, path)
        else:
            raise ValueError(f"Unknown serialisation policy {policy}")
