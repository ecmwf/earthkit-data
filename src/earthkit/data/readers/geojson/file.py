# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


import numpy as np
from earthkit.utils.decorators import thread_safe_cached_property

from earthkit.data.featurelist.simple import SimpleFeatureListBase


class GeoJsonList(SimpleFeatureListBase):
    def __init__(self, path):
        self._path = path
        print(f"GeoJsonList: {path}")

    @thread_safe_cached_property
    def _features(self):
        return self._get_rows()

    def _get_rows(self, **kwargs):
        return [row[1] for row in self.to_pandas(**kwargs).iterrows()]

    def ls(self, **kwargs):
        return self.to_pandas(**kwargs)

    def head(self, n=5, **kwargs):
        return self.ls(n=n, **kwargs)

    def tail(self, n=5, **kwargs):
        return self.ls(n=-n, **kwargs)

    def to_pandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas_from_multi_paths([self._path], **kwargs)

    def to_geopandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self.to_pandas(**kwargs).to_xarray()

    @classmethod
    def to_pandas_from_multi_paths(cls, paths, **kwargs):
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError("Geojson handling requires 'geopandas' to be installed")

        geo_df = gpd.pd.concat([gpd.read_file(path, **kwargs) for path in paths])

        return geo_df.set_index(np.arange(len(geo_df)))

    def _normalise_key_values(self, **kwargs):
        return kwargs

    def describe(self, *args, **kwargs):
        pass
