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

from earthkit.data.featurelist.simple import IndexFeatureListBase

from .core import ShapefileReaderBase


class ShapeFileList(IndexFeatureListBase, ShapefileReaderBase):
    def __init__(self, path):
        ShapefileReaderBase.__init__(self, self, path)

    def _getitem(self, index):
        return self._df.iloc[index]

    def __len__(self):
        return len(self._df)

    @thread_safe_cached_property
    def _df(self):
        return self._to_pandas()

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
            return self.to_pandas(**kwargs)

    def _to_pandas(self, **kwargs):
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError("shapefile handling requires 'geopandas' to be installed")

        import numpy as np

        geo_df = gpd.read_file(self.path, **kwargs)
        return geo_df.set_index(np.arange(len(geo_df)))

    def to_geopandas(self, **kwargs):
        # TODO: handle multiple paths
        return self.to_pandas(**kwargs)

    def to_xarray(self, **kwargs):
        return self.to_pandas(**kwargs).to_xarray()

    def to_numpy(self, flatten=False, **kwargs):
        v = self._df.to_numpy(**kwargs)
        if flatten:
            import math

            v = v.reshape(
                math.prod(v.shape),
            )
        return v

    def bounding_box(self):
        from earthkit.data.utils.bbox import BoundingBox

        return BoundingBox.from_geopandas(self._df)

    @classmethod
    def to_pandas_from_multi_paths(cls, paths, **kwargs):
        try:
            import geopandas as gpd
        except ImportError:
            raise ImportError("shapefile handling requires 'geopandas' to be installed")

        geo_df = gpd.pd.concat([gpd.read_file(path, **kwargs) for path in paths])

        return geo_df.set_index(np.arange(len(geo_df)))

    def _normalise_key_values(self, **kwargs):
        return kwargs

    def describe(self, *args, **kwargs):
        pass

    def to_data_object(self):
        from earthkit.data.data.shapefile import ShapeFileData

        return ShapeFileData(self)

    def _encode_default(self, encoder, *args, **kwargs):
        return None

    @classmethod
    def new_mask_index(cls, *args, **kwargs):
        from earthkit.data.featurelist.simple import SimpleFeatureList

        assert len(args) == 2
        fs = args[0]
        indices = list(args[1])
        return SimpleFeatureList([fs[i] for i in indices])
