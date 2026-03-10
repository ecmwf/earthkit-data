# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

# The code is copied from skinnywms, and we should combile later


import numpy as np

from earthkit.data.sources import Source

from .core import GeoJsonReaderBase


class GeojsonReader(Source, GeoJsonReaderBase):
    def __init__(self, source, path):
        self._ori_source = source
        GeoJsonReaderBase.__init__(self, source, path)

    def to_pandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas_from_multi_paths([self.path], **kwargs)

    def to_geopandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self.to_pandas(**kwargs).to_xarray()

    def mutate_source(self):
        # A Geojson is a source itself
        return self

    @classmethod
    def to_pandas_from_multi_paths(cls, paths, **kwargs):
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError("Geojson handling requires 'geopandas' to be installed")

        geo_df = gpd.pd.concat([gpd.read_file(path, **kwargs) for path in paths])

        return geo_df.set_index(np.arange(len(geo_df)))

    def to_data_object(self):
        from earthkit.data.data.geojson import GeoJsonData

        return GeoJsonData(self)

    def _encode_default(self, encoder, *args, **kwargs):
        return None
