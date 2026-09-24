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
        type_id = (b"\x89HDF", b"CDF\x01", b"CDF\x02")
        return magic[:4] in type_id
    return False


@matcher(priority=940)
def match_netcdf(source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    if _match_magic(magic, deeper_check):
        from .reader import NetCDFFileReader

        return NetCDFFileReader(source, path, **kwargs)
