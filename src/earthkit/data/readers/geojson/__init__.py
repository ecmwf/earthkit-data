# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import mimetypes


def reader(source, path, *, magic=None, deeper_check=False, **kwargs):
    kind, _ = mimetypes.guess_type(path)
    ext = path.split(".")[-1]

    geojson_extensions = ["geojson"]
    geojson_mimetypes = ["application/geo+json"]
    if ext in geojson_extensions or kind in geojson_mimetypes:
        from .reader import GeojsonReader

        return GeojsonReader(source, path)


READER = reader
