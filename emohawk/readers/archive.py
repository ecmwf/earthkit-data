# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import os

from . import Reader, get_reader


class ArchiveReader(Reader):
    def check(self, member):
        if not member.isdir() and not member.isfile():
            return False

        if member.name.startswith("/"):
            return False

        if ".." in member.name:
            return False

        return True

    def mutate(self):
        if os.path.isdir(self.source):
            return get_reader(self.source).mutate()

        return self

    def expand(self, archive, members, **kwargs):
        def unpack(target):
            try:
                os.mkdir(target)
            except FileExistsError:
                pass

            for member in members:
                if not self.check(member):
                    continue
                archive.extract(member=member, path=target, **kwargs)

        target, _ = os.path.splitext(self.source)

        unpack(target)
        self.source = target
