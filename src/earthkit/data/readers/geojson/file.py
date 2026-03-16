# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#

from abc import abstractmethod

import numpy as np

from earthkit.data.featurelist.simple import IndexFeatureListBase
from earthkit.utils.decorators import thread_safe_cached_property

from .core import GeoJsonReaderBase


class GeoPandasListBase(IndexFeatureListBase):
    @property
    @abstractmethod
    def _df(self):
        pass

    def _getitem(self, index):
        return self._df.iloc[index]

    def __len__(self):
        return len(self._df)

    # def _get_rows(self, **kwargs):
    #     return [row[1] for row in self.to_pandas(**kwargs).iterrows()]

    def ls(self, **kwargs):
        return self._df

    def head(self, n=5, **kwargs):
        return self._df.head(n, **kwargs)

    def tail(self, n=5, **kwargs):
        return self._df.tail(n, **kwargs)

    def to_pandas(self, **kwargs):
        if not kwargs:
            return self._df
        else:
            return self._to_pandas(**kwargs)

    @abstractmethod
    def _to_pandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas_from_multi_paths([self._path], **kwargs)

    @abstractmethod
    def to_geopandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self.to_pandas(**kwargs).to_xarray()

    def _normalise_key_values(self, **kwargs):
        return kwargs

    def describe(self, *args, **kwargs):
        pass

    def to_data_object(self):
        # TODO: to be decided what to do
        return None


class GeoPandasList(GeoPandasListBase):
    def __init__(self, gdf):
        self._gdf = gdf

    @property
    def _df(self):
        return self._gdf

    def _to_pandas(self, **kwargs):
        # TODO: handle multiple paths
        return self._gdf

    def to_geopandas(self, **kwargs):
        # TODO: handle multiple paths
        return self._gdf


class GeoJsonList(GeoPandasListBase, GeoJsonReaderBase):
    def __init__(self, path):
        GeoJsonReaderBase.__init__(self, self, path)

    @thread_safe_cached_property
    def _df(self):
        return self._to_pandas()

    def _to_pandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas_from_multi_paths([self.path], **kwargs)

    def to_geopandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas(**kwargs)

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
