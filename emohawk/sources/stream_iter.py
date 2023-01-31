# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

import logging

from emohawk.readers.grib.memory import GribStreamReader

from . import Source

LOG = logging.getLogger(__name__)


class GribStreamIteratorSource(Source):
    def __init__(self, stream):
        self._reader = GribStreamReader(stream)

    def __iter__(self):
        return self._reader


source = GribStreamIteratorSource
