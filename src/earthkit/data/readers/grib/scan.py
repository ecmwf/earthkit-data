# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import os

from earthkit.data.utils.message import CodesMessagePositionIndex

LOG = logging.getLogger(__name__)


class GribCodesMessagePositionIndex(CodesMessagePositionIndex):
    MAGIC = b"GRIB"

    # This does not belong here, should be in the C library
    def _get_message_positions_part(self, fd, part):
        assert part is not None
        assert len(part) == 2

        offset = part[0]
        end_pos = part[0] + part[1] if part[1] > 0 else -1

        if os.lseek(fd, offset, os.SEEK_SET) != offset:
            return

        while True:
            code = os.read(fd, 4)
            if len(code) < 4:
                break

            if code != self.MAGIC:
                offset = os.lseek(fd, offset + 1, os.SEEK_SET)
                continue

            length = self._get_bytes(fd, 3)
            edition = self._get_bytes(fd, 1)

            if edition == 1:
                if length & 0x800000:
                    sec1len = self._get_bytes(fd, 3)
                    os.lseek(fd, 4, os.SEEK_CUR)
                    flags = self._get_bytes(fd, 1)
                    os.lseek(fd, sec1len - 8, os.SEEK_CUR)

                    if flags & (1 << 7):
                        sec2len = self._get_bytes(fd, 3)
                        os.lseek(fd, sec2len - 3, os.SEEK_CUR)

                    if flags & (1 << 6):
                        sec3len = self._get_bytes(fd, 3)
                        os.lseek(fd, sec3len - 3, os.SEEK_CUR)

                    sec4len = self._get_bytes(fd, 3)

                    if sec4len < 120:
                        length &= 0x7FFFFF
                        length *= 120
                        length -= sec4len
                        length += 4

            if edition == 2:
                length = self._get_bytes(fd, 8)

            if end_pos > 0 and offset + length > end_pos:
                return

            yield offset, length
            offset = os.lseek(fd, offset + length, os.SEEK_SET)
