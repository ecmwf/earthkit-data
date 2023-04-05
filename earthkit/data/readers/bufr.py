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


class BUFRReader(Reader):
    def __init__(self, source, path):
        super().__init__(source, path)
        self._num = None

    def to_pandas(self, columns=COLUMNS, filters=None, **kwargs):
        import pdbufr

        return pdbufr.read_bufr(self.path, columns=columns, filters=filters)

    def __len__(self):
        if self._num is None:
            import eccodes

            with open(self.path, "rb") as f:
                self._num = eccodes.codes_count_in_file(f)
        return self._num

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


def reader(source, path, magic=None, deeper_check=False):
    if magic is None or magic[:4] == b"BUFR":
        return BUFRReader(source, path)
