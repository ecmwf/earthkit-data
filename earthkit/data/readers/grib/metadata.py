# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.core.metadata import Metadata


class GribMetadata(Metadata):
    __handle_type = None

    def __init__(self, handle):
        if not isinstance(handle, self._handle_type()):
            raise TypeError
        self._handle = handle

    @staticmethod
    def _handle_type():
        """Returns the required handle type. Implemented like this
        to avoid cyclic import
        """
        if GribMetadata.__handle_type is None:
            from earthkit.data.readers.grib.codes import GribCodesHandle

            GribMetadata.__handle_type = GribCodesHandle
        return GribMetadata.__handle_type

    def keys(self):
        self._handle.keys()

    def items(self):
        return self._handle.items()

    def __getitem__(self, key):
        return self.get(key)

    def get(self, key, *args):
        if len(args) == 1:
            return self._handle.get(key, default=args[0])
        elif len(args) == 0:
            return self._handle.get(key)
        else:
            raise ValueError

    def update(self, *args, **kwargs):
        pass
