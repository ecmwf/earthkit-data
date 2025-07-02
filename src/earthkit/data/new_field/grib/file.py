# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.readers import Reader
from earthkit.data.utils.parts import Part

from ..fieldlist import SimpleFieldList
from ..new_field import Field
from .handle import GribHandleManager
from .handle import ManagedGribHandle
from .scan import GribCodesMessagePositionIndex


class GribFieldListInFile(SimpleFieldList):
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
        super().__init__(**kwargs)

        from earthkit.data.core.config import CONFIG

        def _get_opt(v, name):
            return v if v is not None else CONFIG.get(name)

        self.handle_manager = GribHandleManager(
            _get_opt(grib_handle_policy, "grib-handle-policy"),
            _get_opt(grib_handle_cache_size, "grib-handle-cache-size"),
        )

        self.use_metadata_cache = _get_opt(use_grib_metadata_cache, "use-grib-metadata-cache")

    @property
    def fields(self):
        if not self._fields:
            r = []
            for n in range(self.number_of_parts()):
                r.append(self._create_field(n))
            self._fields = r
        return self._fields

    def _create_field(self, n):
        part = self.part(n)
        handle = ManagedGribHandle(part.path, part.offset, part.length, self.handle_manager)
        field = Field.from_grib(handle, cache=self.use_metadata_cache)
        return field

    @property
    def _positions(self):
        if self.__positions is None:
            self.__positions = GribCodesMessagePositionIndex(self.path, self._file_parts)
        return self.__positions

    def part(self, n):
        return Part(self.path, self._positions.offsets[n], self._positions.lengths[n])

    def number_of_parts(self):
        return len(self._positions)


def _create_grib_fieldlist(path):
    return GribFieldListInFile(path)


def _create_grib_field(path, offset):
    from earthkit.data.core.new_field.grib.handle import FileGribHandle

    handle = FileGribHandle(path, offset, 0)
    return Field.from_grib(handle)


class GRIBReader(GribFieldListInFile, Reader):
    appendable = True  # GRIB messages can be added to the same file

    def __init__(self, source, path, parts=None, positions=None):
        _kwargs = {}
        for k in [
            # "array_backend",
            # "grib_field_policy",
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

    def __repr__(self):
        return "GRIBReader(%s)" % (self.path,)

    def mutate_source(self):
        # A GRIBReader is a source itself
        return self

    def is_streamable_file(self):
        return True

    # def __getstate__(self):
    #     from earthkit.data.core.config import CONFIG

    #     policy = CONFIG.get("grib-file-serialisation-policy")
    #     r = {"serialisation_policy": policy, "kwargs": self.source._kwargs}

    #     if policy == "path":
    #         r["path"] = self.path
    #         r["positions"] = self._positions
    #     else:
    #         r["messages"] = [f.message() for f in self]

    #     return r

    # def __setstate__(self, state):
    #     policy = state["serialisation_policy"]
    #     if policy == "path":
    #         from earthkit.data import from_source

    #         path = state["path"]
    #         ds = from_source("file", path, **state["kwargs"])
    #         self.__init__(ds.source, path, positions=state["positions"])
    #     elif policy == "memory":
    #         from earthkit.data import from_source
    #         from earthkit.data.core.caching import cache_file

    #         def _create(path, args):
    #             with open(path, "wb") as f:
    #                 for message in state["messages"]:
    #                     f.write(message)

    #         path = cache_file(
    #             "GRIBReader",
    #             _create,
    #             [],
    #         )
    #         ds = from_source("file", path)
    #         self.__init__(ds.source, path)
    #     else:
    #         raise ValueError(f"Unknown serialisation policy {policy}")
