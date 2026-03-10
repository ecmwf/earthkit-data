# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from .source import SourceData


class GribData(SourceData):
    _TYPE_NAME = "GRIB"

    @property
    def available_types(self):
        return [self._FIELDLIST, self._PANDAS, self._XARRAY, self._NUMPY, self._ARRAY]

    def describe(self):
        return f"GRIB data from {self._reader.path}"

    def to_fieldlist(self, *args, **kwargs):
        return self._reader.to_fieldlist(*args, **kwargs)

    def to_pandas(self, **kwargs):
        return self._reader.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self._reader.to_xarray(**kwargs)

    def to_numpy(self, *args, **kwargs):
        return self._reader.to_numpy(*args, **kwargs)

    def to_array(self, *args, **kwargs):
        return self._reader.to_array(*args, **kwargs)
