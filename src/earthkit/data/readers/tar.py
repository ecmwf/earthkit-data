# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging
import tarfile

from .archive import ArchiveReader

LOG = logging.getLogger(__name__)


class TarReader(ArchiveReader):
    def __init__(self, source, path, **kwargs):
        super().__init__(source, path, **kwargs)

        with tarfile.open(path) as tar:
            self.expand(
                tar,
                tar.getmembers(),
                set_attrs=False,
            )


def reader(source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    if tarfile.is_tarfile(path):
        return TarReader(source, path, **kwargs)


READER = reader
