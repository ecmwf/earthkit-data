# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from . import SimpleData


class ShapeFileData(SimpleData):
    _TYPE_NAME = "Shapefile"

    def __init__(self, reader):
        self._reader = reader

    @property
    def available_types(self):
        return [self._GEOPANDAS, self._PANDAS, self._XARRAY, self._GEOJSON]

    def describe(self):
        return f"GeoJSON data from {self._reader.path}"

    def to_pandas(self, **kwargs):
        return self._reader.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self._reader.to_xarray(**kwargs)

    def to_geopandas(self, **kwargs):
        return self._reader.to_geopandas(**kwargs)

    def to_featurelist(self, *args, **kwargs):
        from earthkit.data.readers.shapefile.file import ShapeFileList

        return ShapeFileList(self._reader.path)
