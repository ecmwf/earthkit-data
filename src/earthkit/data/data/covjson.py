# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .source import SourceData


class CovJsonData(SourceData):
    _TYPE_NAME = "Covjson"

    @property
    def available_types(self):
        return [self._XARRAY, self._FIELDLIST]

    def describe(self):
        pass

    def to_xarray(self, **kwargs):
        return self._reader.to_xarray(**kwargs)

    def to_fieldlist(self, **kwargs):
        return self._reader.to_fieldlist(**kwargs)

    def to_geojson(self, **kwargs):
        return self._reader.to_geojson(**kwargs)
