# (C) Copyright 2025- ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.readers.pp import IrisReader
from earthkit.data.sources import Source


class IrisSource(Source):

    def __init__(self, path, **kwargs):
        super().__init__(**kwargs)

        self._reader = IrisReader(self, path, **kwargs)

    def mutate(self):
        source = self._reader.mutate_source()
        if source not in (None, self):
            source._parent = self
            return source

        return self


source = IrisSource
