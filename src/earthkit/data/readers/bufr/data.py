# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from earthkit.data.core.data import Data


class BUFRData(Data):
    _TYPE_NAME = "BUFR"

    def __init__(self, reader):
        self._reader = reader

    @property
    def available_types(self):
        return ["pandas", "featurelist"]

    def describe(self):
        return f"BUFR data from {self._reader.path}"

    def to_fieldlist(self, *args, **kwargs):
        return self._conversion_not_implemented()

    def to_pandas(self, **kwargs):
        return self._reader.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self._conversion_not_implemented()

    def to_geojson(self, **kwargs):
        return self._conversion_not_implemented()

    def to_geopandas(self, **kwargs):
        return self._conversion_not_implemented()

    def to_featurelist(self, *args, **kwargs):
        return self._reader.to_featurelist(*args, **kwargs)

    def to_numpy(self, *args, **kwargs):
        self._conversion_not_implemented()

    def to_array(self, *args, **kwargs):
        self._conversion_not_implemented()
