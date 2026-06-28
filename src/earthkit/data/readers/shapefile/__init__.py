# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import os

SHAPE_EXT = ".shp"
MANDATORY = (".shp", ".shx", ".dbf")
NON_MANDATORY = (".sbn", ".sbx", ".shp.xml", ".prj", ".CPG")
DOUBLE_DOT_EXT = tuple([e for e in NON_MANDATORY if e.count(".") == 2])


def reader(source, path, *, magic=None, deeper_check=False, **kwargs):
    root, extension = os.path.splitext(path)
    for e in DOUBLE_DOT_EXT:
        if path.endswith(e):
            root = path[: -len(e)]
            extension = e

    path = root + ".shp"

    # a shapefile consists of multiple files, but we only create
    # a reader for the .shp file
    if extension == SHAPE_EXT:
        if all(os.path.exists(root + e) for e in MANDATORY):
            from .reader import ShapeFileReader

            return ShapeFileReader(source, path)
    else:
        if extension in MANDATORY or extension in NON_MANDATORY:
            from ..unknown import UnknownReader

            return UnknownReader(source, "", skip_warning=True)


READER = reader
