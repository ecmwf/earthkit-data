# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from . import SimpleData


class BUFRData(SimpleData):
    _TYPE_NAME = "BUFR"

    def __init__(self, reader):
        self._reader = reader

    @property
    def available_types(self):
        return [self._PANDAS, self._FEATURELIST]

    def describe(self):
        return f"BUFR data from {self._reader.path}"

    def to_pandas(self, **kwargs):
        return self._reader.to_pandas(**kwargs)

    def to_featurelist(self, *args, **kwargs):
        return self._reader.to_featurelist(*args, **kwargs)
