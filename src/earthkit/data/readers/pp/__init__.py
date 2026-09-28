# (C) Copyright 2025- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def _match_magic(magic):
    if magic is not None:
        # magic check matching that from iris
        # https://github.com/SciTools/iris/blob/239f5b4dc7fbd55bc69e1fb71d5adc7371477cbf/lib/iris/fileformats/__init__.py#L48-L70
        return magic[:4] in (b"\x00\x00\x01\x00", b"\x00\x01\x00\x00")
    return False


def reader(source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    if _match_magic(magic):
        from .reader import PPReader

        return PPReader(source, path, **kwargs)


READER = reader
