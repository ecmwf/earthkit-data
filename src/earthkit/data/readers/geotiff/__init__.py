# (C) Copyright 2024 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def _match_magic(magic):
    # https://docs.ogc.org/is/19-008r4/19-008r4.html#_tiff_core_test
    # Bytes 0-1: 'II' (little endian) or 'MM' (big endian)
    # Bytes 2-3: 42 as short in the corresponding byte order
    #           or 43 for a bigtiff file
    # Bytes 4-7: offset to first image file directory
    return magic is not None and len(magic) >= 8 and magic[:4] in {b"II*\x00", b"II+\x00", b"MM\x00*"}


def reader(source, path, *, magic=None, **kwargs):
    if _match_magic(magic):
        from .reader import GeoTIFFReader

        return GeoTIFFReader(source, path)


READER = reader
