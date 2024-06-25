# (C) Copyright 2021 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.readers.netcdf import NetCDFFieldListUrlReader
from earthkit.data.readers.netcdf import NetCDFReader
from earthkit.data.sources import Source


class OpenDAP(Source):
    def __init__(self, url):
        self.url = url

    def mutate(self):
        fs = NetCDFFieldListUrlReader(source, self.url)
        if fs.has_fields():
            return fs
        else:
            return NetCDFReader(source, self.path)


source = OpenDAP
