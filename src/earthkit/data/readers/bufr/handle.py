# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import eccodes

from earthkit.data.utils.message import CodesHandle
from earthkit.data.utils.message import CodesReader


class BUFRCodesHandle(CodesHandle):
    PRODUCT_ID = eccodes.CODES_PRODUCT_BUFR

    def __init__(self, handle, path, offset):
        super().__init__(handle, path, offset)
        self._unpacked = False

    def unpack(self):
        """Decode data section"""
        if not self._unpacked:
            eccodes.codes_set(self._handle, "unpack", 1)
            self._unpacked = True

    def pack(self):
        """Encode data section"""
        if self._unpacked:
            eccodes.codes_set(self._handle, "pack", 1)
            self._unpacked = False

    def json_dump(self, path):
        self.unpack()
        with open(path, "w") as f:
            eccodes.codes_dump(self._handle, f, "json")
        self.pack()

    def __iter__(self):
        class _KeyIterator:
            def __init__(self, handle):
                self._iterator = eccodes.codes_bufr_keys_iterator_new(handle)

            def __del__(self):
                try:
                    eccodes.codes_bufr_keys_iterator_delete(self._iterator)
                except Exception:
                    pass

            def __iter__(self):
                return self

            def __next__(self):
                while True:
                    if not eccodes.codes_bufr_keys_iterator_next(self._iterator):
                        raise StopIteration

                    return eccodes.codes_bufr_keys_iterator_get_name(self._iterator)

        return _KeyIterator(self._handle)

    def keys(self, namespace=None):
        """Iterate over all the available keys"""
        return self.__iter__()

    def as_namespace(self, namespace=None):
        return {k: self.get(k, default=None) for k in self.keys(namespace=namespace)}

    def _set(self, key, value):
        if isinstance(value, list):
            return eccodes.codes_set_array(self._handle, key, value)
        else:
            return eccodes.codes_set(self._handle, key, value)


class BUFRCodesReader(CodesReader):
    PRODUCT_ID = eccodes.CODES_PRODUCT_BUFR
    HANDLE_TYPE = BUFRCodesHandle
