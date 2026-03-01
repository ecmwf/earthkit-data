# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os

from earthkit.data.utils.message import CodesMessagePositionIndex


class BufrCodesMessagePositionIndex(CodesMessagePositionIndex):
    MAGIC = b"BUFR"

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

            if end_pos > 0 and offset + length > end_pos:
                return

            if edition in [3, 4]:
                yield offset, length

            offset = os.lseek(fd, offset + length, os.SEEK_SET)
