# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import csv
import io
import logging
import mimetypes
import os
import zipfile

LOG = logging.getLogger(__name__)


def reader(source, path, *, magic=None, deeper_check=False, fwf=False, **kwargs):
    if magic is not None:
        kind, compression = mimetypes.guess_type(path)

        if kind == "text/csv":
            from .reader import CSVReader

            return CSVReader(source, path, compression=compression)


READER = reader
