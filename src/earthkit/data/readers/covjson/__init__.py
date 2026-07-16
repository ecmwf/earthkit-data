# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import mimetypes
import pathlib


def _match_content_type(content_type):
    return content_type is not None and content_type == "application/prs.coverage+json"


def _match_magic(magic, deeper_check):
    if magic is not None:
        type_id = b'{"type": "CoverageCollection"'
        if not deeper_check:
            return magic.startswith(type_id)
        else:
            return type_id in magic
    return False


def reader(source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    def _reader():
        from .reader import CovjsonReader

        return CovjsonReader(source, path)

    if _match_content_type(content_type) or _match_magic(magic, deeper_check):
        return _reader()

    extension = pathlib.Path(path).suffix
    if extension in [".covjson"]:
        return _reader()

    kind, _ = mimetypes.guess_type(path)
    if kind in ["application/prs.cov+json"]:
        return _reader()


def memory_reader(source, buffer, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    if _match_content_type(content_type) or _match_magic(magic, deeper_check):
        from .reader import CovjsonMemoryReader

        return CovjsonMemoryReader(buffer)


def stream_reader(
    source,
    stream,
    *,
    magic=None,
    deeper_check=False,
    content_type=None,
    # memory=False,
    **kwargs,
):
    if _match_content_type(content_type) or _match_magic(magic, deeper_check):
        # if memory:
        #     from .reader import CovjsonMemoryReader

        #     return CovjsonMemoryReader._from_stream(stream)
        from .reader import CovjsonStreamReader

        return CovjsonStreamReader(stream)


READER = reader
MEMORY_READER = memory_reader
STREAM_READER = stream_reader
