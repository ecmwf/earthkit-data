# (C) Copyright 2022 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.


import os
import stat
from zipfile import ZipFile

from . import get_reader
from .archive import ArchiveReader
from .csv import CSVReader
from .shapefile import ShapefileReader

SHAPEFILE_EXTENSIONS = (".shp", ".shx", ".dbf")


class InfoWrapper:
    def __init__(self, member):
        self.member = member
        self.file_or_directory = True
        # See https://stackoverflow.com/questions/35782941/archiving-symlinks-with-python-zipfile
        if member.create_system == 3:  # Unix
            unix_mode = member.external_attr >> 16
            if unix_mode & 0o100000 == 0:
                # if mode is 0, starts with '?' in zipinfo, set it to 1
                unix_mode = unix_mode | 0o100000
            self.file_or_directory = stat.S_ISDIR(unix_mode) or stat.S_ISREG(unix_mode)

    @property
    def name(self):
        return self.member.filename

    def isdir(self):
        return self.file_or_directory and self.member.filename.endswith("/")

    def isfile(self):
        return self.file_or_directory and not self.isdir()


class ZIPReader(ArchiveReader):
    def __init__(self, source):
        super().__init__(source)

        self._mutate = None
        self.source = source

        with ZipFile(source, "r") as zip:
            members = zip.infolist()

            if len(members) == 1:

                _, ext = os.path.splitext(members[0].filename)
                if ext in (".csv",):
                    self._mutate = CSVReader(source, compression="zip")
                    return  # Pandas can read zipped files directly

            if ".zattrs" in members:
                return  # Zarr can read zipped files directly

            if any(
                [
                    os.path.splitext(member.filename)[-1] in SHAPEFILE_EXTENSIONS
                    for member in members
                ]
            ):
                self._mutate = ShapefileReader(source)
                return  # GeoPandas can read zipped files directly

            # Extract contents to directory, and update source
            self.expand(zip, members)
            # Mutate to directory source
            self._mutate = get_reader(self.source).mutate()

    def check(self, member):
        return super().check(InfoWrapper(member))

    def mutate(self):

        if self._mutate:
            return self._mutate

        return super().mutate()


EXTENSIONS_TO_SKIP = (".npz",)  # Numpy arrays


def reader(path, magic=None, deeper_check=False):
    if magic is None:  # Bypass check and force
        return ZIPReader(path)

    _, extension = os.path.splitext(path)

    if magic[:4] == b"PK\x03\x04" and extension not in EXTENSIONS_TO_SKIP:
        return ZIPReader(path)
