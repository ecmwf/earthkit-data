# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#
import logging

LOG = logging.getLogger(__name__)


def _match_magic(magic, deeper_check):
    if magic is not None and len(magic) > 0:
        type_id = b"GRIB"
        if not deeper_check:
            return len(magic) >= 4 and magic[:4] == type_id
        else:
            return type_id in magic
    return False


def _is_default(magic, content_type):
    return (magic is None or len(magic) == 0) and (content_type is None or len(content_type) == 0)


def is_grib_file(path):
    from earthkit.data.core.settings import SETTINGS

    n_bytes = SETTINGS.get("reader-type-check-bytes")
    magic = None
    with open(path, "rb") as f:
        magic = f.read(n_bytes)

    if _match_magic(magic, False):
        return True
    return _match_magic(magic, True)


def reader(source, path, *, magic=None, deeper_check=False, **kwargs):
    if _match_magic(magic, deeper_check):
        from .file import GRIBReader

        parts = source.parts if hasattr(source, "parts") else None
        return GRIBReader(source, path, parts=parts)


def memory_reader(source, buffer, *, magic=None, deeper_check=False, **kwargs):
    if _match_magic(magic, deeper_check):
        from .memory import GribFieldListInMemory
        from .memory import GribMessageMemoryReader

        return GribFieldListInMemory(source, GribMessageMemoryReader(buffer, **kwargs), **kwargs)


def stream_reader(
    source,
    stream,
    magic=None,
    *,
    deeper_check=False,
    content_type=None,
    memory=False,
    **kwargs,
):
    if _is_default(magic, content_type) or _match_magic(magic, deeper_check):
        from .memory import GribFieldListInMemory
        from .memory import GribStreamReader

        r = GribStreamReader(stream, **kwargs)
        if memory:
            r = GribFieldListInMemory(source, r, **kwargs)
        return r
