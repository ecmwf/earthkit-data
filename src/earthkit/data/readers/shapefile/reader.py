# (C) Copyright 2020 ECMWF.
#
# This software is licensed under the terms of the Apache Licence Version 2.0
# which can be obtained at http://www.apache.org/licenses/LICENSE-2.0.
# In applying this licence, ECMWF does not waive the privileges and immunities
# granted to it by virtue of its status as an intergovernmental organisation
# nor does it submit to any jurisdiction.
#


from earthkit.data.readers import Reader
from earthkit.data.sources import Source
from earthkit.data.utils.bbox import BoundingBox


class ShapeFileReader(Source, Reader):
    def __init__(self, source, path):
        self.__gdf = None
        assert path.endswith(".shp")
        self._ori_source = source
        Reader.__init__(self, source, path)

    def __repr__(self):
        return f"{self.__class__.__name__}({self.path})"

    def _repr_html_(self):
        html_repr = (
            f"<h4>{self.__class__.__name__}(represented as a geopandas object):</h3>{self.to_pandas()._repr_html_()}"
        )

        return html_repr

    @property
    def _gdf(self):
        if self.__gdf is None:
            self.__gdf = self.to_pandas()
        return self.__gdf

    def __len__(self):
        return len(self._gdf)

    def __getitem__(self, n):
        return self._gdf.iloc[n]

    def mutate_source(self):
        # A ShapeFileReader is a source itself
        return self

    def bounding_box(self):
        return BoundingBox.from_geopandas(self._gdf)

    def ls(self, **kwargs):
        return self._gdf

    def head(self, **kwargs):
        return self._gdf.head(**kwargs)

    def tail(self, **kwargs):
        return self._gdf.tail(**kwargs)

    def describe(self, **kwargs):
        return self._gdf

    def to_numpy(self, flatten=False, **kwargs):
        v = self.to_pandas().to_numpy(**kwargs)
        if flatten:
            import math

            v = v.reshape(
                math.prod(v.shape),
            )
        return v

    def to_pandas(self, **kwargs):
        if not kwargs and self.__gdf is not None:
            return self.__gdf
        else:
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

    def to_data_object(self):
        from earthkit.data.data.shapefile import ShapeFileData

        return ShapeFileData(self)

    def _encode_default(self, encoder, **kwargs):
        return None
