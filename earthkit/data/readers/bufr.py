# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os

import eccodes

from earthkit.data.core import Base
from earthkit.data.utils.dump import make_bufr_html_tree
from earthkit.data.utils.message import (
    CodesHandle,
    CodesMessagePositionIndex,
    CodesReader,
)
from earthkit.data.utils.parts import Part

from . import Reader

COLUMNS = ("latitude", "longitude", "data_datetime")

BUFR_LS_KEYS = {
    "edition": "edition",
    "type": "dataCategory",
    "subtype": "dataSubCategory",
    "c": "bufrHeaderCentre",
    "mv": "masterTablesVersionNumber",
    "lv": "localTablesVersionNumber",
    "subsets": "numberOfSubsets",
    "compr": "compressedData",
    "typicalDate": "typicalDate",
    "typicalTime": "typicalTime",
    "ident": "ident",
    "lat": "localLatitude",
    "lon": "localLongitude",
}


class BufrCodesMessagePositionIndex(CodesMessagePositionIndex):
    # This does not belong here, should be in the C library
    def _get_message_positions(self, path):
        fd = os.open(path, os.O_RDONLY)
        try:

            def get(count):
                buf = os.read(fd, count)
                assert len(buf) == count
                return int.from_bytes(
                    buf,
                    byteorder="big",
                    signed=False,
                )

            offset = 0
            while True:
                code = os.read(fd, 4)
                if len(code) < 4:
                    break

                if code != b"BUFR":
                    offset = os.lseek(fd, offset + 1, os.SEEK_SET)
                    continue

                length = get(3)
                edition = get(1)

                if edition in [3, 4]:
                    yield offset, length
                    offset = os.lseek(fd, offset + length, os.SEEK_SET)

        finally:
            os.close(fd)


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


class BUFRCodesReader(CodesReader):
    PRODUCT_ID = eccodes.CODES_PRODUCT_BUFR
    HANDLE_TYPE = BUFRCodesHandle


class BUFRMessage(Base):
    def __init__(self, path, offset, length):
        self.path = path
        self._offset = offset
        self._length = length
        self._handle = None

    @property
    def handle(self):
        r""":class:`CodesHandle`: Gets an object providing access to the low level BUFR message structure."""
        if self._handle is None:
            assert self._offset is not None
            self._handle = BUFRCodesReader.from_cache(self.path).at_offset(self._offset)
        return self._handle

    def __repr__(self):
        return "BUFRMessage(%s,%s,%s,%s)" % (
            self.handle.get("dataCategory", default=None),
            self.handle.get("dataSubCategory", default=None),
            self.handle.get("typicalDate", default=None),
            self.handle.get("typicalTime", default=None),
        )

    def _header(self, key):
        return self.handle.get(key, default=None)

    def dump(self):
        from earthkit.data.core.temporary import temp_file

        with temp_file() as filename:
            self.handle.json_dump(filename)
            with open(filename, "r") as f:
                import json
                import warnings

                try:
                    d = json.loads(f.read())
                    return make_bufr_html_tree(d, self.__repr__)
                except Exception as e:
                    warnings.warn("Failed to parse bufr_dump", e)
                    return None

    def message(self):
        r"""Returns a buffer containing the encoded message.

        Returns
        -------
        bytes
        """
        return self.handle.get_buffer()


class BUFRInOneFile:
    def __init__(self, path):
        self.path = path
        self._positions = BufrCodesMessagePositionIndex(self.path)

    def __getitem__(self, n):
        if isinstance(n, int):
            part = self.part(n if n >= 0 else len(self) + n)
            return BUFRMessage(part.path, part.offset, part.length)
        else:
            return super().__getitem__(n)

    def __len__(self):
        return self.number_of_parts()

    def part(self, n):
        return Part(self.path, self._positions.offsets[n], self._positions.lengths[n])

    def number_of_parts(self):
        return len(self._positions)


class BUFRReader(Reader):
    """Represents a BUFR file"""

    def __init__(self, source, path):
        super().__init__(source, path)
        self._reader = None

    def to_pandas(self, columns=COLUMNS, filters=None, **kwargs):
        """Extracts BUFR data into an pandas DataFranme using :xref:`pdbufr`.

        Parameters
        ----------
        columns: str, sequence[str]
            List of ecCodes BUFR keys to extract for each BUFR message/subset.
            See: :xref:`read_bufr` for details.
        filters: dict
            Defines the conditions when to extract the specified ``columns``. See:
            :xref:`read_bufr` for details.
        **kwargs: dict, optional
            Other keyword arguments:

        Returns
        -------
        Pandas DataFrame

        Examples
        --------
        :ref:`/examples/bufr.ipynb`

        """
        import pdbufr

        filters = {} if filters is None else filters
        return pdbufr.read_bufr(self.path, columns=columns, filters=filters)

    def __len__(self):
        return len(self.reader)

    def __getitem__(self, n):
        return self.reader.__getitem__(n)

    def _header(self, key):
        return self.handle.get(key, default=None)

    def ls(self, *args, **kwargs):
        from earthkit.data.utils.summary import ls

        def _proc(keys, n):
            count_start = 0
            if n is None:
                count_end = len(self)
            elif n > 0:
                count_end = n
            else:
                num = len(self)
                count_start = max(0, num + n)
                count_end = num

            for count, msg in enumerate(self):
                if count_start <= count < count_end:
                    yield ({k: msg._header(k1) for k, k1 in keys.items()})
                elif count >= count_end:
                    break

        return ls(_proc, BUFR_LS_KEYS, *args, **kwargs)

    @property
    def reader(self):
        if self._reader is None:
            self._reader = BUFRInOneFile(self.path)
        return self._reader


def reader(source, path, magic=None, deeper_check=False):
    if magic is None or magic[:4] == b"BUFR":
        return BUFRReader(source, path)
