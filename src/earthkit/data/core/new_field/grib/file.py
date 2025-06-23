# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

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
