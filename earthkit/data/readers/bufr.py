# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

# See:
# https://github.com/ecmwf/pdbufr

# import os

import eccodes

from earthkit.data.core import Base
from earthkit.data.utils.dump import make_bufr_html_tree

# from earthkit.data.readers.grib.codes import CodesReader
from earthkit.data.utils.message import (
    CodesHandle,
    CodesReader,
    get_bufr_messages_positions,
)
from earthkit.data.utils.parts import Part

from . import Reader

# import threading


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


# # This does not belong here, should be in the C library
# def get_messages_positions(path):
#     fd = os.open(path, os.O_RDONLY)
#     try:

#         def get(count):
#             buf = os.read(fd, count)
#             assert len(buf) == count
#             return int.from_bytes(
#                 buf,
#                 byteorder="big",
#                 signed=False,
#             )

#         offset = 0
#         while True:
#             code = os.read(fd, 4)
#             if len(code) < 4:
#                 break

#             if code != b"BUFR":
#                 offset = os.lseek(fd, offset + 1, os.SEEK_SET)
#                 continue

#             length = get(3)
#             edition = get(1)

#             if edition in [3, 4]:
#                 yield offset, length
#                 offset = os.lseek(fd, offset + length, os.SEEK_SET)

#     finally:
#         os.close(fd)


class BUFRCodesHandle(CodesHandle):
    # MISSING_VALUE = np.finfo(np.float32).max
    # KEY_TYPES = {"s": str, "l": int, "d": float}

    # def __init__(self, handle, path, offset):
    #     super().__init__(handle)
    #     self.path = path
    #     self.offset = offset
    #     # self.unpack(1)

    def unpack(self):
        """Decode data section"""
        eccodes.codes_set(self._handle, "unpack", 1)

    def pack(self):
        """Encode data section"""
        eccodes.codes_set(self._handle, "pack", 1)

    def json_dump(self, path):
        self.unpack()
        with open(path, "w") as f:
            eccodes.codes_dump(self._handle, f, "json")
        self.pack()

    # def write(self, f):
    #     eccodes.codes_write(self._handle, f)

    # def save(self, path):
    #     with open(path, "wb") as f:
    #         self.write_to(f)
    #         self.path = path
    #         self.offset = 0


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
        r""":class:`CodesHandle`: Gets an object providing access to the low level GRIB message structure."""
        if self._handle is None:
            assert self._offset is not None
            self._handle = BUFRCodesReader.from_cache(self.path).at_offset(self._offset)
        return self._handle

    def dump(self):
        # self._get_positions()

        # handle = self.at_offset(self.offsets[n])
        # handle = self.at_offset(0)
        import json
        import warnings

        from earthkit.data.core.temporary import temp_file

        with temp_file() as filename:
            # self._get_positions()
            # handle = self.at_offset(self.offsets[n])
            self.handle.json_dump(filename)

            # handle = self.at_offset(0)
            # self.handle.unpack()
            # with open(filename, "w") as f:
            #     eccodes.codes_dump(handle, f, "json")

            # eccodes.codes_release(handle)

            with open(filename, "r") as f:
                try:
                    d = json.loads(f.read())
                    return make_bufr_html_tree(d)
                    # print(d)
                    # return d
                except Exception as e:
                    warnings.warn("Failed to parse bufr_dump", e)
                    return None

    # def __getitem__(self, n):
    #     elf.offsets[n], self.lengths[n])


class BUFRInOneFile:
    def __init__(self, path):
        self.path = path
        # self.lock = threading.Lock()
        # self.file = open(self.path, "rb")
        self.offsets = []
        self.lengths = []
        self._get_positions()
        # self.num = None

    # def __del__(self):
    #     try:
    #         self.file.close()
    #     except Exception:
    #         pass

    def __getitem__(self, n):
        if isinstance(n, int):
            part = self.part(n if n >= 0 else len(self) + n)
            return BUFRMessage(part.path, part.offset, part.length)
        else:
            return super().__getitem__(n)

    def _get_positions(self):
        if not self.offsets:
            self.offsets = []
            self.lengths = []

            for offset, length in get_bufr_messages_positions(self.path):
                self.offsets.append(offset)
                self.lengths.append(length)

            # with self.lock:
            #     while True:
            #         pos = self.file.tell()
            #         handle = eccodes.codes_bufr_new_from_file(self.file)
            #         if handle is None:
            #             break
            #         self.offsets.append(pos)
            #         self.lengths.append(self.file.tell() - pos)
            #         eccodes.codes_release(handle)

        # if self.num is None:
        #     self.num = len(self.offsets)

    def __len__(self):
        return self.number_of_parts()
        # num = self.number_of_parts()
        # if num > 0:
        #     self.num = num
        # elif self.num is None:
        #     with self.lock:
        #         self.num = eccodes.codes_count_in_file(self.file)
        # return self.num

    # def dump(self, n):
    #     self._get_positions()

    #     # handle = self.at_offset(self.offsets[n])
    #     # handle = self.at_offset(0)
    #     import json
    #     import warnings

    #     import eccodes

    #     from earthkit.data.core.temporary import temp_file

    #     with temp_file() as filename:
    #         self._get_positions()
    #         handle = self.at_offset(self.offsets[n])
    #         # handle = self.at_offset(0)
    #         eccodes.codes_set(handle, "unpack", 1)
    #         with open(filename, "w") as f:
    #             eccodes.codes_dump(handle, f, "json")

    #         eccodes.codes_release(handle)

    #         with open(filename, "r") as f:
    #             try:
    #                 d = json.loads(f.read())
    #                 # print(d)
    #                 return d
    #             except Exception as e:
    #                 warnings.warn("Failed to parse bufr_dump", e)
    #                 return None

    # def __getitem__(self, n):
    #     elf.offsets[n], self.lengths[n])

    # def at_offset(self, offset):
    #     with self.lock:
    #         print(f"offsets={self.offsets} ")
    #         print(f"path={self.path} offset={offset} file={self.file}")
    #         print(f"tell={self.file.tell()}")
    #         self.file.seek(offset, 0)
    #         print(f"tell={self.file.tell()}")
    #         handle = eccodes.codes_bufr_new_from_file(self.file)

    #         # handle = eccodes.codes_new_from_file(
    #         #     self.file,
    #         #     eccodes.CODES_PRODUCT_BUFR,
    #         # )
    #         print(f"handle={handle}")
    #         assert handle is not None
    #         # return CodesHandle(handle, self.path, offset)
    #         return handle

    def part(self, n):
        return Part(self.path, self.offsets[n], self.lengths[n])

    def number_of_parts(self):
        return len(self.offsets)


class BUFRReader(Reader):
    """Represents a BUFR file"""

    def __init__(self, source, path):
        super().__init__(source, path)
        self._reader = BUFRInOneFile(self.path)

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
        return len(self._reader)

    def __getitem__(self, n):
        return self._reader.__getitem__(n)

    def ls(self, *args, **kwargs):
        from pdbufr.high_level_bufr.bufr import BufrFile

        from earthkit.data.utils.summary import ls

        b = BufrFile(self.path)

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

            for count, msg in enumerate(b):
                with msg:
                    if count_start <= count < count_end:
                        yield ({k: msg[k1] for k, k1 in keys.items()})
                    elif count >= count_end:
                        break

        return ls(_proc, BUFR_LS_KEYS, *args, **kwargs)

    def dump(self, index, **kwargs):
        # import json
        # import subprocess
        # import sys
        # import warnings
        # from earthkit.data.core.temporary import temp_file
        from earthkit.data.utils.dump import make_bufr_html_tree

        d = self._reader.dump(index)
        if d is not None:
            return make_bufr_html_tree(d, **kwargs)

        # with temp_file() as filename:
        #     cmd = f"bufr_dump -js -w count=1 -X 0 {self.path} > {filename}"
        #     try:
        #         ret = subprocess.call(cmd, shell=True)
        #         if ret < 0:
        #             warnings.warn("Failed to generate bufr_dump", file=sys.stderr)
        #             return None
        #     except OSError as e:
        #         warnings.warn("Failed to generate bufr_dump", e, file=sys.stderr)
        #         return None

        #     with open(filename, "r") as f:
        #         try:
        #             d = json.loads(f.read())
        #             return make_bufr_html_tree(d, **kwargs)
        #         except Exception as e:
        #             warnings.warn("Failed to parse bufr_dump", e)
        #             return None


def reader(source, path, magic=None, deeper_check=False):
    if magic is None or magic[:4] == b"BUFR":
        return BUFRReader(source, path)
