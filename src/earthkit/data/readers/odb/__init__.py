# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.readers import matcher


def _match_magic(magic, deeper_check):
    if magic is not None:
        type_id = b"\xff\xffODA"
        if not deeper_check:
            return magic[:5] == type_id
        else:
            return type_id in magic
    return False


@matcher(priority=920)
def match_odb(source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    if _match_magic(magic, deeper_check):
        from .reader import ODBReader

        return ODBReader(source, path, **kwargs)
