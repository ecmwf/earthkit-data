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

import threading

import eccodes

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


class BUFRInOneFile:
    def __init__(self, path):
        self.path = path
        self.lock = threading.Lock()
        self.file = open(self.path, "rb")
        self.offsets = []
        self.lengths = []
        self.num = None

    def __del__(self):
        try:
            # print("CLOSE", self.path)
            self.file.close()
        except Exception:
            pass

    def _get_positions(self):
        if not self.offsets:
            with self.lock:
                while True:
                    pos = self.file.tell()
                    handle = eccodes.codes_bufr_new_from_file(self.file)
                    if handle is None:
                        break
                    self.offsets.append(pos)
                    self.lengths.append(self.file.tell() - pos)
                    eccodes.codes_release(handle)

        if self.num is None:
            self.num = len(self.offsets)

    def __len__(self):
        if self.num is None:
            with self.lock:
                self.num = eccodes.codes_count_in_file(self.file)
            return self.num

    def dump(self, n):
        # self._get_positions()

        # handle = self.at_offset(self.offsets[n])
        # handle = self.at_offset(0)
        import json
        import warnings

        import eccodes

        from earthkit.data.core.temporary import temp_file

        with temp_file() as filename:
            # self._get_positions()
            # handle = self.at_offset(self.offsets[n])
            handle = self.at_offset(0)
            eccodes.codes_set(handle, "unpack", 1)
            with open(filename, "w") as f:
                eccodes.codes_dump(handle, f, "json")

            eccodes.codes_release(handle)

            with open(filename, "r") as f:
                try:
                    d = json.loads(f.read())
                    # print(d)
                    return d
                except Exception as e:
                    warnings.warn("Failed to parse bufr_dump", e)
                    return None

    # def __getitem__(self, n):
    #     elf.offsets[n], self.lengths[n])

    def at_offset(self, offset):
        with self.lock:
            print(f"offsets={self.offsets} ")
            print(f"path={self.path} offset={offset} file={self.file}")
            print(f"tell={self.file.tell()}")
            self.file.seek(offset, 0)
            print(f"tell={self.file.tell()}")
            handle = eccodes.codes_bufr_new_from_file(self.file)

            # handle = eccodes.codes_new_from_file(
            #     self.file,
            #     eccodes.CODES_PRODUCT_BUFR,
            # )
            print(f"handle={handle}")
            assert handle is not None
            # return CodesHandle(handle, self.path, offset)
            return handle


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
