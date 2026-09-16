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
import itertools
import logging
import mimetypes

LOG = logging.getLogger(__name__)


def is_probably_csv(
    path,
    probe_size=8192,
    delimiters=",;\t|",
    minimum_rows=2,
    minimum_columns=2,
    maximum_rows=20,
):
    try:
        with open(path, "r", encoding="utf-8-sig", newline="") as f:
            sample = f.read(probe_size)

        dialect = csv.Sniffer().sniff(sample, delimiters=delimiters)
        rows = list(itertools.islice(csv.reader(io.StringIO(sample), dialect), maximum_rows))

        return (
            len(rows) >= minimum_rows
            and len(rows[0]) >= minimum_columns
            and all(len(row) == len(rows[0]) for row in rows)
        )
    except (OSError, UnicodeDecodeError, csv.Error):
        return False


def reader(source, path, *, magic=None, deeper_check=False, content_type=None, **kwargs):
    if magic is not None:
        kind, compression = mimetypes.guess_type(path)

        if kind == "text/csv" or (deeper_check and is_probably_csv(path)):
            from .reader import CSVReader

            return CSVReader(source, path, compression=compression)


READER = reader
