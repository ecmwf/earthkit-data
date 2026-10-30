# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


def reader(source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    # Geopoints files start with "#GEO" and geopointset files with "#GEOPOINTSET", whatever
    # the file name is. Files named ``*.csv`` are still taken by the CSV reader.
    if magic is not None and magic.startswith(b"#GEO"):
        from .reader import GeopointsReader

        return GeopointsReader(source, path, **kwargs)


READER = reader
